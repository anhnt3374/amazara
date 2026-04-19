import { useState, useEffect } from 'react'
import type { Brand, Category, ProductFilters, SortOption } from '../types/product'
import { PRICE_RANGES } from '../data/mockProducts'
import FilterDropdown from './FilterDropdown'

interface FilterBarProps {
  filters: ProductFilters
  onFiltersChange: (filters: ProductFilters) => void
  availableBrands: Brand[]
  availableCategories: Category[]
}

const SORT_OPTIONS = [
  { value: 'best-sellers', label: 'Best Sellers' },
  { value: 'newest', label: 'Newest' },
  { value: 'price-high-low', label: 'Price High To Low' },
  { value: 'price-low-high', label: 'Price Low To High' },
  { value: 'discount-rate', label: 'Discount Rate' },
]

export default function FilterBar({ filters, onFiltersChange, availableBrands, availableCategories }: FilterBarProps) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 0)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const priceOptions = PRICE_RANGES.map(r => ({ value: r.value, label: r.label }))
  const brandOptions = availableBrands.map(b => ({ value: b.id, label: b.name }))
  const categoryOptions = availableCategories.map(c => ({ value: c.id, label: c.name }))

  const selectedPrice = filters.priceRange
    ? PRICE_RANGES.find(r => r.range[0] === filters.priceRange![0] && r.range[1] === filters.priceRange![1])?.value ?? null
    : null

  function handlePriceSelect(value: string | null) {
    const range = value ? PRICE_RANGES.find(r => r.value === value)?.range ?? null : null
    onFiltersChange({ ...filters, priceRange: range, page: 1 })
  }

  function handleBrandSelect(values: string[]) {
    onFiltersChange({ ...filters, brandIds: values, page: 1 })
  }

  function handleCategorySelect(values: string[]) {
    onFiltersChange({ ...filters, categoryIds: values, page: 1 })
  }

  function handleSortSelect(value: string | null) {
    onFiltersChange({ ...filters, sort: (value ?? 'best-sellers') as SortOption, page: 1 })
  }

  return (
    <div
      className="sticky top-[46px] z-30 bg-white flex items-center justify-between px-12 h-[46px] border-y border-sand"
      style={{ boxShadow: scrolled ? '0 1px 4px rgba(33,25,34,0.06)' : 'none' }}
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
          selected={null}
          onSelect={() => {}}
          multi
          selectedMulti={filters.brandIds}
          onSelectMulti={handleBrandSelect}
        />
        <FilterDropdown
          label="Category"
          options={categoryOptions}
          selected={null}
          onSelect={() => {}}
          multi
          selectedMulti={filters.categoryIds}
          onSelectMulti={handleCategorySelect}
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
