import { authApi } from '../../api/auth.js'

// Fin de session côté client, isolée d'AuthContext pour être testable sans DOM.
export async function endSession() {
  try {
    if (localStorage.getItem('refresh_token')) await authApi.logout()
  } catch {
    // On nettoie dans tous les cas : token refusé, erreur serveur ou serveur injoignable
  }
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}
