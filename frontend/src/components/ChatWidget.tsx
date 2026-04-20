import { useState } from 'react'
import clsx from 'clsx'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../contexts/ChatContext'
import ConversationList from './chat/ConversationList'
import {
  ChatBubbleIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  HelpCircleIcon,
  HomeIcon,
  SearchIcon,
  XIcon,
} from './Icons'

type Tab = 'home' | 'messages' | 'help'

const COLLECTIONS = [
  { title: 'Order & Shipping', desc: 'Tracking, delivery windows, address changes', count: '12 articles' },
  { title: 'Returns & Refunds', desc: 'Eligibility, timelines, how to initiate', count: '8 articles' },
  { title: 'Payment Methods', desc: 'Cards, wallets, installment plans', count: '6 articles' },
  { title: 'Product Information', desc: 'Sizing, materials, authenticity', count: '15 articles' },
  { title: 'Account & Security', desc: 'Login, password, 2FA', count: '9 articles' },
]

export default function ChatWidget() {
  const { account } = useAuth()
  const user = account?.type === 'user' ? account : null
  const navigate = useNavigate()
  const chat = useChat()
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<Tab>('home')

  const greetingName = user?.fullname || user?.username || account?.displayName || 'there'
  const effectiveTab: Tab = tab === 'messages' && !user ? 'home' : tab

  const requireLogin = () => {
    setOpen(false)
    navigate('/login')
  }

  const handleSelectTab = (next: Tab) => {
    if (next === 'messages' && !user) {
      requireLogin()
      return
    }
    setTab(next)
  }

  const handleOpenMessages = () => {
    if (!user) {
      requireLogin()
      return
    }
    setTab('messages')
  }

  const handleOpenConversation = (id: string) => {
    setOpen(false)
    navigate(`/messages/${id}`)
  }

  const handleStartSystem = async () => {
    if (!user) {
      requireLogin()
      return
    }
    try {
      const conv = await chat.openSystem()
      handleOpenConversation(conv.id)
    } catch {
      // Surface failure silently; user can retry from the widget.
    }
  }

  const badge = user && chat.unreadTotal > 0 ? chat.unreadTotal : 0

  return (
    <div
      className="fixed right-6 z-50 flex flex-col items-end gap-3"
      style={{ bottom: 'calc(1.5rem + var(--bottom-bar-offset, 0px))' }}
    >
      {open && (
        <div className="w-[360px] h-[560px] bg-white rounded-pin-lg border border-sand shadow-[0_20px_50px_rgba(33,25,34,0.18)] flex flex-col overflow-hidden">
          {effectiveTab === 'home' && (
            <HomeTab
              name={greetingName}
              onClose={() => setOpen(false)}
              onOpenMessages={handleOpenMessages}
              onOpenHelp={() => setTab('help')}
            />
          )}
          {effectiveTab === 'messages' && (
            <MessagesTab
              onClose={() => setOpen(false)}
              conversations={chat.conversations}
              onSelect={conv => handleOpenConversation(conv.id)}
              onAskAssistant={handleStartSystem}
            />
          )}
          {effectiveTab === 'help' && <HelpTab onClose={() => setOpen(false)} />}

          <TabBar tab={effectiveTab} onChange={handleSelectTab} />
        </div>
      )}

      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open support chat"
          className="relative w-14 h-14 rounded-full bg-brand-red text-white flex items-center justify-center shadow-[0_12px_30px_rgba(230,0,35,0.35)] hover:bg-[var(--color-brand-red-hover)] transition-colors focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
        >
          <ChatBubbleIcon className="w-6 h-6" />
          {badge > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[20px] h-5 px-1.5 rounded-full bg-white text-brand-red text-[11px] font-bold flex items-center justify-center border border-brand-red">
              {badge > 99 ? '99+' : badge}
            </span>
          )}
        </button>
      )}
    </div>
  )
}

function CloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label="Close"
      className="absolute right-4 top-4 w-7 h-7 rounded-full flex items-center justify-center text-olive hover:bg-fog hover:text-plum transition-colors"
    >
      <XIcon />
    </button>
  )
}

