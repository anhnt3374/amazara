import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProduct } from '../../services/product'
import type { Product } from '../../types/product'
import { formatVnd, priceAfterDiscount } from '../../utils/money'

export default function ProductRefCard({ productId }: { productId: string }) {
  const [product, setProduct] = useState<Product | null>(null)

  useEffect(() => {
    let cancelled = false
    getProduct(productId)
      .then(p => {
        if (!cancelled) setProduct(p)
      })
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [productId])

  if (!product) {
    return (
      <div className="rounded-pin border border-sand bg-fog px-2 py-1.5 text-xs text-olive">
        Loading product...
      </div>
    )
  }

  const image = product.images[0] ?? null
  const finalPrice = priceAfterDiscount(product.price, product.discount)
  return (
    <Link
      to={`/product/${product.id}`}
      className="flex items-center gap-2 rounded-pin border border-sand bg-white px-2 py-1.5 hover:border-[color:var(--color-border-hover)] transition-colors"
    >
      {image ? (
        <img
          src={image}
          alt=""
          className="w-10 h-10 rounded-md object-cover"
        />
      ) : (
        <div className="w-10 h-10 rounded-md bg-sand" />
      )}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold text-plum truncate">{product.name}</p>
        <p className="text-xs text-brand-red mt-0.5">{formatVnd(finalPrice)}</p>
      </div>
    </Link>
  )
}
