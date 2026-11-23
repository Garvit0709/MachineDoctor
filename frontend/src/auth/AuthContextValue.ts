
import { createContext } from 'react'

import type { Administrator } from '../services/authApi'

export type AuthContextValue = {
  token: string | null
  administrator: Administrator | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(
  null,
)
