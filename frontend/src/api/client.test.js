// Tests isolés du client API et de la fin de session : `npm test` (node --test, sans dépendance supplémentaire).
// Un adaptateur axios simule l'API Django ; tous les tokens sont fictifs.
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import axios, { AxiosError } from 'axios'

// ── Environnement navigateur minimal ─────────────────────────────────────────

const store = new Map()
globalThis.localStorage = {
  getItem: (key) => (store.has(key) ? store.get(key) : null),
  setItem: (key, value) => store.set(key, String(value)),
  removeItem: (key) => store.delete(key),
}
globalThis.window = { location: { href: '/dashboard' } }

// ── Faux serveur ──────────────────────────────────────────────────────────────

const server = {
  validAccess: new Set(),
  validRefresh: new Set(),
  revoked: new Set(),
  calls: [],
  meAlways401: false,
  meStatus: null,
  refreshFails: false,
  logoutMode: 'normal',
  tokenCounter: 0,
}

function issue(prefix) {
  server.tokenCounter += 1
  return `fake-${prefix}-${server.tokenCounter}`
}

function callsTo(path) {
  return server.calls.filter((call) => call.path === path)
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function respond(config, status, data) {
  const response = { data, status, statusText: String(status), headers: {}, config, request: {} }
  if (status >= 200 && status < 300) return response
  throw new AxiosError(`Request failed with status code ${status}`, AxiosError.ERR_BAD_REQUEST, config, {}, response)
}

async function fakeAdapter(config) {
  const path = config.url.startsWith('/api/') ? config.url : `${config.baseURL ?? ''}${config.url}`
  const body = typeof config.data === 'string' ? JSON.parse(config.data) : (config.data ?? {})
  const authorization = config.headers?.Authorization ?? config.headers?.get?.('Authorization') ?? null
  const access = authorization?.replace('Bearer ', '') ?? null
  server.calls.push({ path, body, access })

  // Les réponses arrivent après un délai : les requêtes concurrentes se chevauchent.
  await delay(path.endsWith('/token/refresh/') ? 20 : 5)

  switch (path) {
    case '/api/v1/auth/login/':
      return respond(config, 401, { detail: 'No active account found with the given credentials' })
    case '/api/v1/auth/token/refresh/': {
      if (server.refreshFails || !server.validRefresh.has(body.refresh)) {
        return respond(config, 401, { detail: 'Token is invalid', code: 'token_not_valid' })
      }
      server.validRefresh.delete(body.refresh)
      server.revoked.add(body.refresh)
      const newAccess = issue('access')
      const newRefresh = issue('refresh')
      server.validAccess.add(newAccess)
      server.validRefresh.add(newRefresh)
      return respond(config, 200, { access: newAccess, refresh: newRefresh })
    }
    case '/api/v1/auth/me/':
      if (server.meStatus) return respond(config, server.meStatus, { detail: 'erreur serveur simulée' })
      if (server.meAlways401 || !server.validAccess.has(access)) return respond(config, 401, { detail: 'expired' })
      return respond(config, 200, { email: 'fictif@example.com' })
    case '/api/v1/auth/logout/':
      if (server.logoutMode === 'network') {
        throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config, {})
      }
      if (server.logoutMode === 'error500') return respond(config, 500, { detail: 'erreur serveur simulée' })
      if (!server.validAccess.has(access)) return respond(config, 401, { detail: 'expired' })
      if (!server.validRefresh.has(body.refresh)) return respond(config, 400, { detail: 'Token invalide.' })
      server.validRefresh.delete(body.refresh)
      server.revoked.add(body.refresh)
      return respond(config, 200, { detail: 'Déconnexion réussie.' })
    default:
      return respond(config, 404, {})
  }
}

// L'adaptateur doit être en place avant la création de l'instance axios du client.
axios.defaults.adapter = fakeAdapter
const { default: client } = await import('./client.js')
const { authApi } = await import('./auth.js')
const { endSession } = await import('../features/auth/session.js')

