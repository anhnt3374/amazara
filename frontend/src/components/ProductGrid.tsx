import type { Product } from '../types/product'
import ProductCard from './ProductCard'

interface ProductGridProps {
  products: Product[]
  onToggleFavorite?: (productId: string, next: boolean) => void
}

export default function ProductGrid({ products, onToggleFavorite }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-olive text-sm">
        No products found.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 px-12">
      {products.map(product => (
        <ProductCard
          key={product.id}
          product={product}
          onToggleFavorite={onToggleFavorite}
        />
      ))}
    </div>
  )
}
