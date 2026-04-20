import type { Brand, Category, Product, ProductDetail, SortOption } from '../types/product'

export function mapProduct(p: Record<string, unknown>): Product {
  return {
    id: p.id as string,
    name: p.name as string,
    description: p.description as string | null,
    price: p.price as number,
    discount: p.discount as number,
    images: p.image ? (p.image as string).split('|').map(s => s.trim()).filter(Boolean) : [],
    categoryId: p.category_id as string,
    stock: (p.stock as number) ?? 0,
    isFavorited: Boolean(p.is_favorited),
  }
}

function mapProductDetail(p: Record<string, unknown>): ProductDetail {
  return {
    ...mapProduct(p),
    categoryName: (p.category_name as string | null) ?? null,
    brandName: (p.brand_name as string | null) ?? null,
    reviewCount: (p.review_count as number) ?? 0,
    averageRating: (p.average_rating as number | null) ?? null,
  }
}
import { ApiError } from './auth'

const API_BASE = '/api/v1'

export interface ProductSearchParams {
  search?: string
  brandIds?: string[]
  categoryIds?: string[]
  page?: number
  sort?: SortOption
}

export interface ProductSearchResponse {
  products: Product[]
  total: number
  page: number
  pageSize: number
  availableBrands: Brand[]
  availableCategories: Category[]
}

export async function searchProducts(
  params: ProductSearchParams,
  token?: string | null,
): Promise<ProductSearchResponse> {
  const url = new URL(`${API_BASE}/products/search`, window.location.origin)
  if (params.search) url.searchParams.set('search', params.search)
  if (params.brandIds?.length) {
    params.brandIds.forEach(id => url.searchParams.append('brand_ids', id))
  }
  if (params.categoryIds?.length) {
    params.categoryIds.forEach(id => url.searchParams.append('category_ids', id))
  }
  if (params.page) url.searchParams.set('page', String(params.page))
  if (params.sort) url.searchParams.set('sort', params.sort)

  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(url.pathname + url.search, { headers })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Search failed')
  }

  const data = await res.json()
  return {
    products: data.products.map(mapProduct),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    availableBrands: data.available_brands,
    availableCategories: data.available_categories.map((c: Record<string, unknown>) => ({
      id: c.id,
      name: c.name,
      brandId: c.brand_id,
    })),
  }
}

export async function getProduct(productId: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/products/${productId}`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Product not found')
  }
  const data = await res.json()
  return mapProduct(data)
}

export interface SimilarProductsResponse {
  products: Product[]
  total: number
  page: number
  pageSize: number
}

export async function getSimilarProducts(
  productId: string,
  page: number,
  token?: string | null,
): Promise<SimilarProductsResponse> {
  const url = new URL(`${API_BASE}/products/${productId}/similar`, window.location.origin)
  url.searchParams.set('page', String(page))
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(url.pathname + url.search, { headers })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load similar products')
  }
  const data = await res.json()
  return {
    products: data.products.map(mapProduct),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  }
}

export async function getProductDetail(productId: string, token?: string | null): Promise<ProductDetail> {
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${API_BASE}/products/${productId}`, { headers })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Product not found')
  }
  const data = await res.json()
  return mapProductDetail(data)
}