// Session dont l'access token a expiré mais dont le refresh token est valide.
function startSessionWithExpiredAccess() {
  const refresh = issue('refresh')
  server.validRefresh.add(refresh)
  localStorage.setItem('access_token', 'fake-access-expired')
  localStorage.setItem('refresh_token', refresh)
  return refresh
}

// Session dont l'access token et le refresh token sont valides.
function startValidSession() {
  const access = issue('access')
  const refresh = issue('refresh')
  server.validAccess.add(access)
  server.validRefresh.add(refresh)
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
  return { access, refresh }
}

beforeEach(() => {
  store.clear()
  server.validAccess.clear()
  server.validRefresh.clear()
  server.revoked.clear()
  server.calls = []
  server.meAlways401 = false
  server.meStatus = null
  server.refreshFails = false
  server.logoutMode = 'normal'
  window.location.href = '/dashboard'
})

// ── Renouvellement ────────────────────────────────────────────────────────────

test('401 sur une requête protégée : renouvellement réussi puis nouvelle tentative', async () => {
  const oldRefresh = startSessionWithExpiredAccess()

  const response = await client.get('/auth/me/')

  assert.equal(response.status, 200)
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 1)
  assert.notEqual(localStorage.getItem('access_token'), 'fake-access-expired')
  assert.notEqual(localStorage.getItem('refresh_token'), oldRefresh, 'le refresh token issu de la rotation est stocké')
  assert.ok(server.revoked.has(oldRefresh))
})

test('requêtes concurrentes en 401 : un seul renouvellement, toutes rejouées avec le nouveau token', async () => {
  startSessionWithExpiredAccess()

  const responses = await Promise.all([client.get('/auth/me/'), client.get('/auth/me/'), client.get('/auth/me/')])

  assert.deepEqual(responses.map((r) => r.status), [200, 200, 200])
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 1)
  const newAccess = localStorage.getItem('access_token')
  const retried = callsTo('/api/v1/auth/me/').filter((call) => call.access === newAccess)
  assert.equal(retried.length, 3)
})

test('échec du renouvellement : file rejetée, tokens effacés, redirection, aucune boucle', async () => {
  startSessionWithExpiredAccess()
  server.refreshFails = true

  const results = await Promise.allSettled([client.get('/auth/me/'), client.get('/auth/me/'), client.get('/auth/me/')])

  assert.deepEqual(results.map((r) => r.status), ['rejected', 'rejected', 'rejected'])
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 1, 'le refresh en 401 ne relance pas de refresh')
  assert.equal(callsTo('/api/v1/auth/me/').length, 3, 'aucune requête rejouée')
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(localStorage.getItem('refresh_token'), null)
  assert.equal(window.location.href, '/login')
})

test('401 persistant après renouvellement : chaque requête n\'est rejouée qu\'une fois, un seul refresh', async () => {
  startSessionWithExpiredAccess()
  server.meAlways401 = true

  const results = await Promise.allSettled([client.get('/auth/me/'), client.get('/auth/me/'), client.get('/auth/me/')])

  assert.deepEqual(results.map((r) => r.status), ['rejected', 'rejected', 'rejected'])
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 1)
  assert.equal(callsTo('/api/v1/auth/me/').length, 6, '3 requêtes initiales + 3 nouvelles tentatives')
})

test('401 sans refresh token stocké : pas d\'appel au refresh, session effacée, redirection', async () => {
  localStorage.setItem('access_token', 'fake-access-expired')

  await assert.rejects(client.get('/auth/me/'))

  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0)
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(window.location.href, '/login')
})

test('erreur serveur 500 : transmise telle quelle, sans renouvellement ni effacement de la session', async () => {
  const { access, refresh } = startValidSession()
  server.meStatus = 500

  await assert.rejects(client.get('/auth/me/'), (error) => {
    assert.equal(error.response.status, 500)
    return true
  })
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0)
  assert.equal(localStorage.getItem('access_token'), access)
  assert.equal(localStorage.getItem('refresh_token'), refresh)
  assert.equal(window.location.href, '/dashboard')
})

