import { useEffect, useMemo, useRef } from 'react'
import { useChat, useActiveThread } from '../../contexts/ChatContext'
import { useAuth } from '../../hooks/useAuth'
import type { Conversation } from '../../types/chat'
import MessageBubble from './MessageBubble'
import MessageComposer from './MessageComposer'

interface Props {
  conversation: Conversation
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
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length])

  const partnerName =
    conversation.type === 'user_system'
      ? 'Amaraza Assistant'
      : conversation.partner.display_name

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white">
      <div className="h-14 border-b border-sand flex items-center px-5 shrink-0">
        <span className="text-sm font-semibold text-plum">{partnerName}</span>
        {conversation.type === 'user_system' && (
          <span className="ml-2 text-[11px] text-olive">
            Automated responses — real assistant coming soon.
          </span>
        )}
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
          messages.map(m => (
            <MessageBubble key={m.id} message={m} viewerType={viewerType} />
          ))
        )}
      </div>

      <MessageComposer
        onSend={content =>
          chat.sendMessage(conversation.id, { content })
        }
      />
    </div>
  )
}
