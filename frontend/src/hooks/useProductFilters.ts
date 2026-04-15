import { useState, useMemo } from 'react'
import type { Product, Brand, Category, ProductFilters } from '../types/product'

const DEFAULT_FILTERS: ProductFilters = {
  priceRange: null,
  brandId: null,
  categoryId: null,
  sort: 'best-sellers',
}

export function useProductFilters(
  allProducts: Product[],
  brands: Brand[],
  categories: Category[],
) {
  const [filters, setFilters] = useState<ProductFilters>(DEFAULT_FILTERS)

  const filteredProducts = useMemo(() => {
    let result = [...allProducts]

    // Filter by price range
    if (filters.priceRange) {
      const [min, max] = filters.priceRange
      result = result.filter(p => p.price >= min && p.price <= max)
    }

    // Filter by brand (through categories)
    if (filters.brandId) {
      const brandCategoryIds = categories
        .filter(c => c.brandId === filters.brandId)
        .map(c => c.id)
      result = result.filter(p => brandCategoryIds.includes(p.categoryId))
    }

    // Filter by category
    if (filters.categoryId) {
      result = result.filter(p => p.categoryId === filters.categoryId)
    }

    // Sort
    switch (filters.sort) {
      case 'newest':
        result.reverse()
        break
      case 'price-high-low':
        result.sort((a, b) => b.price - a.price)
        break
      case 'price-low-high':
        result.sort((a, b) => a.price - b.price)
        break
      case 'discount-rate':
        result.sort((a, b) => b.discount - a.discount)
        break
      case 'best-sellers':
      default:
        break
    }

    return result
  }, [allProducts, categories, filters])

  return {
    filters,
    setFilters,
    filteredProducts,
    productCount: filteredProducts.length,
  }
}
