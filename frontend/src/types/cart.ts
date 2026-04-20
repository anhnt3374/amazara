export interface CartStoreMini {
  id: string
  name: string
  slug: string | null
  avatarUrl: string | null
}

export interface CartProductMini {
  id: string
  name: string
  price: number
  discount: number
  images: string[]
  stock: number
  categoryId: string | null
  storeId: string
  categoryName: string | null
}

export interface EnrichedCartItem {
  id: string
  productId: string
  quantity: number
  notes: string | null
  product: CartProductMini
  store: CartStoreMini
}

export interface CartListResponse {
  items: EnrichedCartItem[]
  totalCount: number
}
