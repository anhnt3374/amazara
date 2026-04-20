import { useEffect, useRef } from 'react'
import { openChatSocket } from '../services/chat'
import type { Message, SendMessagePayload } from '../types/chat'

type ServerEvent =
  | { type: 'message'; conversation_id: string; message: Message }
  | { type: 'error'; detail: string }

interface UseChatSocketOpts {
  token: string | null
  enabled: boolean
  onMessage: (conversationId: string, message: Message) => void
}

interface UseChatSocketApi {
  send: (
    conversationId: string,
    payload: SendMessagePayload,
  ) => boolean
  markRead: (conversationId: string) => boolean
}

export function useChatSocket({
  token,
  enabled,
  onMessage,
}: UseChatSocketOpts): UseChatSocketApi {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<number | null>(null)
  const onMessageRef = useRef(onMessage)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    if (!enabled || !token) {
      return
    }
    let cancelled = false

    const connect = () => {
      if (cancelled) return
      const ws = openChatSocket(token)
      wsRef.current = ws

      ws.onmessage = ev => {
        try {
          const data = JSON.parse(ev.data) as ServerEvent
          if (data.type === 'message') {
            onMessageRef.current(data.conversation_id, data.message)
          }
        } catch {
          // Ignore malformed payloads.
        }
      }

      ws.onclose = () => {
        wsRef.current = null
        if (cancelled) return
        reconnectRef.current = window.setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectRef.current !== null) {
        window.clearTimeout(reconnectRef.current)
      }
      const ws = wsRef.current
      if (ws) {
        ws.onclose = null
        ws.close()
        wsRef.current = null
      }
    }
  }, [enabled, token])

  const send = (conversationId: string, payload: SendMessagePayload) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(
      JSON.stringify({
        type: 'send',
        conversation_id: conversationId,
        content: payload.content,
        ref_type: payload.ref_type ?? null,
        ref_id: payload.ref_id ?? null,
      }),
    )
    return true
  }

  const markRead = (conversationId: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify({ type: 'read', conversation_id: conversationId }))
    return true
  }

  return { send, markRead }
}
