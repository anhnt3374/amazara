const API_BASE = '/api/v1'

export interface UserOut {
  id: string
  email: string
  username: string
  fullname: string
  avatar: string | null
}

export interface RegisterPayload {
  email: string
  username: string
  fullname: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function register(payload: RegisterPayload): Promise<UserOut> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Đăng ký thất bại')
  }
  return res.json()
}

export async function login(payload: LoginPayload): Promise<{ access_token: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Đăng nhập thất bại')
  }
  return res.json()
}

export async function getMe(token: string): Promise<UserOut> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Unauthorized')
  }
  return res.json()
}
