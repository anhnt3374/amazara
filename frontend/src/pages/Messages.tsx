import { useEffect, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useChat } from '../contexts/ChatContext'
import ConversationList from '../components/chat/ConversationList'
import MessageThread from '../components/chat/MessageThread'

export default function Messages() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const chat = useChat()

  useEffect(() => {
    if (!conversationId && chat.conversations.length > 0) {
      navigate(`/messages/${chat.conversations[0].id}`, { replace: true })
    }
  }, [conversationId, chat.conversations, navigate])

  const active = useMemo(
    () => chat.conversations.find(c => c.id === conversationId) ?? null,
    [chat.conversations, conversationId],
  )

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <div className="flex h-[calc(100vh-140px)] rounded-pin-lg border border-sand bg-white overflow-hidden shadow-[0_4px_20px_rgba(33,25,34,0.06)]">
        <aside className="w-[320px] border-r border-sand flex flex-col min-h-0">
          <div className="h-14 border-b border-sand flex items-center px-5 shrink-0">
            <span className="text-sm font-semibold text-plum">Messages</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ConversationList
              conversations={chat.conversations}
              activeId={conversationId}
              onSelect={c => navigate(`/messages/${c.id}`)}
            />
          </div>
        </aside>
        <section className="flex-1 flex flex-col min-h-0">
          {active ? (
            <MessageThread conversation={active} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-olive">
              {chat.conversations.length === 0
                ? 'You have no conversations yet.'
                : 'Select a conversation to start chatting.'}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
