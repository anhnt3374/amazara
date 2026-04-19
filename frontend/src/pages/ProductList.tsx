import { useProductFilters } from '../hooks/useProductFilters'
import FilterBar from '../components/FilterBar'
import ProductGrid from '../components/ProductGrid'
import Pagination from '../components/Pagination'

export default function ProductList() {
  const {
    filters, setFilters, products, total,
    availableBrands, availableCategories, loading,
  } = useProductFilters()

  const totalPages = Math.min(Math.ceil(total / 20), 25)

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
      <ProductGrid products={products} />
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
