import { useProductFilters } from '../hooks/useProductFilters'
import { useAuth } from '../hooks/useAuth'
import { addFavorite, removeFavorite } from '../services/favorite'
import FilterBar from '../components/FilterBar'
import ProductGrid from '../components/ProductGrid'
import Pagination from '../components/Pagination'

export default function ProductList() {
  const {
    filters, setFilters, products, setProducts, total,
    availableBrands, availableCategories, loading,
  } = useProductFilters()
  const { account, token } = useAuth()

  const canFavorite = account?.type === 'user' && !!token
  const totalPages = Math.min(Math.ceil(total / 20), 25)

  async function handleToggleFavorite(productId: string, next: boolean) {
    if (!token) return
    setProducts(prev => prev.map(p =>
      p.id === productId ? { ...p, isFavorited: next } : p
    ))
    try {
      if (next) await addFavorite(token, productId)
      else await removeFavorite(token, productId)
    } catch {
      setProducts(prev => prev.map(p =>
        p.id === productId ? { ...p, isFavorited: !next } : p
      ))
    }
  }

  return (
    <div>
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        availableBrands={availableBrands}
        availableCategories={availableCategories}
      />
      <div className="px-12 py-4">
        <p className="text-sm font-semibold text-plum uppercase tracking-wide">
          {loading ? 'Searching...' : `${total} Products Found`}
        </p>
      </div>
      <ProductGrid
        products={products}
        onToggleFavorite={canFavorite ? handleToggleFavorite : undefined}
      />
      {totalPages > 1 && (
        <div className="px-12 py-8">
          <Pagination
            currentPage={filters.page}
            totalPages={totalPages}
            onPageChange={page => setFilters({ ...filters, page })}
          />
        </div>
      )}
    </div>
  )
}
