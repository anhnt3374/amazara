import { useEffect, useState } from 'react'
import ProductGrid from '../components/ProductGrid'
import { useAuth } from '../hooks/useAuth'
import { addFavorite, listFavoriteProducts, removeFavorite } from '../services/favorite'
import type { Product } from '../types/product'

export default function Favorites() {
  const { token, account } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || account?.type !== 'user') {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    listFavoriteProducts(token)
      .then(setProducts)
      .catch(() => setError('Failed to load favorites.'))
      .finally(() => setLoading(false))
  }, [token, account?.type])

  async function handleToggleFavorite(productId: string, next: boolean) {
    if (!token) return
    const previous = products
    if (next) {
      setProducts(prev => prev.map(p =>
        p.id === productId ? { ...p, isFavorited: true } : p
      ))
    } else {
      setProducts(prev => prev.filter(p => p.id !== productId))
    }
    try {
      if (next) await addFavorite(token, productId)
      else await removeFavorite(token, productId)
    } catch {
      setProducts(previous)
    }
  }

  return (
    <div className="bg-fog min-h-[calc(100vh-64px)]">
      <div className="max-w-[1200px] mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-plum mb-6">Your Favorites</h1>

        {loading && (
          <div className="flex items-center justify-center h-64 text-olive text-sm">
            Loading...
          </div>
        )}

        {!loading && error && (
          <div className="bg-white border border-sand rounded-pin-md px-6 py-10 text-center">
            <p className="text-sm text-[color:var(--color-error-red)]">{error}</p>
          </div>
        )}

        {!loading && !error && products.length === 0 && (
          <div className="bg-white border border-sand rounded-pin-md px-6 py-12 text-center">
            <h2 className="text-lg font-semibold text-plum">No favorites yet.</h2>
            <p className="text-sm text-olive mt-1">
              Tap the heart on a product to save it here.
            </p>
          </div>
        )}

        {!loading && !error && products.length > 0 && (
          <ProductGrid
            products={products}
            onToggleFavorite={handleToggleFavorite}
          />
        )}
      </div>
    </div>
  )
}
