import { ApiError } from './auth'
import type { Address } from '../types/address'

const API_BASE = '/api/v1'

function mapAddress(raw: Record<string, unknown>): Address {
  return {
    id: raw.id as string,
    userId: raw.user_id as string,
    place: raw.place as string,
    phone: raw.phone as string,
    clientName: raw.client_name as string,
  }
}

export async function listAddresses(token: string): Promise<Address[]> {
  const res = await fetch(`${API_BASE}/addresses/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load addresses')
  }
  const data = (await res.json()) as Record<string, unknown>[]
  return data.map(mapAddress)
}
