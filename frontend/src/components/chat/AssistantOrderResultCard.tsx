import { Link } from 'react-router-dom'
import type { OrderResultPayload } from '../../types/chat'
import { formatVnd } from '../../utils/money'

export default function AssistantOrderResultCard({
  payload,
}: {
  payload: OrderResultPayload
}) {
  return (
    <div className="rounded-pin border border-sand bg-white p-3 text-xs text-plum">
      <p className="text-sm font-semibold">Order placed</p>
      <p className="mt-1 text-olive">Order ID: {payload.order.order_id}</p>
      <p className="mt-1 text-olive">
        {payload.order.product_name} x{payload.order.quantity}
      </p>
      <p className="mt-1 font-semibold text-brand-red">
        {formatVnd(payload.order.total_amount)}
      </p>
      <Link
        to="/orders"
        className="mt-3 inline-flex h-8 items-center rounded-pin border border-sand px-3 text-sm font-semibold text-plum transition-colors hover:border-[color:var(--color-border-hover)]"
      >
        View orders
      </Link>
    </div>
  )
}
