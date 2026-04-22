import clsx from 'clsx'
import { useEffect, useState } from 'react'
import type { Message, SenderType } from '../../types/chat'
import ProductRefCard from './ProductRefCard'
import OrderRefCard from './OrderRefCard'
import AssistantProductCarousel from './AssistantProductCarousel'
import AssistantOrderConfirmationCard from './AssistantOrderConfirmationCard'
import AssistantOrderResultCard from './AssistantOrderResultCard'

interface Props {
  message: Message
  viewerType: 'user' | 'store'
  animate?: boolean
  onAssistantAction?: (actionId: string, data?: Record<string, unknown>) => Promise<void>
}

export default function MessageBubble({
  message,
  viewerType,
  animate = false,
  onAssistantAction,
}: Props) {
  const side = alignment(message.sender_type, viewerType)
  const showRef =
    message.ref_type === 'product' ||
    message.ref_type === 'order' ||
    message.ref_type === 'order_event'
  const [entered, setEntered] = useState(!animate)

  useEffect(() => {
    if (!animate) return
    setEntered(false)
    const frame = window.requestAnimationFrame(() => {
      setEntered(true)
    })
    return () => window.cancelAnimationFrame(frame)
  }, [animate, message.id])

  return (
    <div
      className={clsx(
        'flex w-full transition-all duration-200 ease-out',
        entered ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0',
        side === 'right' ? 'justify-end' : 'justify-start',
      )}
    >
      <div
        className={clsx(
          'max-w-[75%] rounded-pin-md px-3.5 py-2.5 text-sm',
          side === 'right'
            ? 'bg-brand-red text-white'
            : side === 'left'
              ? 'bg-white border border-sand text-plum'
              : 'bg-fog border border-sand text-plum italic',
        )}
      >
        {showRef && message.ref_type && message.ref_id && (
          <div className="mb-2">
            {message.ref_type === 'product' && (
              <ProductRefCard productId={message.ref_id} />
            )}
            {(message.ref_type === 'order' ||
              message.ref_type === 'order_event') && (
              <OrderRefCard
                orderId={message.ref_id}
                payload={message.ref_payload}
              />
            )}
          </div>
        )}
        {message.assistant_payload && (
          <div className="mb-2">
            {message.assistant_payload.type === 'product_carousel' && (
              <AssistantProductCarousel payload={message.assistant_payload} />
            )}
            {message.assistant_payload.type === 'order_confirmation' && onAssistantAction && (
              <AssistantOrderConfirmationCard
                payload={message.assistant_payload}
                onConfirm={draftId =>
                  onAssistantAction('confirm_order', { draft_id: draftId })
                }
              />
            )}
            {message.assistant_payload.type === 'order_result' && (
              <AssistantOrderResultCard payload={message.assistant_payload} />
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <span
          className={clsx(
            'block mt-1 text-[10px]',
            side === 'right' ? 'text-white/75' : 'text-warm-silver',
          )}
        >
          {formatTime(message.created_at)}
        </span>
      </div>
    </div>
  )
}

function alignment(
  sender: SenderType,
  viewer: 'user' | 'store',
): 'left' | 'right' | 'center' {
  if (sender === 'system') return 'center'
  if (viewer === 'user') return sender === 'user' ? 'right' : 'left'
  return sender === 'store' ? 'right' : 'left'
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
