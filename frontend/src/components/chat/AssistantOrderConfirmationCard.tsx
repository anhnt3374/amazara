import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { OrderConfirmationPayload } from '../../types/chat'
import { formatVnd } from '../../utils/money'

interface Props {
  payload: OrderConfirmationPayload
  onConfirm: (draftId: string) => Promise<void>
}

export default function AssistantOrderConfirmationCard({
  payload,
  onConfirm,
}: Props) {
  const [submitting, setSubmitting] = useState(false)

  const handleConfirm = async () => {
    if (submitting) return
    setSubmitting(true)
    try {
      await onConfirm(payload.action.draft_id)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-pin border border-sand bg-white p-3 text-xs text-plum">
      <div className="flex gap-3">
        <div className="h-16 w-16 shrink-0 overflow-hidden rounded-pin bg-fog border border-sand">
          {payload.product.image ? (
            <img
              src={payload.product.image}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : null}
        </div>
        <div className="min-w-0 flex-1">
          <Link
            to={`/product/${payload.product.product_id}`}
            className="line-clamp-2 text-sm font-semibold text-plum hover:text-brand-red"
          >
            {payload.product.name}
          </Link>
          <p className="mt-1 break-all text-[11px] text-olive">
            Code: {payload.product.product_id}
          </p>
          <p className="mt-1 text-brand-red font-semibold">
            {formatVnd(payload.product.final_price)}
          </p>
        </div>
      </div>
      <div className="mt-3 grid gap-1 text-[11px] text-olive">
        <p>Quantity: {payload.quantity}</p>
        <p>Deliver to: {payload.address.client_name} ({payload.address.phone})</p>
        <p>{payload.address.place}</p>
        <p>Shipping: {formatVnd(payload.shipping_fee)}</p>
        <p className="text-sm font-semibold text-plum">
          Total: {formatVnd(payload.total_amount)}
        </p>
      </div>
      <button
        type="button"
        onClick={() => void handleConfirm()}
        disabled={submitting}
        className="mt-3 h-9 rounded-pin bg-brand-red px-4 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-brand-red-hover)] disabled:cursor-not-allowed disabled:bg-sand disabled:text-warm-silver"
      >
        {submitting ? 'Placing order...' : payload.action.label}
      </button>
    </div>
  )
}
