import { Link } from 'react-router-dom'
import type { ProductCarouselPayload } from '../../types/chat'
import { formatVnd } from '../../utils/money'

export default function AssistantProductCarousel({
  payload,
}: {
  payload: ProductCarouselPayload
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-[11px] text-olive">
        <span>Query: {payload.query}</span>
        <span>
          Page {payload.page} • {payload.total} result{payload.total === 1 ? '' : 's'}
        </span>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {payload.items.map(item => (
          <Link
            key={item.product_id}
            to={`/product/${item.product_id}`}
            className="w-52 shrink-0 rounded-pin border border-sand bg-white p-3 transition-colors hover:border-[color:var(--color-border-hover)]"
          >
            <div className="h-28 rounded-pin bg-fog overflow-hidden border border-sand">
              {item.image ? (
                <img
                  src={item.image}
                  alt=""
                  className="h-full w-full object-cover"
                />
              ) : null}
            </div>
            <p className="mt-2 line-clamp-2 text-xs font-semibold text-plum">
              {item.name}
            </p>
            <p className="mt-1 text-[11px] text-olive break-all">
              Code: {item.product_id}
            </p>
            <div className="mt-2 flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-brand-red">
                {formatVnd(item.final_price)}
              </span>
              <span className="text-[11px] text-olive">Stock {item.stock}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
