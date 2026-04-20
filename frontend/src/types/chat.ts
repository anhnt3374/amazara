export type ConversationType = 'user_store' | 'user_system'

export type SenderType = 'user' | 'store' | 'bot' | 'system'

export type MessageRefType = 'product' | 'order' | 'order_event'

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
