import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { getSimilarProducts } from '../../services/product'
import type { Product } from '../../types/product'
import CompactProductCard from './CompactProductCard'

interface SimilarProductsPanelProps {
  productId: string
  initialProducts: Product[]
  initialTotal: number
  initialPageSize: number
}

export default function SimilarProductsPanel({
  productId,
  initialProducts,
  initialTotal,
  initialPageSize,
}: SimilarProductsPanelProps) {
  const [page, setPage] = useState(1)
  const [products, setProducts] = useState<Product[]>(initialProducts)
  const [loading, setLoading] = useState(false)

  const totalPages = Math.max(1, Math.ceil(initialTotal / initialPageSize))

  useEffect(() => {
    if (page === 1) {
      setProducts(initialProducts)
      return
    }
    let cancelled = false
    setLoading(true)
    getSimilarProducts(productId, page)
      .then(res => {
        if (!cancelled) setProducts(res.products)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, productId, initialProducts])

  return (
    <div className="border-t border-sand bg-white px-4 py-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-plum">Similar products</span>
      </div>

      <div className="grid grid-cols-6 gap-3">
        {products.map(p => (
          <CompactProductCard key={p.id} product={p} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-1">
          <button
            type="button"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1 || loading}
            className={clsx(
              'w-7 h-7 rounded-pin border text-xs transition-colors',
              page <= 1
                ? 'border-sand text-warm-silver cursor-not-allowed'
                : 'border-sand text-plum hover:border-plum',
            )}
          >
            ‹
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setPage(p)}
              disabled={loading}
              className={clsx(
                'w-7 h-7 text-xs rounded-pin border transition-colors',
                p === page
                  ? 'border-brand-red bg-brand-red text-white'
                  : 'border-sand text-plum hover:border-plum',
              )}
            >
              {p}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages || loading}
            className={clsx(
              'w-7 h-7 rounded-pin border text-xs transition-colors',
              page >= totalPages
                ? 'border-sand text-warm-silver cursor-not-allowed'
                : 'border-sand text-plum hover:border-plum',
            )}
          >
            ›
          </button>
        </div>
      )}
    </div>
  )
}
