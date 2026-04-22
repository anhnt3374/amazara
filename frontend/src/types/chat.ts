export type ConversationType = 'user_store' | 'user_system'

export type SenderType = 'user' | 'store' | 'bot' | 'system'

export type MessageRefType = 'product' | 'order' | 'order_event'

export interface AssistantCarouselItem {
  product_id: string
  name: string
  image: string | null
  price: number
  discount: number
  final_price: number
  stock: number
}

export interface ProductCarouselPayload {
  type: 'product_carousel'
  query: string
  page: number
  page_size: number
  total: number
  items: AssistantCarouselItem[]
}

export interface OrderConfirmationPayload {
  type: 'order_confirmation'
  quantity: number
  shipping_fee: number
  total_amount: number
  address: {
    place: string
    phone: string
    client_name: string
  }
  product: {
    product_id: string
    name: string
    image: string | null
    price: number
    discount: number
    final_price: number
  }
  action: {
    action_id: 'confirm_order'
    draft_id: string
    label: string
  }
}

export interface OrderResultPayload {
  type: 'order_result'
  order: {
    order_id: string
    status: string
    total_amount: number
    product_id: string
    product_name: string
    quantity: number
  }
}

export type AssistantPayload =
  | ProductCarouselPayload
  | OrderConfirmationPayload
  | OrderResultPayload

export interface PartnerInfo {
  id: string | null
  display_name: string
  avatar: string | null
}

export interface Message {
  id: string
  conversation_id: string
  sender_type: SenderType
  sender_id: string | null
  content: string
  ref_type: MessageRefType | null
  ref_id: string | null
  ref_payload: Record<string, unknown> | null
  assistant_payload: AssistantPayload | null
  created_at: string
}

export interface Conversation {
  id: string
  type: ConversationType
  user_id: string
  store_id: string | null
  partner: PartnerInfo
  last_message: Message | null
  unread_count: number
  last_message_at: string | null
  created_at: string
  updated_at: string
}

export interface SendMessagePayload {
  content: string
  ref_type?: MessageRefType | null
  ref_id?: string | null
}

export interface AssistantActionPayload {
  action_id: string
  data?: Record<string, unknown> | null
}
