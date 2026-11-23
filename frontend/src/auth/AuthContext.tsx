import { useEffect } from 'react'

import {
  setAccessToken,
  setUnauthorizedHandler,
} from '../services/tokenManager'
import {
  useCallback,
  useMemo,
  useState,
} from 'react'

import type { ReactNode } from 'react'

import {
  getAdministrator,
  loginAdministrator,
} from '../services/authApi'

import type { Administrator } from '../services/authApi'

import { AuthContext } from './AuthContextValue'

export function AuthProvider({
  children,
}: {
  children: ReactNode
}) {
  const [token, setToken] = useState<string | null>(null)

  const [administrator, setAdministrator] =
    useState<Administrator | null>(null)

 const logout = useCallback(() => {
  setAccessToken(null)
  setToken(null)
  setAdministrator(null)
}, [])
useEffect(() => {
  setUnauthorizedHandler(logout)

  return () => {
    setUnauthorizedHandler(null)
  }
}, [logout])
  const login = useCallback(
    async (username: string, password: string) => {
      const accessToken = await loginAdministrator(
        username,
        password,
      )

      const profile = await getAdministrator(accessToken)

      if (!profile.is_active) {
        throw new Error('Administrator account is inactive.')
      }

      setAccessToken(accessToken)
      setToken(accessToken)
      setAdministrator(profile)
    },
    [],
  )

  const value = useMemo(
    () => ({
      token,
      administrator,
      isAuthenticated: Boolean(token && administrator),
      login,
      logout,
    }),
    [token, administrator, login, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
