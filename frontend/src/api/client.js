import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // Lu à chaque envoi : une nouvelle tentative après rotation transmet le refresh token courant
  if (config.sendRefreshToken) config.data = { refresh: localStorage.getItem('refresh_token') }
  return config
})

// Un 401 sur ces endpoints signifie « identifiants ou token refusés », pas « access expiré »
const AUTH_ENDPOINTS = ['/auth/login/', '/auth/register/', '/auth/token/refresh/']

// File d'attente des requêtes pendant le refresh
let isRefreshing = false
let queue = []

function processQueue(error, token = null) {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  queue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status !== 401 || original._retry || AUTH_ENDPOINTS.includes(original.url)) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject })
      }).then((token) => {
        original._retry = true
        original.headers.Authorization = `Bearer ${token}`
        return client(original)
      })
    }

    original._retry = true
    isRefreshing = true

    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) {
      isRefreshing = false
      localStorage.removeItem('access_token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    try {
      const { data } = await axios.post('/api/v1/auth/token/refresh/', { refresh })
      localStorage.setItem('access_token', data.access)
      if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
      processQueue(null, data.access)
      original.headers.Authorization = `Bearer ${data.access}`
      return client(original)
    } catch (err) {
      processQueue(err, null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(err)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
