export type OrderStatus =
  | 'shipping'
  | 'awaiting_delivery'
  | 'completed'
  | 'cancelled'
  | 'returning'

export interface OrderItemStoreMini {
  id: string
  name: string
  slug: string | null
  avatarUrl: string | null
}

export interface OrderItem {
  id: string
  orderId: string
  productId: string
  productName: string
  quantity: number
  price: number
  notes: string | null
  productImage: string | null
  productImages: string[]
  store: OrderItemStoreMini | null
}

export interface Order {
  id: string
  userId: string
  place: string
  phone: string
  clientName: string
  totalAmount: number
  status: OrderStatus
  note: string | null
  createdAt: string | null
  orderItems: OrderItem[]
}

export interface CreateOrderItemPayload {
  productId: string
  productName: string
  quantity: number
  price: number
  notes?: string | null
}

export interface CreateOrderPayload {
  place: string
  phone: string
  clientName: string
  totalAmount: number
  note?: string | null
  items: CreateOrderItemPayload[]
  cartItemIds?: string[]
}
