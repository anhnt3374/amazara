import { ApiError } from './auth'

const API_BASE = '/api/v1'

export async function addFavorite(token: string, productId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/favorites/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ product_id: productId }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Add favorite failed')
  }
}

export async function removeFavorite(token: string, productId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/favorites/${productId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Remove favorite failed')
  }
}
