// Who is signed in, shared across the app.
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import {
  fetchCurrentUser,
  loginRequest,
  logoutRequest,
  registerRequest,
  type RegisterData,
  type User,
} from './api'

interface AuthState {
  user: User | null
  loading: boolean // true until we've asked the backend whether a session exists
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .finally(() => setLoading(false))
  }, [])

  const value: AuthState = {
    user,
    loading,
    login: async (email, password) => setUser(await loginRequest(email, password)),
    register: async (data) => setUser(await registerRequest(data)),
    logout: async () => {
      await logoutRequest()
      setUser(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
