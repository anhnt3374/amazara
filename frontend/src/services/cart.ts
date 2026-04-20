import { ApiError } from './auth'
import type {
  CartListResponse,
  CartProductMini,
  CartStoreMini,
  EnrichedCartItem,
} from '../types/cart'

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

function mapStore(raw: Record<string, unknown>): CartStoreMini {
  return {
    id: raw.id as string,
    name: raw.name as string,
    slug: (raw.slug as string | null) ?? null,
    avatarUrl: (raw.avatar_url as string | null) ?? null,
  }
}

function mapProductMini(raw: Record<string, unknown>): CartProductMini {
  const image = (raw.image as string | null) ?? ''
  const images = image ? image.split('|').map(s => s.trim()).filter(Boolean) : []
  return {
    id: raw.id as string,
    name: raw.name as string,
    price: raw.price as number,
    discount: raw.discount as number,
    images,
    stock: (raw.stock as number) ?? 0,
    categoryId: (raw.category_id as string | null) ?? null,
    storeId: raw.store_id as string,
    categoryName: (raw.category_name as string | null) ?? null,
  }
}

function mapEnriched(raw: Record<string, unknown>): EnrichedCartItem {
  return {
    id: raw.id as string,
    productId: raw.product_id as string,
    quantity: raw.quantity as number,
    notes: (raw.notes as string | null) ?? null,
    product: mapProductMini(raw.product as Record<string, unknown>),
    store: mapStore(raw.store as Record<string, unknown>),
  }
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

export async function listCart(token: string): Promise<CartListResponse> {
  const res = await fetch(`${API_BASE}/cart/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load cart')
  }
  const data = await res.json()
  return {
    items: (data.items as Record<string, unknown>[]).map(mapEnriched),
    totalCount: data.total_count as number,
  }
}

export async function updateCartItem(
  token: string,
  itemId: string,
  patch: { quantity?: number; notes?: string | null },
): Promise<CartItem> {
  const res = await fetch(`${API_BASE}/cart/${itemId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(patch),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Update cart item failed')
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

export async function deleteCartItem(token: string, itemId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/cart/${itemId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Delete cart item failed')
  }
}

export async function bulkDeleteCartItems(
  token: string,
  ids: string[],
): Promise<number> {
  const res = await fetch(`${API_BASE}/cart/bulk-delete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ids }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Bulk delete failed')
  }
  const data = await res.json()
  return data.deleted as number
}
