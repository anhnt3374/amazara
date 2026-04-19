import { Fragment } from 'react'
import type { EnrichedCartItem, CartStoreMini } from '../../types/cart'
import type { Product } from '../../types/product'
import Checkbox from '../Checkbox'
import { ChatBubbleIcon } from '../Icons'
import CartItemRow from './CartItemRow'
import SimilarProductsPanel from './SimilarProductsPanel'
import NoSimilarProductsPopup from './NoSimilarProductsPopup'

export type ShopSelectionState = 'all' | 'some' | 'none'

export interface SimilarState {
  status: 'loading' | 'loaded'
  total: number
  pageSize: number
  products: Product[]
}

interface CartShopGroupProps {
  store: CartStoreMini
  items: EnrichedCartItem[]
  selected: Set<string>
  selectionState: ShopSelectionState
  onToggleShop: (next: boolean) => void
  onToggleItem: (id: string) => void
  onQuantityChange: (id: string, next: number) => void
  onDelete: (id: string) => void
  onToggleSimilar: (item: EnrichedCartItem) => void
  onCloseSimilar: () => void
  openSimilarFor: string | null
  similarState: SimilarState | null
}

export default function CartShopGroup({
  store,
  items,
  selected,
  selectionState,
  onToggleShop,
  onToggleItem,
  onQuantityChange,
  onDelete,
  onToggleSimilar,
  onCloseSimilar,
  openSimilarFor,
  similarState,
}: CartShopGroupProps) {
  return (
    <section className="bg-white rounded-pin-md border border-sand overflow-hidden">
      {/* Shop header */}
      <div className="grid grid-cols-[32px_1fr] items-center gap-4 px-4 py-3">
        <Checkbox
          checked={selectionState === 'all'}
          indeterminate={selectionState === 'some'}
          onChange={onToggleShop}
          ariaLabel={`Select all items from ${store.name}`}
        />
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center bg-brand-red text-white text-xs font-semibold px-2 py-0.5 rounded-pin-sm">
            Favorite
          </span>
          <span className="text-sm font-semibold text-plum truncate">{store.name}</span>
          <button
            type="button"
            className="inline-flex items-center justify-center w-7 h-7 rounded-full text-brand-red hover:bg-fog transition-colors"
            aria-label={`Chat with ${store.name}`}
          >
            <ChatBubbleIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {items.map(item => {
        const isOpen = openSimilarFor === item.id
        return (
          <Fragment key={item.id}>
            <CartItemRow
              item={item}
              selected={selected.has(item.id)}
              onToggleSelected={() => onToggleItem(item.id)}
              onQuantityChange={next => onQuantityChange(item.id, next)}
              onDelete={() => onDelete(item.id)}
              onToggleSimilar={() => onToggleSimilar(item)}
              similarOpen={isOpen}
            />
            {isOpen && similarState && similarState.status === 'loaded' && (
              similarState.total === 0 ? (
                <NoSimilarProductsPopup onClose={onCloseSimilar} />
              ) : (
                <SimilarProductsPanel
                  productId={item.productId}
                  initialProducts={similarState.products}
                  initialTotal={similarState.total}
                  initialPageSize={similarState.pageSize}
                />
              )
            )}
            {isOpen && similarState && similarState.status === 'loading' && (
              <div className="border-t border-sand bg-white px-4 py-6 text-sm text-olive text-center">
                Loading similar products...
              </div>
            )}
          </Fragment>
        )
      })}
    </section>
  )
}
