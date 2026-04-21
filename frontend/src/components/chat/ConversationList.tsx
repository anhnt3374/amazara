import clsx from 'clsx'
import type { Conversation } from '../../types/chat'
import { formatVnd } from '../../utils/money'

interface Props {
  conversations: Conversation[]
  activeId?: string | null
  onSelect: (conv: Conversation) => void
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
}: Props) {
  if (conversations.length === 0) {
    return (
      <div className="p-4 text-sm text-olive">
        No conversations yet. Try contacting a seller from a product or order
        page.
      </div>
    )
  }
  return (
    <ul className="divide-y divide-[color:var(--color-sand)]">
      {conversations.map(conv => (
        <li key={conv.id}>
          <button
            type="button"
            onClick={() => onSelect(conv)}
            className={clsx(
              'w-full px-4 py-3 flex items-start gap-3 text-left transition-colors',
              activeId === conv.id ? 'bg-fog' : 'hover:bg-fog',
            )}
          >
            <Avatar conv={conv} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-plum truncate">
                  {conv.type === 'user_system'
                    ? 'Amaraza Assistant'
                    : conv.partner.display_name}
                </span>
                {conv.unread_count > 0 && (
                  <span className="shrink-0 min-w-[20px] h-5 px-1.5 rounded-full bg-brand-red text-white text-[11px] font-semibold flex items-center justify-center">
                    {conv.unread_count > 99 ? '99+' : conv.unread_count}
                  </span>
                )}
              </div>
              <p className="text-xs text-olive mt-0.5 truncate">
                {renderPreview(conv)}
              </p>
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}

function renderPreview(conv: Conversation): string {
  const msg = conv.last_message
  if (!msg) {
    return conv.type === 'user_system'
      ? 'Ask anything — we are here to help.'
      : 'Start the conversation.'
  }
  if (msg.ref_type === 'order_event' && msg.ref_payload) {
    const total = (msg.ref_payload as { total_amount?: number }).total_amount
    if (typeof total === 'number') return `${msg.content} • ${formatVnd(total)}`
  }
  return msg.content
}

function Avatar({ conv }: { conv: Conversation }) {
  const letter =
    conv.type === 'user_system'
      ? 'S'
      : (conv.partner.display_name.trim()[0] ?? '?').toUpperCase()
  if (conv.partner.avatar) {
    return (
      <img
        src={conv.partner.avatar}
        alt=""
        className="w-10 h-10 rounded-full object-cover shrink-0"
      />
    )
  }
  return (
    <div
      className={clsx(
        'w-10 h-10 rounded-full flex items-center justify-center font-semibold text-plum shrink-0',
        conv.type === 'user_system' ? 'bg-warm-light' : 'bg-sand',
      )}
    >
      {letter}
    </div>
  )
}
