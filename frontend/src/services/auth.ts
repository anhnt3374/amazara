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

export interface RegisterStorePayload {
  name: string
  email: string
  password: string
  slug?: string | null
  avatar_url?: string | null
  description?: string | null
}

export interface StoreLoginPayload {
  email: string
  password: string
}

export interface UserAccount {
  type: 'user'
  id: string
  email: string
  displayName: string
  fullname: string | null
  username: string | null
  avatar: string | null
}

export interface StoreAccount {
  type: 'store'
  id: string
  email: string
  displayName: string
  avatar: string | null
}

export type Account = UserAccount | StoreAccount

interface MeResponseRaw {
  type: 'user' | 'store'
  id: string
  email: string
  display_name: string
  fullname: string | null
  username: string | null
  avatar: string | null
}

function mapMe(raw: MeResponseRaw): Account {
  if (raw.type === 'store') {
    return {
      type: 'store',
      id: raw.id,
      email: raw.email,
      displayName: raw.display_name,
      avatar: raw.avatar,
    }
  }
  return {
    type: 'user',
    id: raw.id,
    email: raw.email,
    displayName: raw.display_name,
    fullname: raw.fullname,
    username: raw.username,
    avatar: raw.avatar,
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function postJson<T>(path: string, body: unknown, fallback: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? fallback)
  }
  return res.json()
}

export async function register(payload: RegisterPayload): Promise<UserOut> {
  return postJson<UserOut>('/auth/register', payload, 'Registration failed')
}

export async function login(payload: LoginPayload): Promise<{ access_token: string }> {
  return postJson<{ access_token: string }>('/auth/login', payload, 'Login failed')
}

export async function registerStore(
  payload: RegisterStorePayload,
): Promise<{ access_token: string }> {
  return postJson<{ access_token: string }>(
    '/auth/register-store',
    payload,
    'Store registration failed',
  )
}

export async function loginStore(
  payload: StoreLoginPayload,
): Promise<{ access_token: string }> {
  return postJson<{ access_token: string }>(
    '/auth/login-store',
    payload,
    'Store login failed',
  )
}

export async function getMe(token: string): Promise<Account> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Unauthorized')
  }
  const raw = (await res.json()) as MeResponseRaw
  return mapMe(raw)
}
