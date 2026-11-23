
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

export type Administrator = {
  id: number
  username: string
  is_active: boolean
}

type LoginResponse = {
  access_token: string
  token_type: string
}

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'AuthenticationError'
  }
}

export async function loginAdministrator(
  username: string,
  password: string,
): Promise<string> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
    }),
  })

  if (response.status === 401) {
    throw new AuthenticationError(
      'Invalid username or password.',
    )
  }

  if (!response.ok) {
    throw new AuthenticationError(
      'Unable to sign in. Please try again.',
    )
  }

  const result = (await response.json()) as LoginResponse

  if (!result.access_token || result.token_type !== 'bearer') {
    throw new AuthenticationError(
      'Invalid authentication response.',
    )
  }

  return result.access_token
}

export async function getAdministrator(
  token: string,
): Promise<Administrator> {
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (response.status === 401) {
    throw new AuthenticationError(
      'Your session has expired. Please sign in again.',
    )
  }

  if (!response.ok) {
    throw new AuthenticationError(
      'Unable to verify administrator session.',
    )
  }

  return response.json() as Promise<Administrator>
}
