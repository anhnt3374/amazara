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

export type SortOption =
  | 'best-sellers'
  | 'newest'
  | 'price-high-low'
  | 'price-low-high'
  | 'discount-rate'

export interface ProductFilters {
  priceRange: [number, number] | null
  brandId: string | null
  categoryId: string | null
  sort: SortOption
}
