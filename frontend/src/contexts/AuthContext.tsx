import { createContext, useCallback, useEffect, useState } from 'react'
import {
  type RegisterPayload,
  type UserOut,
  getMe,
  login as apiLogin,
  register as apiRegister,
} from '../services/auth'

const TOKEN_KEY = 'access_token'

interface AuthContextValue {
  user: UserOut | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Bootstrap: khôi phục session từ localStorage khi app khởi động
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY)
    if (!stored) {
      setLoading(false)
      return
    }
    getMe(stored)
      .then(u => {
        setToken(stored)
        setUser(u)
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin({ email, password })
    localStorage.setItem(TOKEN_KEY, access_token)
    const u = await getMe(access_token)
    setToken(access_token)
    setUser(u)
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    await apiRegister(payload)
    // Auto-login sau khi đăng ký thành công
    await login(payload.email, payload.password)
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
