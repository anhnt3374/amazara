import { ApiError } from './auth'

const API_BASE = '/api/v1'

export interface AddToCartPayload {
  productId: string
  quantity: number
  notes?: string | null
}

export interface CartItem {
  id: string
  userId: string
  productId: string
  quantity: number
  notes: string | null
}

export async function addToCart(token: string, payload: AddToCartPayload): Promise<CartItem> {
  const res = await fetch(`${API_BASE}/cart/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      product_id: payload.productId,
      quantity: payload.quantity,
      notes: payload.notes ?? null,
    }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Add to cart failed')
  }
  const data = await res.json()
  return {
    id: data.id,
    userId: data.user_id,
    productId: data.product_id,
    quantity: data.quantity,
    notes: data.notes,
  }
}
