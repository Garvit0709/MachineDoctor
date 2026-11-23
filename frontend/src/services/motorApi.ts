
import { apiFetch } from './apiClient'

export interface Bearing {
  id: number
  motor_id: number
  bearing_code: string
  position: string
  bearing_type: string | null
  created_at?: string
}

export interface Motor {
  id: number
  motor_code: string
  name: string
  manufacturer: string | null
  location: string | null
  motor_type: string | null
  rated_rpm: number | null
  rated_power_kw: number | null
  notes: string | null
  operational_status: string
  bearings: Bearing[]
  created_at?: string
}

export interface MotorCreate {
  motor_code: string
  name: string
  manufacturer?: string | null
  location?: string | null
  motor_type?: string | null
  rated_rpm?: number | null
  rated_power_kw?: number | null
  notes?: string | null
  operational_status?: string
}

export type MotorUpdate = Partial<MotorCreate>

export interface BearingCreate {
  bearing_code: string
  position: string
  bearing_type?: string | null
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await apiFetch(path, options)

  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const body: unknown = await response.json()

      if (
        typeof body === 'object' &&
        body !== null &&
        'detail' in body
      ) {
        const detail = body.detail

        if (typeof detail === 'string') {
          message = detail
        } else if (Array.isArray(detail)) {
          message = detail
            .map((item: unknown) => {
              if (
                typeof item === 'object' &&
                item !== null &&
                'msg' in item &&
                typeof item.msg === 'string'
              ) {
                return item.msg
              }

              return 'Invalid input'
            })
            .join('; ')
        }
      }
    } catch {
      // Keep the HTTP status fallback.
    }

    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const motorApi = {
  list: (signal?: AbortSignal) =>
    request<Motor[]>(
      '/api/motors',
      { signal },
    ),

  get: (
    motorId: number,
    signal?: AbortSignal,
  ) =>
    request<Motor>(
      `/api/motors/${motorId}`,
      { signal },
    ),

  create: (payload: MotorCreate) =>
    request<Motor>(
      '/api/motors',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      },
    ),

  update: (
    motorId: number,
    payload: MotorUpdate,
  ) =>
    request<Motor>(
      `/api/motors/${motorId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      },
    ),

  remove: (motorId: number) =>
    request<void>(
      `/api/motors/${motorId}`,
      {
        method: 'DELETE',
      },
    ),

  delete: (motorId: number) =>
    request<void>(
      `/api/motors/${motorId}`,
      {
        method: 'DELETE',
      },
    ),

  addBearing: (
    motorId: number,
    payload: BearingCreate,
  ) =>
    request<Bearing>(
      `/api/motors/${motorId}/bearings`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      },
    ),

  listBearings: (
    motorId: number,
    signal?: AbortSignal,
  ) =>
    request<Bearing[]>(
      `/api/motors/${motorId}/bearings`,
      { signal },
    ),
}
