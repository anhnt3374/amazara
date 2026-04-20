import { ApiError } from './auth'
import type {
  CreateOrderPayload,
  Order,
  OrderItem,
  OrderItemStoreMini,
  OrderStatus,
} from '../types/order'

const API_BASE = '/api/v1'

function mapStore(raw: Record<string, unknown> | null | undefined): OrderItemStoreMini | null {
  if (!raw) return null
  return {
    id: raw.id as string,
    name: raw.name as string,
    slug: (raw.slug as string | null) ?? null,
    avatarUrl: (raw.avatar_url as string | null) ?? null,
  }
}

function mapItem(raw: Record<string, unknown>): OrderItem {
  const image = (raw.product_image as string | null) ?? null
  const images = image
    ? image.split('|').map(s => s.trim()).filter(Boolean)
    : []
  return {
    id: raw.id as string,
    orderId: raw.order_id as string,
    productId: raw.product_id as string,
    productName: raw.product_name as string,
    quantity: raw.quantity as number,
    price: raw.price as number,
    notes: (raw.notes as string | null) ?? null,
    productImage: image,
    productImages: images,
    store: mapStore(raw.store as Record<string, unknown> | null),
  }
}

function mapOrder(raw: Record<string, unknown>): Order {
  return {
    id: raw.id as string,
    userId: raw.user_id as string,
    place: raw.place as string,
    phone: raw.phone as string,
    clientName: raw.client_name as string,
    totalAmount: raw.total_amount as number,
    status: raw.status as OrderStatus,
    note: (raw.note as string | null) ?? null,
    createdAt: (raw.created_at as string | null) ?? null,
    orderItems: (raw.order_items as Record<string, unknown>[]).map(mapItem),
  }
}

export async function createOrder(
  token: string,
  payload: CreateOrderPayload,
): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      place: payload.place,
      phone: payload.phone,
      client_name: payload.clientName,
      total_amount: payload.totalAmount,
      note: payload.note ?? null,
      items: payload.items.map(i => ({
        product_id: i.productId,
        product_name: i.productName,
        quantity: i.quantity,
        price: i.price,
        notes: i.notes ?? null,
      })),
      cart_item_ids: payload.cartItemIds ?? null,
    }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Create order failed')
  }
  return mapOrder(await res.json())
}

export async function listOrders(
  token: string,
  status?: OrderStatus,
): Promise<Order[]> {
  const url = status
    ? `${API_BASE}/orders/?status=${encodeURIComponent(status)}`
    : `${API_BASE}/orders/`
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load orders')
  }
  const data = (await res.json()) as Record<string, unknown>[]
  return data.map(mapOrder)
}

export async function getOrder(token: string, orderId: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load order')
  }
  return mapOrder(await res.json())
}
