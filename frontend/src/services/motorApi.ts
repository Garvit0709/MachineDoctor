
export type Bearing = {
  id: number
  motor_id: number
  bearing_code: string
  position: string
  bearing_type: string | null
  manufacturer: string | null
  model_number: string | null
  notes: string | null
  created_at: string
}

export type Motor = {
  id: number
  motor_code: string
  name: string
  location: string | null
  motor_type: string | null
  manufacturer: string | null
  rated_rpm: number | null
  rated_power_kw: number | null
  operational_status: string
  notes: string | null
  created_at: string
  bearings: Bearing[]
}

export type MotorCreate = {
  motor_code: string
  name: string
  location?: string | null
  motor_type?: string | null
  manufacturer?: string | null
  rated_rpm?: number | null
  rated_power_kw?: number | null
  notes?: string | null
}

export type MotorUpdate = Partial<
  Omit<MotorCreate, 'motor_code'>
> & {
  operational_status?: string
}

export type BearingCreate = {
  bearing_code: string
  position: string
  bearing_type?: string | null
  manufacturer?: string | null
  model_number?: string | null
  notes?: string | null
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    throw new Error(
      'Cannot connect to MachineDoctor backend. Check FastAPI.',
    )
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const body: unknown = await response.json()

      if (
        typeof body === 'object' &&
        body !== null &&
        'detail' in body
      ) {
        if (typeof body.detail === 'string') {
          message = body.detail
        }
      }
    } catch {
      // Keep HTTP status message.
    }

    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const motorApi = {
  list: () => request<Motor[]>('/api/motors'),

  get: (id: number) =>
    request<Motor>(`/api/motors/${id}`),

  create: (data: MotorCreate) =>
    request<Motor>('/api/motors', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: MotorUpdate) =>
    request<Motor>(`/api/motors/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  remove: (id: number) =>
    request<void>(`/api/motors/${id}`, {
      method: 'DELETE',
    }),

  addBearing: (motorId: number, data: BearingCreate) =>
    request<Bearing>(`/api/motors/${motorId}/bearings`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}
