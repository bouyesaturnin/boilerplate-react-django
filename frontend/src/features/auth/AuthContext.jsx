import { createContext, useCallback, useContext, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { endSession } from './session'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem('access_token')
  )

  const isAuthenticated = !!accessToken

  const login = useCallback(async (credentials) => {
    const { data } = await authApi.login(credentials)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    setAccessToken(data.access)
    const { data: profile } = await authApi.me()
    setUser(profile)
    return profile
  }, [])

  const register = useCallback(async (credentials) => {
    const { data } = await authApi.register(credentials)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    setAccessToken(data.access)
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    await endSession()
    setAccessToken(null)
    setUser(null)
    navigate('/login')
  }, [navigate])

  return (
    <AuthContext.Provider value={{ user, setUser, isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans AuthProvider')
  return ctx
}
