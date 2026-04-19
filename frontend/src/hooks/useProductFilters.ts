import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { Product, Brand, Category, ProductFilters, SortOption } from '../types/product'
import { searchProducts } from '../services/product'

export function useProductFilters() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [availableBrands, setAvailableBrands] = useState<Brand[]>([])
  const [availableCategories, setAvailableCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)

  const filters: ProductFilters = useMemo(() => ({
    search: searchParams.get('search') ?? '',
    priceRange: null,
    brandIds: searchParams.getAll('brand_ids'),
    categoryIds: searchParams.getAll('category_ids'),
    sort: (searchParams.get('sort') ?? 'best-sellers') as SortOption,
    page: Number(searchParams.get('page') ?? 1),
  }), [searchParams])

  const paramsKey = searchParams.toString()

  useEffect(() => {
    setLoading(true)
    searchProducts({
      search: filters.search || undefined,
      brandIds: filters.brandIds.length ? filters.brandIds : undefined,
      categoryIds: filters.categoryIds.length ? filters.categoryIds : undefined,
      page: filters.page,
      sort: filters.sort,
    })
      .then(data => {
        setProducts(data.products)
        setTotal(data.total)
        setAvailableBrands(data.availableBrands)
        setAvailableCategories(data.availableCategories)
      })
      .catch(() => {
        setProducts([])
        setTotal(0)
      })
      .finally(() => setLoading(false))
  }, [paramsKey])

  function setFilters(next: ProductFilters) {
    const params = new URLSearchParams()
    if (next.search) params.set('search', next.search)
    next.brandIds.forEach(id => params.append('brand_ids', id))
    next.categoryIds.forEach(id => params.append('category_ids', id))
    if (next.sort !== 'best-sellers') params.set('sort', next.sort)
    if (next.page > 1) params.set('page', String(next.page))
    setSearchParams(params, { replace: true })
  }

  return {
    filters,
    setFilters,
    products,
    total,
    availableBrands,
    availableCategories,
    loading,
  }
}
