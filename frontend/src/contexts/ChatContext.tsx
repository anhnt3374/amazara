import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { useAuth } from '../hooks/useAuth'
import { useChatSocket } from '../hooks/useChatSocket'
import {
  submitAssistantAction,
  listMessagesAsStore,
  listMessagesAsUser,
  listMyConversations,
  listStoreConversations,
  markReadAsStore,
  markReadAsUser,
  openStoreConversation,
  openSystemConversation,
  sendMessageAsStore,
  sendMessageAsUser,
} from '../services/chat'
import type {
  AssistantActionPayload,
  Conversation,
  Message,
  SendMessagePayload,
} from '../types/chat'

interface ChatContextValue {
  conversations: Conversation[]
  messagesByConversation: Record<string, Message[]>
  activeConversationId: string | null
  setActiveConversationId: (id: string | null) => void
  unreadTotal: number
  refreshConversations: () => Promise<void>
  loadMessages: (conversationId: string) => Promise<Message[]>
  sendMessage: (conversationId: string, payload: SendMessagePayload) => Promise<void>
  runAssistantAction: (
    conversationId: string,
    payload: AssistantActionPayload,
  ) => Promise<void>
  markRead: (conversationId: string) => Promise<void>
  openWithStore: (storeId: string) => Promise<Conversation>
  openSystem: () => Promise<Conversation>
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside <ChatProvider>')
  return ctx
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { account, token } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messagesByConversation, setMessagesByConversation] = useState<
    Record<string, Message[]>
  >({})
  const [activeConversationId, setActiveConversationIdState] = useState<
    string | null
  >(null)
  const activeRef = useRef<string | null>(null)

  useEffect(() => {
    activeRef.current = activeConversationId
  }, [activeConversationId])

  const setActiveConversationId = useCallback((id: string | null) => {
    setActiveConversationIdState(id)
  }, [])

  const enabled = Boolean(account && token)
  const viewerIsUser = account?.type === 'user'

  const refreshConversations = useCallback(async () => {
    if (!token || !account) return
    try {
      const list =
        account.type === 'user'
          ? await listMyConversations(token)
          : await listStoreConversations(token)
      setConversations(list)
    } catch {
      // swallow; user will see empty list
    }
  }, [account, token])

  useEffect(() => {
    if (!enabled) {
      setConversations([])
      setMessagesByConversation({})
      return
    }
    void refreshConversations()
  }, [enabled, refreshConversations])

  const handleIncoming = useCallback(
    (conversationId: string, message: Message) => {
      setMessagesByConversation(prev => {
        const existing = prev[conversationId] ?? []
        if (existing.some(m => m.id === message.id)) return prev
        return { ...prev, [conversationId]: [...existing, message] }
      })
      setConversations(prev => {
        const idx = prev.findIndex(c => c.id === conversationId)
        if (idx < 0) {
          // Unknown conversation — refresh list from server.
          void refreshConversations()
          return prev
        }
        const updated: Conversation = {
          ...prev[idx],
          last_message: message,
          last_message_at: message.created_at,
          unread_count:
            activeRef.current === conversationId
              ? prev[idx].unread_count
              : prev[idx].unread_count + (isIncrementable(message, account?.type) ? 1 : 0),
        }
        const without = prev.filter((_, i) => i !== idx)
        return [updated, ...without]
      })
    },
    [account?.type, refreshConversations],
  )

  const socket = useChatSocket({
    token,
    enabled,
    onMessage: handleIncoming,
  })

  const loadMessages = useCallback(
    async (conversationId: string) => {
      if (!token || !account) return []
      const fetcher =
        account.type === 'user' ? listMessagesAsUser : listMessagesAsStore
      const msgs = await fetcher(token, conversationId, { limit: 100 })
      setMessagesByConversation(prev => ({ ...prev, [conversationId]: msgs }))
      return msgs
    },
    [account, token],
  )

  const sendMessage = useCallback(
    async (conversationId: string, payload: SendMessagePayload) => {
      if (!token || !account) return
      // Always use REST — it broadcasts via WS and triggers bot reply.
      const sender =
        account.type === 'user' ? sendMessageAsUser : sendMessageAsStore
      const msg = await sender(token, conversationId, payload)
      handleIncoming(conversationId, msg)
    },
    [account, handleIncoming, token],
  )

  const runAssistantAction = useCallback(
    async (conversationId: string, payload: AssistantActionPayload) => {
      if (!token || !account || account.type !== 'user') return
      const msg = await submitAssistantAction(token, conversationId, payload)
      handleIncoming(conversationId, msg)
    },
    [account, handleIncoming, token],
  )

  const markRead = useCallback(
    async (conversationId: string) => {
      if (!token || !account) return
      const reader =
        account.type === 'user' ? markReadAsUser : markReadAsStore
      try {
        await reader(token, conversationId)
      } catch {
        // ignore
      }
      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId ? { ...c, unread_count: 0 } : c,
        ),
      )
      socket.markRead(conversationId)
    },
    [account, socket, token],
  )

  const openWithStore = useCallback(
    async (storeId: string) => {
      if (!token || !account || account.type !== 'user') {
        throw new Error('User login required')
      }
      const conv = await openStoreConversation(token, storeId)
      setConversations(prev => {
        if (prev.some(c => c.id === conv.id)) return prev
        return [conv, ...prev]
      })
      return conv
    },
    [account, token],
  )

  const openSystem = useCallback(async () => {
    if (!token || !account || account.type !== 'user') {
      throw new Error('User login required')
    }
    const conv = await openSystemConversation(token)
    setConversations(prev => {
      if (prev.some(c => c.id === conv.id)) return prev
      return [conv, ...prev]
    })
    return conv
  }, [account, token])

  const unreadTotal = useMemo(
    () => conversations.reduce((acc, c) => acc + (c.unread_count || 0), 0),
    [conversations],
  )

  const value: ChatContextValue = {
    conversations,
    messagesByConversation,
    activeConversationId,
    setActiveConversationId,
    unreadTotal,
    refreshConversations,
    loadMessages,
    sendMessage,
    runAssistantAction,
    markRead,
    openWithStore,
    openSystem,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

function isIncrementable(msg: Message, viewer?: 'user' | 'store') {
  if (!viewer) return false
  if (viewer === 'user' && msg.sender_type === 'user') return false
  if (viewer === 'store' && msg.sender_type === 'store') return false
  return true
}

// Convenience hook to react when the user enters a specific thread.
export function useActiveThread(conversationId: string | undefined) {
  const chat = useChat()
  useEffect(() => {
    if (!conversationId) return
    chat.setActiveConversationId(conversationId)
    void chat.loadMessages(conversationId)
    void chat.markRead(conversationId)
    return () => {
      chat.setActiveConversationId(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId])
}
