import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type MutableRefObject,
  type SetStateAction,
} from 'react'
import { useChat, useActiveThread } from '../../contexts/ChatContext'
import { useAuth } from '../../hooks/useAuth'
import type { Conversation, Message } from '../../types/chat'
import MessageBubble from './MessageBubble'
import MessageComposer from './MessageComposer'

interface Props {
  conversation: Conversation
}

interface VisibleMessage {
  message: Message
  animate: boolean
}

export default function MessageThread({ conversation }: Props) {
  const { account } = useAuth()
  const chat = useChat()
  useActiveThread(conversation.id)

  const messages = useMemo(
    () => chat.messagesByConversation[conversation.id] ?? [],
    [chat.messagesByConversation, conversation.id],
  )

  const viewerType: 'user' | 'store' =
    account?.type === 'store' ? 'store' : 'user'

  const scrollRef = useRef<HTMLDivElement | null>(null)
  const revealTimerRef = useRef<number | null>(null)
  const revealQueueRef = useRef<Message[]>([])
  const [visibleMessages, setVisibleMessages] = useState<VisibleMessage[]>([])
  const [draftValue, setDraftValue] = useState('')

  useEffect(() => {
    setVisibleMessages(messages.map(message => ({ message, animate: false })))
    revealQueueRef.current = []
    if (revealTimerRef.current !== null) {
      window.clearTimeout(revealTimerRef.current)
      revealTimerRef.current = null
    }
  }, [conversation.id])

  useEffect(() => {
    setDraftValue('')
  }, [conversation.id])

  useEffect(() => {
    const visibleIds = visibleMessages.map(item => item.message.id)
    const nextIds = messages.map(message => message.id)

    if (sameIds(visibleIds, nextIds)) return

    if (
      visibleMessages.length === 0 ||
      messages.length < visibleMessages.length ||
      !isPrefix(visibleIds, nextIds)
    ) {
      revealQueueRef.current = []
      if (revealTimerRef.current !== null) {
        window.clearTimeout(revealTimerRef.current)
        revealTimerRef.current = null
      }
      setVisibleMessages(messages.map(message => ({ message, animate: false })))
      return
    }

    const queuedIds = new Set(revealQueueRef.current.map(message => message.id))
    const appended = messages
      .slice(visibleMessages.length)
      .filter(message => !queuedIds.has(message.id))

    if (appended.length === 0) return

    revealQueueRef.current = [...revealQueueRef.current, ...appended]
    queueNextReveal(revealQueueRef, revealTimerRef, viewerType, setVisibleMessages)
  }, [messages, viewerType, visibleMessages])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [visibleMessages.length])

  useEffect(() => {
    return () => {
      if (revealTimerRef.current !== null) {
        window.clearTimeout(revealTimerRef.current)
      }
    }
  }, [])

  const partnerName =
    conversation.type === 'user_system'
      ? 'Amaraza Assistant'
      : conversation.partner.display_name

  const handleInsertToChat = (value: string) => {
    setDraftValue(prev => appendDraftToken(prev, value))
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white">
      <div className="h-14 border-b border-sand flex items-center px-5 shrink-0">
        <span className="text-sm font-semibold text-plum">{partnerName}</span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-2 bg-fog"
      >
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-sm text-olive">
            No messages yet. Say hello!
          </div>
        ) : (
          visibleMessages.map(({ message, animate }) => (
            <MessageBubble
              key={message.id}
              message={message}
              viewerType={viewerType}
              animate={animate}
              onAssistantAction={
                viewerType === 'user'
                  ? (actionId, data) =>
                      chat.runAssistantAction(conversation.id, {
                        action_id: actionId,
                        data: data ?? null,
                      })
                  : undefined
              }
              onAssistantInsert={viewerType === 'user' ? handleInsertToChat : undefined}
            />
          ))
        )}
      </div>

      <MessageComposer
        value={draftValue}
        onChange={setDraftValue}
        onSend={content => chat.sendMessage(conversation.id, { content })}
      />
    </div>
  )
}

function appendDraftToken(current: string, token: string) {
  const trimmed = current.trimEnd()
  if (!trimmed) return token
  if (trimmed.includes(token)) return trimmed
  return `${trimmed} ${token}`
}

function queueNextReveal(
  revealQueueRef: MutableRefObject<Message[]>,
  revealTimerRef: MutableRefObject<number | null>,
  viewerType: 'user' | 'store',
  setVisibleMessages: Dispatch<SetStateAction<VisibleMessage[]>>,
) {
  if (revealTimerRef.current !== null || revealQueueRef.current.length === 0) return

  const nextMessage = revealQueueRef.current[0]
  revealTimerRef.current = window.setTimeout(() => {
    revealTimerRef.current = null
    const revealed = revealQueueRef.current.shift()
    if (!revealed) return
    setVisibleMessages(prev => [...prev, { message: revealed, animate: true }])
    queueNextReveal(revealQueueRef, revealTimerRef, viewerType, setVisibleMessages)
  }, revealDelay(nextMessage, viewerType))
}

function revealDelay(message: Message, viewerType: 'user' | 'store') {
  if (isOwnMessage(message, viewerType)) return 0
  if (message.sender_type === 'bot' || message.sender_type === 'system') return 220
  return 120
}

function isOwnMessage(message: Message, viewerType: 'user' | 'store') {
  return (
    (viewerType === 'user' && message.sender_type === 'user') ||
    (viewerType === 'store' && message.sender_type === 'store')
  )
}

function sameIds(left: string[], right: string[]) {
  if (left.length !== right.length) return false
  return left.every((id, index) => id === right[index])
}

function isPrefix(prefix: string[], full: string[]) {
  if (prefix.length > full.length) return false
  return prefix.every((id, index) => id === full[index])
}
