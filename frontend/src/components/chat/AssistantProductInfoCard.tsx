import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { addFavorite } from '../../services/favorite'
import type { ProductInfoPayload } from '../../types/chat'
import { formatVnd } from '../../utils/money'

export default function AssistantProductInfoCard({
  payload,
  onAddToChat,
}: {
  payload: ProductInfoPayload
  onAddToChat?: (value: string) => void
}) {
  const { token, account } = useAuth()
  const [favoriteBusy, setFavoriteBusy] = useState(false)
  const [favorited, setFavorited] = useState(false)
  const product = payload.product

  const handleAddFavorite = async () => {
    if (!token || account?.type !== 'user' || favoriteBusy || favorited) return
    setFavoriteBusy(true)
    try {
      await addFavorite(token, product.product_id)
      setFavorited(true)
    } catch {
      // Keep the chat card lightweight; failure leaves the action available.
    } finally {
      setFavoriteBusy(false)
    }
  }

  return (
    <div className="w-full max-w-[30rem] overflow-hidden rounded-pin border border-sand bg-white p-3">
      <div className="flex gap-3">
        <Link
          to={`/product/${product.product_id}`}
          className="block h-24 w-24 shrink-0 overflow-hidden rounded-pin border border-sand bg-fog"
        >
          {product.image ? (
            <img
              src={product.image}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-xs text-olive">
              No image
            </div>
          )}
        </Link>

        <div className="min-w-0 flex-1">
          <Link
            to={`/product/${product.product_id}`}
            className="line-clamp-2 text-sm font-semibold text-plum transition-colors hover:text-brand-red"
          >
            {product.name}
          </Link>
          <p className="mt-1 break-all text-[11px] text-olive">
            Code: {product.product_id}
          </p>
          <p className="mt-1 text-sm font-semibold text-brand-red">
            {formatVnd(product.final_price)}
          </p>
          {product.discount > 0 && (
            <p className="text-[11px] text-warm-silver line-through">
              {formatVnd(product.price)}
            </p>
          )}
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-olive">
            <span>Stock {product.stock}</span>
            {product.brand_name && <span>Brand: {product.brand_name}</span>}
            {product.category_name && <span>Category: {product.category_name}</span>}
            <span>
              Rating:{' '}
              {product.average_rating !== null
                ? `${product.average_rating.toFixed(1)} (${product.review_count})`
                : 'No ratings'}
            </span>
          </div>
        </div>
      </div>

      <p className="mt-3 line-clamp-3 text-xs text-plum">
        {product.description}
      </p>

      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          onClick={() => onAddToChat?.(`Product [${product.product_id}]`)}
          className="inline-flex h-8 items-center rounded-pin border border-sand px-3 text-xs font-semibold text-plum transition-colors hover:border-[color:var(--color-border-hover)] hover:bg-fog"
        >
          Add to chat
        </button>
        <button
          type="button"
          onClick={() => void handleAddFavorite()}
          disabled={
            !token || account?.type !== 'user' || favoriteBusy || favorited
          }
          className="inline-flex h-8 items-center rounded-pin border border-brand-red px-3 text-xs font-semibold text-brand-red transition-colors hover:bg-brand-red hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {favorited ? 'Added to favorite' : 'Add to favorite'}
        </button>
      </div>
    </div>
  )
}
