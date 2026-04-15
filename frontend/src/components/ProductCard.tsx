import { useState } from 'react'
import type { Product } from '../types/product'
import { ChevronLeftIcon, ChevronRightIcon } from './Icons'

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const hasMultipleImages = product.images.length > 1

  const discountedPrice = product.discount > 0
    ? Math.round(product.price * (1 - product.discount / 100))
    : null

  function prevImage(e: React.MouseEvent) {
    e.stopPropagation()
    setCurrentImageIndex(i =>
      i === 0 ? product.images.length - 1 : i - 1
    )
  }

  function nextImage(e: React.MouseEvent) {
    e.stopPropagation()
    setCurrentImageIndex(i =>
      i === product.images.length - 1 ? 0 : i + 1
    )
  }

  return (
    <div className="group cursor-pointer">
      {/* Image container */}
      <div className="relative aspect-square bg-[#f5f5f5] rounded-lg overflow-hidden">
        <img
          src={product.images[currentImageIndex]}
          alt={product.name}
          className="w-full h-full object-cover"
        />

        {/* Discount tag */}
        {product.discount > 0 && (
          <span className="absolute top-3 left-3 bg-[#111] text-white text-xs font-semibold px-2 py-1 rounded">
            {product.discount}% OFF
          </span>
        )}

        {/* Image navigation arrows */}
        {hasMultipleImages && (
          <>
            <button
              onClick={prevImage}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 hover:bg-white rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ChevronLeftIcon />
            </button>
            <button
              onClick={nextImage}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 hover:bg-white rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
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
                  idx === currentImageIndex ? 'bg-[#111]' : 'bg-white/60'
                }`}
              />
            ))}
          </div>
        )}
      </div>

      {/* Product info */}
      <div className="mt-3">
        <h3 className="text-sm font-medium text-[#111] line-clamp-2">{product.name}</h3>
        <div className="mt-1 flex items-center gap-2">
          {discountedPrice !== null ? (
            <>
              <span className="text-sm font-semibold text-red-600">
                {discountedPrice.toLocaleString('vi-VN')} &#8363;
              </span>
              <span className="text-sm text-[#757575] line-through">
                {product.price.toLocaleString('vi-VN')} &#8363;
              </span>
            </>
          ) : (
            <span className="text-sm font-medium text-[#111]">
              {product.price.toLocaleString('vi-VN')} &#8363;
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
