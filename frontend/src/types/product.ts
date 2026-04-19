export interface Brand {
  id: string
  name: string
}

export interface Category {
  id: string
  name: string
  brandId: string
}

export interface Product {
  id: string
  name: string
  description: string | null
  price: number
  discount: number
  images: string[]
  categoryId: string
}

export interface ProductDetail extends Product {
  categoryName: string | null
  brandName: string | null
  reviewCount: number
  averageRating: number | null
  isFavorited: boolean
}

export interface Review {
  id: string
  userFullname: string
  rating: number
  content: string
  createdAt: string
}

export type ReviewBreakdown = Record<1 | 2 | 3 | 4 | 5, number>

export interface ReviewPage {
  reviews: Review[]
  total: number
  page: number
  pageSize: number
  overallCount: number
  overallAverage: number | null
  breakdown: ReviewBreakdown
}

export type SortOption =
  | 'best-sellers'
  | 'newest'
  | 'price-high-low'
  | 'price-low-high'
  | 'discount-rate'

export interface ProductFilters {
  search: string
  priceRange: [number, number] | null
  brandIds: string[]
  categoryIds: string[]
  sort: SortOption
  page: number
}
