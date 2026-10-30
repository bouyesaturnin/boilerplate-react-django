import client from './client.js'

export const authApi = {
  register: (data) => client.post('/auth/register/', data),
  login: (data) => client.post('/auth/login/', data),
  // Le refresh token est inséré par l'intercepteur au moment de l'envoi (voir client.js)
  logout: () => client.post('/auth/logout/', null, { sendRefreshToken: true }),
  me: () => client.get('/auth/me/'),
  refreshToken: (refresh) => client.post('/auth/token/refresh/', { refresh }),
}
