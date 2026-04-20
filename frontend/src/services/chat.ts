import { ApiError } from './auth'
import type {
  Conversation,
  Message,
  SendMessagePayload,
} from '../types/chat'

const API_BASE = '/api/v1'

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` }
}

async function jsonFetch<T>(
  path: string,
  init: RequestInit,
  fallback: string,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, (data as { detail?: string }).detail ?? fallback)
  }
  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

export function listMyConversations(token: string): Promise<Conversation[]> {
  return jsonFetch<Conversation[]>(
    '/chats',
    { headers: authHeaders(token) },
    'Failed to load conversations',
  )
}

export function listStoreConversations(token: string): Promise<Conversation[]> {
  return jsonFetch<Conversation[]>(
    '/chats/store',
    { headers: authHeaders(token) },
    'Failed to load conversations',
  )
}

export function openSystemConversation(token: string): Promise<Conversation> {
  return jsonFetch<Conversation>(
    '/chats/system',
    { method: 'POST', headers: authHeaders(token) },
    'Failed to open system conversation',
  )
}

export function openStoreConversation(
  token: string,
  storeId: string,
): Promise<Conversation> {
  return jsonFetch<Conversation>(
    `/chats/with-store/${storeId}`,
    { method: 'POST', headers: authHeaders(token) },
    'Failed to open conversation',
  )
}

export function listMessagesAsUser(
  token: string,
  conversationId: string,
  opts: { limit?: number; before?: string } = {},
): Promise<Message[]> {
  const params = new URLSearchParams()
  if (opts.limit) params.set('limit', String(opts.limit))
  if (opts.before) params.set('before', opts.before)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return jsonFetch<Message[]>(
    `/chats/${conversationId}/messages${qs}`,
    { headers: authHeaders(token) },
    'Failed to load messages',
  )
}

export function listMessagesAsStore(
  token: string,
  conversationId: string,
  opts: { limit?: number; before?: string } = {},
): Promise<Message[]> {
  const params = new URLSearchParams()
  if (opts.limit) params.set('limit', String(opts.limit))
  if (opts.before) params.set('before', opts.before)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return jsonFetch<Message[]>(
    `/chats/store/${conversationId}/messages${qs}`,
    { headers: authHeaders(token) },
    'Failed to load messages',
  )
}

export function sendMessageAsUser(
  token: string,
  conversationId: string,
  payload: SendMessagePayload,
): Promise<Message> {
  return jsonFetch<Message>(
    `/chats/${conversationId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
      body: JSON.stringify(payload),
    },
    'Failed to send message',
  )
}

export function sendMessageAsStore(
  token: string,
  conversationId: string,
  payload: SendMessagePayload,
): Promise<Message> {
  return jsonFetch<Message>(
    `/chats/store/${conversationId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
      body: JSON.stringify(payload),
    },
    'Failed to send message',
  )
}

export function markReadAsUser(token: string, conversationId: string): Promise<void> {
  return jsonFetch<void>(
    `/chats/${conversationId}/read`,
    { method: 'POST', headers: authHeaders(token) },
    'Failed to mark read',
  )
}

export function markReadAsStore(token: string, conversationId: string): Promise<void> {
  return jsonFetch<void>(
    `/chats/store/${conversationId}/read`,
    { method: 'POST', headers: authHeaders(token) },
    'Failed to mark read',
  )
}

export function openChatSocket(token: string): WebSocket {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return new WebSocket(
    `${proto}://${host}${API_BASE}/ws/chat?token=${encodeURIComponent(token)}`,
  )
}
