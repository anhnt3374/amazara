import { Link } from 'react-router-dom'
import type { Product } from '../../types/product'

interface CompactProductCardProps {
  product: Product
}

export default function CompactProductCard({ product }: CompactProductCardProps) {
  const discountedPrice =
    product.discount > 0
      ? Math.round(product.price * (1 - product.discount / 100))
      : null
  const cover = product.images[0] ?? ''

  return (
    <Link
      to={`/product/${product.id}`}
      className="group block bg-white rounded-pin border border-sand hover:border-plum transition-colors overflow-hidden"
    >
      <div className="relative aspect-square bg-fog">
        {cover && (
          <img
            src={cover}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        )}
        {product.discount > 0 && (
          <span className="absolute top-2 left-2 bg-brand-red text-white text-[10px] font-semibold px-1.5 py-0.5 rounded-pin-sm">
            {product.discount}% OFF
          </span>
        )}
      </div>
      <div className="p-2">
        <h4 className="text-xs text-plum line-clamp-2 min-h-[32px]">
          {product.name}
        </h4>
        <div className="mt-1 flex items-baseline gap-1">
          {discountedPrice !== null ? (
            <>
              <span className="text-xs font-semibold text-brand-red">
                {discountedPrice.toLocaleString('vi-VN')}&#8363;
              </span>
              <span className="text-[10px] text-warm-silver line-through">
                {product.price.toLocaleString('vi-VN')}&#8363;
              </span>
            </>
          ) : (
            <span className="text-xs font-semibold text-plum">
              {product.price.toLocaleString('vi-VN')}&#8363;
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
