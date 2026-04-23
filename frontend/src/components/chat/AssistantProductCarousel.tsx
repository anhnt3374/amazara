import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeftIcon, ChevronRightIcon } from '../Icons'
import { useAuth } from '../../hooks/useAuth'
import { addFavorite } from '../../services/favorite'
import type { ProductCarouselPayload } from '../../types/chat'
import { formatVnd } from '../../utils/money'

const GAP_PX = 12

export default function AssistantProductCarousel({
  payload,
  onAddToChat,
}: {
  payload: ProductCarouselPayload
  onAddToChat?: (value: string) => void
}) {
  const { token, account } = useAuth()
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const [viewportWidth, setViewportWidth] = useState(0)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(payload.items.length > 1)
  const [favoriteBusyId, setFavoriteBusyId] = useState<string | null>(null)
  const [favoritedIds, setFavoritedIds] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const node = viewportRef.current
    if (!node) return

    const updateScrollState = () => {
      const maxScrollLeft = node.scrollWidth - node.clientWidth
      setCanScrollLeft(node.scrollLeft > 4)
      setCanScrollRight(node.scrollLeft < maxScrollLeft - 4)
      setViewportWidth(node.clientWidth)
    }

    const observer = new ResizeObserver(() => {
      updateScrollState()
    })

    updateScrollState()
    observer.observe(node)
    node.addEventListener('scroll', updateScrollState, { passive: true })
    return () => {
      observer.disconnect()
      node.removeEventListener('scroll', updateScrollState)
    }
  }, [payload.items.length])

  const itemsPerPage = useMemo(() => {
    if (viewportWidth >= 720) return 3
    if (viewportWidth >= 430) return 2
    return 1
  }, [viewportWidth])

  const cardWidth = useMemo(() => {
    if (!viewportWidth) return 0
    return Math.max(
      (viewportWidth - GAP_PX * (itemsPerPage - 1)) / itemsPerPage,
      180,
    )
  }, [itemsPerPage, viewportWidth])

  const scrollByPage = (direction: 'left' | 'right') => {
    const node = viewportRef.current
    if (!node) return
    const amount = viewportWidth || node.clientWidth
    node.scrollBy({
      left: direction === 'left' ? -amount : amount,
      behavior: 'smooth',
    })
  }

  const handleAddFavorite = async (productId: string) => {
    if (!token || account?.type !== 'user' || favoriteBusyId === productId || favoritedIds[productId]) {
      return
    }
    setFavoriteBusyId(productId)
    try {
      await addFavorite(token, productId)
      setFavoritedIds(prev => ({ ...prev, [productId]: true }))
    } catch {
      // Keep the action lightweight in chat; failure simply leaves the button enabled.
    } finally {
      setFavoriteBusyId(current => (current === productId ? null : current))
    }
  }

  return (
    <div className="flex w-full max-w-[42rem] min-w-0 flex-col gap-2 overflow-hidden">
      <div className="flex items-center justify-between gap-2 text-[11px] text-olive">
        <span className="truncate">Query: {payload.query}</span>
        <span className="shrink-0">
          Page {payload.page} • {payload.total} result{payload.total === 1 ? '' : 's'}
        </span>
      </div>

      <div className="relative min-w-0 overflow-hidden">
        {canScrollLeft && (
          <button
            type="button"
            onClick={() => scrollByPage('left')}
            className="absolute left-1 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-warm-light/95 text-plum shadow-sm transition-colors hover:bg-[color:var(--color-border-hover)]"
            aria-label="Previous products"
          >
            <ChevronLeftIcon />
          </button>
        )}

        {canScrollRight && (
          <button
            type="button"
            onClick={() => scrollByPage('right')}
            className="absolute right-1 top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-warm-light/95 text-plum shadow-sm transition-colors hover:bg-[color:var(--color-border-hover)]"
            aria-label="Next products"
          >
            <ChevronRightIcon />
          </button>
        )}

        <div
          ref={viewportRef}
          className="flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-smooth pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {payload.items.map(item => (
            <div
              key={item.product_id}
              className="shrink-0 snap-start rounded-pin border border-sand bg-white p-3"
              style={cardWidth ? { width: `${cardWidth}px` } : undefined}
            >
              <Link
                to={`/product/${item.product_id}`}
                className="block transition-colors hover:text-brand-red"
              >
              <div className="overflow-hidden rounded-pin border border-sand bg-fog">
                <div className="aspect-[1/0.72]">
                  {item.image ? (
                    <img
                      src={item.image}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-olive">
                      No image
                    </div>
                  )}
                </div>
              </div>

              <p className="mt-2 line-clamp-2 text-xs font-semibold text-plum">
                {item.name}
              </p>
              <p className="mt-1 line-clamp-2 break-all text-[11px] text-olive">
                Code: {item.product_id}
              </p>

              <div className="mt-2 flex items-end justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-brand-red">
                    {formatVnd(item.final_price)}
                  </p>
                  {item.discount > 0 && (
                    <p className="text-[11px] text-warm-silver line-through">
                      {formatVnd(item.price)}
                    </p>
                  )}
                </div>
                <span className="shrink-0 text-[11px] text-olive">
                  Stock {item.stock}
                </span>
              </div>
              </Link>

              <div className="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => onAddToChat?.(`Product [${item.product_id}]`)}
                  className="inline-flex h-8 items-center rounded-pin border border-sand px-3 text-xs font-semibold text-plum transition-colors hover:border-[color:var(--color-border-hover)] hover:bg-fog"
                >
                  Add to chat
                </button>
                <button
                  type="button"
                  onClick={() => void handleAddFavorite(item.product_id)}
                  disabled={
                    !token ||
                    account?.type !== 'user' ||
                    favoriteBusyId === item.product_id ||
                    Boolean(favoritedIds[item.product_id])
                  }
                  className="inline-flex h-8 items-center rounded-pin border border-brand-red px-3 text-xs font-semibold text-brand-red transition-colors hover:bg-brand-red hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {favoritedIds[item.product_id] ? 'Added to favorite' : 'Add to favorite'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