// ── Endpoints d'authentification ──────────────────────────────────────────────

test('identifiants invalides : 401 transmis à la page, sans refresh ni rechargement', async () => {
  await assert.rejects(authApi.login({ email: 'fictif@example.com', password: 'faux' }), (error) => {
    assert.equal(error.response.status, 401)
    return true
  })
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0)
  assert.equal(window.location.href, '/dashboard')
})

test('identifiants invalides avec un ancien refresh token stocké : la connexion n\'est pas rejouée', async () => {
  const staleRefresh = startSessionWithExpiredAccess()

  await assert.rejects(authApi.login({ email: 'fictif@example.com', password: 'faux' }))

  assert.equal(callsTo('/api/v1/auth/login/').length, 1)
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0)
  assert.equal(localStorage.getItem('refresh_token'), staleRefresh)
  assert.equal(window.location.href, '/dashboard')
})

test('refresh appelé via le client et refusé : pas de boucle de renouvellement', async () => {
  localStorage.setItem('refresh_token', 'fake-refresh-inconnu')

  await assert.rejects(authApi.refreshToken('fake-refresh-inconnu'))

  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 1)
})

// ── Déconnexion ───────────────────────────────────────────────────────────────

test('déconnexion avec access expiré : le refresh token issu de la rotation est révoqué', async () => {
  const initialRefresh = startSessionWithExpiredAccess()

  const response = await authApi.logout()

  assert.equal(response.status, 200)
  const logoutCalls = callsTo('/api/v1/auth/logout/')
  assert.equal(logoutCalls.length, 2, 'tentative en 401, puis nouvelle tentative après rotation')
  assert.equal(logoutCalls[0].body.refresh, initialRefresh)
  const rotatedRefresh = logoutCalls[1].body.refresh
  assert.notEqual(rotatedRefresh, initialRefresh, 'la nouvelle tentative envoie le token courant')
  assert.ok(server.revoked.has(initialRefresh), 'ancien token révoqué par la rotation')
  assert.ok(server.revoked.has(rotatedRefresh), 'nouveau token révoqué par la déconnexion')
  assert.equal(server.validRefresh.size, 0, 'aucun refresh token ne reste valide côté serveur')
})

test('déconnexion avec access valide : un seul appel, token courant révoqué', async () => {
  const { refresh } = startValidSession()

  await authApi.logout()

  assert.equal(callsTo('/api/v1/auth/logout/').length, 1)
  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0)
  assert.ok(server.revoked.has(refresh))
})

// ── Fin de session côté client (endSession, utilisée par AuthContext) ─────────

test('fin de session réussie : token révoqué côté serveur et état local nettoyé', async () => {
  const { refresh } = startValidSession()

  await endSession()

  assert.ok(server.revoked.has(refresh))
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(localStorage.getItem('refresh_token'), null)
})

test('fin de session : état local nettoyé même si le serveur refuse le token (400)', async () => {
  startValidSession()
  server.validRefresh.clear()

  await endSession()

  assert.equal(callsTo('/api/v1/auth/logout/').length, 1)
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(localStorage.getItem('refresh_token'), null)
})

test('fin de session : état local nettoyé même en cas d\'erreur serveur (500)', async () => {
  startValidSession()
  server.logoutMode = 'error500'

  await endSession()

  assert.equal(callsTo('/api/v1/auth/token/refresh/').length, 0, 'une 500 ne déclenche pas de renouvellement')
  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(localStorage.getItem('refresh_token'), null)
})

test('fin de session : état local nettoyé même si le serveur est injoignable', async () => {
  startValidSession()
  server.logoutMode = 'network'

  await endSession()

  assert.equal(localStorage.getItem('access_token'), null)
  assert.equal(localStorage.getItem('refresh_token'), null)
})

test('fin de session sans refresh token stocké : aucun appel au serveur', async () => {
  localStorage.setItem('access_token', 'fake-access-orphelin')

  await endSession()

  assert.equal(callsTo('/api/v1/auth/logout/').length, 0)
  assert.equal(localStorage.getItem('access_token'), null)
})
