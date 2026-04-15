import { MOCK_BRANDS, MOCK_CATEGORIES, MOCK_PRODUCTS } from '../data/mockProducts'
import { useProductFilters } from '../hooks/useProductFilters'
import FilterBar from '../components/FilterBar'
import ProductGrid from '../components/ProductGrid'

export default function ProductList() {
  const { filters, setFilters, filteredProducts, productCount } = useProductFilters(
    MOCK_PRODUCTS,
    MOCK_BRANDS,
    MOCK_CATEGORIES,
  )

  return (
    <div>
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        brands={MOCK_BRANDS}
        categories={MOCK_CATEGORIES}
      />
      <div className="px-12 py-4">
        <p className="text-sm font-semibold text-[#111] uppercase tracking-wide">
          {productCount} Products Found
        </p>
      </div>
      <ProductGrid products={filteredProducts} />
    </div>
  )
}
