
import {
  getAccessToken,
  notifyUnauthorized,
} from './tokenManager'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

export async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = getAccessToken()

  const headers = new Headers(options.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...options,
      headers,
    },
  )

  if (response.status === 401 && token) {
    // Avoid logging out a newer session because
    // an older request returned late.
    if (getAccessToken() === token) {
      notifyUnauthorized()
    }
  }

  return response
}
