import { createContext, useCallback, useEffect, useState } from 'react'
import {
  type Account,
  type RegisterPayload,
  type RegisterStorePayload,
  getMe,
  login as apiLogin,
  loginStore as apiLoginStore,
  register as apiRegister,
  registerStore as apiRegisterStore,
} from '../services/auth'

const TOKEN_KEY = 'access_token'

interface AuthContextValue {
  account: Account | null
  token: string | null
  loading: boolean
  loginUser: (email: string, password: string) => Promise<void>
  loginStore: (email: string, password: string) => Promise<void>
  registerUser: (payload: RegisterPayload) => Promise<void>
  registerStore: (payload: RegisterStorePayload) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY)
    if (!stored) {
      setLoading(false)
      return
    }
    getMe(stored)
      .then(a => {
        setToken(stored)
        setAccount(a)
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
      })
      .finally(() => setLoading(false))
  }, [])

  const applyToken = useCallback(async (access_token: string) => {
    localStorage.setItem(TOKEN_KEY, access_token)
    const a = await getMe(access_token)
    setToken(access_token)
    setAccount(a)
  }, [])

  const loginUser = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiLogin({ email, password })
      await applyToken(access_token)
    },
    [applyToken],
  )

  const loginStore = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiLoginStore({ email, password })
      await applyToken(access_token)
    },
    [applyToken],
  )

  const registerUser = useCallback(
    async (payload: RegisterPayload) => {
      await apiRegister(payload)
      await loginUser(payload.email, payload.password)
    },
    [loginUser],
  )

  const registerStore = useCallback(
    async (payload: RegisterStorePayload) => {
      const { access_token } = await apiRegisterStore(payload)
      await applyToken(access_token)
    },
    [applyToken],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setAccount(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        account,
        token,
        loading,
        loginUser,
        loginStore,
        registerUser,
        registerStore,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
