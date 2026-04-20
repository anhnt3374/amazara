import { useEffect, useMemo, useState } from 'react'
import { useChat } from '../contexts/ChatContext'
import ConversationList from '../components/chat/ConversationList'
import MessageThread from '../components/chat/MessageThread'

export default function StoreMessages() {
  const chat = useChat()
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    if (!activeId && chat.conversations.length > 0) {
      setActiveId(chat.conversations[0].id)
    }
  }, [activeId, chat.conversations])

  const active = useMemo(
    () => chat.conversations.find(c => c.id === activeId) ?? null,
    [chat.conversations, activeId],
  )

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <h1 className="text-2xl font-bold text-plum mb-4">Messages</h1>
      <div className="flex h-[calc(100vh-180px)] rounded-pin-lg border border-sand bg-white overflow-hidden shadow-[0_4px_20px_rgba(33,25,34,0.06)]">
        <aside className="w-[320px] border-r border-sand flex flex-col min-h-0">
          <div className="h-14 border-b border-sand flex items-center px-5 shrink-0">
            <span className="text-sm font-semibold text-plum">Buyers</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ConversationList
              conversations={chat.conversations}
              activeId={activeId}
              onSelect={c => setActiveId(c.id)}
            />
          </div>
        </aside>
        <section className="flex-1 flex flex-col min-h-0">
          {active ? (
            <MessageThread conversation={active} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-olive">
              {chat.conversations.length === 0
                ? 'No buyer conversations yet.'
                : 'Select a buyer to open their thread.'}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
