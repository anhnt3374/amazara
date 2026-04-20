import { Link } from 'react-router-dom'
import { formatVnd } from '../../utils/money'

interface Props {
  orderId: string
  payload?: Record<string, unknown> | null
}

export default function OrderRefCard({ orderId, payload }: Props) {
  const total =
    payload && typeof (payload as { total_amount?: number }).total_amount === 'number'
      ? ((payload as { total_amount?: number }).total_amount as number)
      : null
  const event = payload
    ? ((payload as { event?: string }).event ?? null)
    : null

  return (
    <Link
      to="/orders"
      className="block rounded-pin border border-sand bg-white px-3 py-2 text-xs hover:border-[color:var(--color-border-hover)] transition-colors"
    >
      <p className="font-semibold text-plum">Order #{orderId.slice(0, 8)}</p>
      <p className="mt-0.5 text-olive">
        {event ? labelForEvent(event) : 'View order'}
        {total !== null && (
          <span className="ml-1 text-brand-red">{formatVnd(total)}</span>
        )}
      </p>
    </Link>
  )
}

function labelForEvent(event: string): string {
  switch (event) {
    case 'created':
      return 'Order placed'
    case 'status_changed':
      return 'Status updated'
    case 'cancelled':
      return 'Order cancelled'
    default:
      return 'Order update'
  }
}
