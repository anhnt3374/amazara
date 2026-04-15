import { useState, useEffect } from 'react'
import type { Brand, Category, ProductFilters, SortOption } from '../types/product'
import { PRICE_RANGES } from '../data/mockProducts'
import FilterDropdown from './FilterDropdown'

interface FilterBarProps {
  filters: ProductFilters
  onFiltersChange: (filters: ProductFilters) => void
  brands: Brand[]
  categories: Category[]
}

const SORT_OPTIONS = [
  { value: 'best-sellers', label: 'Best Sellers' },
  { value: 'newest', label: 'Newest' },
  { value: 'price-high-low', label: 'Price High To Low' },
  { value: 'price-low-high', label: 'Price Low To High' },
  { value: 'discount-rate', label: 'Discount Rate' },
]

export default function FilterBar({ filters, onFiltersChange, brands, categories }: FilterBarProps) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 0)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const priceOptions = PRICE_RANGES.map(r => ({ value: r.value, label: r.label }))
  const brandOptions = brands.map(b => ({ value: b.id, label: b.name }))
  const categoryOptions = categories.map(c => ({ value: c.id, label: c.name }))

  const selectedPrice = filters.priceRange
    ? PRICE_RANGES.find(r => r.range[0] === filters.priceRange![0] && r.range[1] === filters.priceRange![1])?.value ?? null
    : null

  function handlePriceSelect(value: string | null) {
    const range = value ? PRICE_RANGES.find(r => r.value === value)?.range ?? null : null
    onFiltersChange({ ...filters, priceRange: range })
  }

  function handleBrandSelect(value: string | null) {
    onFiltersChange({ ...filters, brandId: value, categoryId: null })
  }

  function handleCategorySelect(value: string | null) {
    onFiltersChange({ ...filters, categoryId: value })
  }

  function handleSortSelect(value: string | null) {
    onFiltersChange({ ...filters, sort: (value ?? 'best-sellers') as SortOption })
  }

  return (
    <div
      className="sticky top-[46px] z-30 bg-white flex items-center justify-between px-12 h-[46px] border-y border-[#e5e5e5]"
      style={{ boxShadow: scrolled ? '0 1px 4px rgba(0,0,0,0.08)' : 'none' }}
    >
      <div className="flex items-center gap-3">
        <FilterDropdown
          label="Price"
          options={priceOptions}
          selected={selectedPrice}
          onSelect={handlePriceSelect}
        />
        <FilterDropdown
          label="Brand"
          options={brandOptions}
          selected={filters.brandId}
          onSelect={handleBrandSelect}
        />
        <FilterDropdown
          label="Category"
          options={categoryOptions}
          selected={filters.categoryId}
          onSelect={handleCategorySelect}
        />
      </div>
      <div>
        <FilterDropdown
          label="Sort by"
          options={SORT_OPTIONS}
          selected={filters.sort}
          onSelect={handleSortSelect}
          align="right"
        />
      </div>
    </div>
  )
}
