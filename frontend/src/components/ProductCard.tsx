import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Product } from '../types/product'
import { ChevronLeftIcon, ChevronRightIcon, HeartFilledIcon, HeartIcon } from './Icons'

interface ProductCardProps {
  product: Product
  onToggleFavorite?: (productId: string, next: boolean) => void
}

export default function ProductCard({ product, onToggleFavorite }: ProductCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const hasMultipleImages = product.images.length > 1
  const isSoldOut = product.stock === 0

  const discountedPrice = product.discount > 0
    ? Math.round(product.price * (1 - product.discount / 100))
    : null

  function prevImage(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImageIndex(i =>
      i === 0 ? product.images.length - 1 : i - 1
    )
  }

  function nextImage(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImageIndex(i =>
      i === product.images.length - 1 ? 0 : i + 1
    )
  }

  function handleToggleFavorite(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    onToggleFavorite?.(product.id, !product.isFavorited)
  }

  return (
    <Link
      to={`/product/${product.id}`}
      className="group cursor-pointer block bg-white rounded-pin-md border border-sand overflow-hidden transition-shadow hover:shadow-[0_6px_16px_rgba(33,25,34,0.08)]"
    >
      {/* Image container */}
      <div className="relative aspect-square bg-fog overflow-hidden">
        <img
          src={product.images[currentImageIndex]}
          alt={product.name}
          className={`w-full h-full object-cover ${isSoldOut ? 'grayscale opacity-55' : ''}`}
        />

        {/* Sold-out or discount badge (sold-out wins) */}
        {isSoldOut ? (
          <span className="absolute top-3 left-3 bg-brand-red text-white text-xs font-semibold px-2 py-1 rounded-pin-sm">
            Out of Stock
          </span>
        ) : product.discount > 0 ? (
          <span className="absolute top-3 left-3 bg-brand-red text-white text-xs font-semibold px-2 py-1 rounded-pin-sm">
            {product.discount}% OFF
          </span>
        ) : null}

        {/* Heart toggle (user-only — parent passes onToggleFavorite) */}
        {onToggleFavorite && (
          <button
            type="button"
            onClick={handleToggleFavorite}
            aria-label={product.isFavorited ? 'Remove from favorites' : 'Add to favorites'}
            className="absolute top-3 right-3 w-9 h-9 bg-white/85 hover:bg-white rounded-full flex items-center justify-center shadow-sm transition-colors"
          >
            {product.isFavorited ? (
              <HeartFilledIcon className="text-brand-red" />
            ) : (
              <HeartIcon className="text-plum" />
            )}
          </button>
        )}

        {/* Image navigation arrows */}
        {hasMultipleImages && (
          <>
            <button
              onClick={prevImage}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-9 h-9 bg-white/85 hover:bg-white text-plum rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronLeftIcon />
            </button>
            <button
              onClick={nextImage}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 bg-white/85 hover:bg-white text-plum rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronRightIcon />
            </button>
          </>
        )}

        {/* Image dots indicator */}
        {hasMultipleImages && (
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
            {product.images.map((_, idx) => (
              <span
                key={idx}
                className={`w-1.5 h-1.5 rounded-full transition-colors ${
                  idx === currentImageIndex ? 'bg-brand-red' : 'bg-white/70'
                }`}
              />
            ))}
          </div>
        )}
      </div>

      {/* Product info */}
      <div className={`px-3 pt-2.5 pb-3 ${isSoldOut ? 'opacity-60' : ''}`}>
        <h3 className="text-sm font-medium text-plum line-clamp-2">{product.name}</h3>
        <div className="mt-1 flex items-center gap-2">
          {discountedPrice !== null ? (
            <>
              <span className="text-sm font-semibold text-brand-red">
                {discountedPrice.toLocaleString('vi-VN')} &#8363;
              </span>
              <span className="text-sm text-warm-silver line-through">
                {product.price.toLocaleString('vi-VN')} &#8363;
              </span>
            </>
          ) : (
            <span className="text-sm font-medium text-plum">
              {product.price.toLocaleString('vi-VN')} &#8363;
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