function HomeTab({
  name,
  onClose,
  onOpenMessages,
  onOpenHelp,
}: {
  name: string
  onClose: () => void
  onOpenMessages: () => void
  onOpenHelp: () => void
}) {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="relative px-5 pt-5 pb-4 shrink-0">
        <CloseButton onClose={onClose} />
        <div className="flex items-center justify-between pr-8">
          <span className="text-xl font-bold text-plum tracking-[-0.4px]">Support</span>
        </div>
        <div className="mt-5">
          <p className="text-sm text-olive">Hi {name} <span aria-hidden>👋</span></p>
          <p className="text-2xl font-bold text-plum tracking-[-0.5px] mt-0.5">How can we help?</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 flex flex-col gap-3 min-h-0">
        <button
          type="button"
          onClick={onOpenMessages}
          className="rounded-pin-md border border-sand bg-white px-4 py-3 flex items-center justify-between text-left hover:border-[color:var(--color-border-hover)] transition-colors"
        >
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-plum">Open your messages</span>
            <span className="text-xs text-olive">Chat with stores or ask our assistant</span>
          </div>
          <ChevronRightIcon className="text-olive" />
        </button>

        <div className="rounded-pin-md border border-sand bg-white px-4 py-3 flex items-start gap-3">
          <CheckCircleIcon className="text-[color:var(--color-success-green)] shrink-0 mt-0.5" />
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-plum">Status: All systems operational</span>
            <span className="text-xs text-olive">Order updates appear in your Assistant thread.</span>
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenHelp}
          className="rounded-pin-md border border-sand bg-white px-4 py-3 flex items-center justify-between text-left hover:border-[color:var(--color-border-hover)] transition-colors"
        >
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-plum">Browse frequently asked questions</span>
            <span className="text-xs text-olive">Quick answers to the most common questions</span>
          </div>
          <ChevronRightIcon className="text-olive" />
        </button>
      </div>
    </div>
  )
}

function MessagesTab({
  onClose,
  conversations,
  onSelect,
  onAskAssistant,
}: {
  onClose: () => void
  conversations: import('../types/chat').Conversation[]
  onSelect: (conv: import('../types/chat').Conversation) => void
  onAskAssistant: () => void
}) {
  return (
    <>
      <div className="relative h-14 border-b border-sand flex items-center justify-center shrink-0">
        <span className="text-base font-semibold text-plum">Messages</span>
        <CloseButton onClose={onClose} />
      </div>

      <div className="flex-1 overflow-y-auto">
        <ConversationList conversations={conversations} onSelect={onSelect} />
      </div>

      <div className="px-4 py-3 border-t border-sand flex justify-center">
        <button
          type="button"
          onClick={onAskAssistant}
          className="h-10 px-4 rounded-pin bg-brand-red text-white text-sm font-semibold flex items-center gap-2 shadow-[0_8px_20px_rgba(230,0,35,0.25)] hover:bg-[var(--color-brand-red-hover)] transition-colors"
        >
          Ask the assistant
          <HelpCircleIcon className="w-4 h-4" />
        </button>
      </div>
    </>
  )
}

function HelpTab({ onClose }: { onClose: () => void }) {
  return (
    <>
      <div className="relative h-14 border-b border-sand flex items-center justify-center shrink-0">
        <span className="text-base font-semibold text-plum">Help</span>
        <CloseButton onClose={onClose} />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="px-4 pt-3">
          <div className="flex items-center gap-2 bg-fog rounded-pin px-3 h-10">
            <SearchIcon className="w-4 h-4 text-olive" />
            <input
              type="text"
              placeholder="Search for help"
              className="flex-1 bg-transparent outline-none text-sm text-plum placeholder:text-warm-silver"
            />
          </div>
        </div>

        <p className="px-4 pt-4 pb-2 text-sm font-semibold text-plum">{COLLECTIONS.length} collections</p>

        <ul className="divide-y divide-[color:var(--color-sand)] border-t border-sand">
          {COLLECTIONS.map(c => (
            <li key={c.title}>
              <button
                type="button"
                className="w-full px-4 py-3 flex items-center justify-between gap-3 text-left hover:bg-fog transition-colors"
              >
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="text-sm font-semibold text-plum truncate">{c.title}</span>
                  <span className="text-xs text-olive truncate">{c.desc}</span>
                  <span className="text-xs text-olive mt-0.5">{c.count}</span>
                </div>
                <ChevronRightIcon className="text-olive shrink-0" />
              </button>
            </li>
          ))}
        </ul>
      </div>
    </>
  )
}

function TabBar({ tab, onChange }: { tab: Tab; onChange: (t: Tab) => void }) {
  return (
    <nav className="border-t border-sand flex items-stretch h-16 shrink-0">
      <TabButton active={tab === 'home'} onClick={() => onChange('home')} label="Home">
        <HomeIcon filled={tab === 'home'} className="w-5 h-5" />
      </TabButton>
      <TabButton active={tab === 'messages'} onClick={() => onChange('messages')} label="Messages">
        <ChatBubbleIcon filled={tab === 'messages'} className="w-5 h-5" />
      </TabButton>
      <TabButton active={tab === 'help'} onClick={() => onChange('help')} label="Help">
        <HelpCircleIcon filled={tab === 'help'} className="w-5 h-5" />
      </TabButton>
    </nav>
  )
}

function TabButton({
  active,
  onClick,
  label,
  children,
}: {
  active: boolean
  onClick: () => void
  label: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex-1 flex flex-col items-center justify-center gap-1 text-xs transition-colors',
        active ? 'text-brand-red font-semibold' : 'text-olive hover:text-plum',
      )}
    >
      {children}
      <span>{label}</span>
    </button>
  )
}
