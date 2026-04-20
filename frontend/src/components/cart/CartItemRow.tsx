import { Link } from 'react-router-dom'
import type { EnrichedCartItem } from '../../types/cart'
import { formatVnd, priceAfterDiscount } from '../../utils/money'
import Checkbox from '../Checkbox'
import QuantitySelector from '../QuantitySelector'
import { ChevronDownIcon } from '../Icons'

interface CartItemRowProps {
  item: EnrichedCartItem
  selected: boolean
  onToggleSelected: () => void
  onQuantityChange: (next: number) => void
  onDelete: () => void
  onToggleSimilar: () => void
  similarOpen: boolean
}

export default function CartItemRow({
  item,
  selected,
  onToggleSelected,
  onQuantityChange,
  onDelete,
  onToggleSimilar,
  similarOpen,
}: CartItemRowProps) {
  const { product } = item
  const unit = priceAfterDiscount(product.price, product.discount)
  const subtotal = unit * item.quantity
  const cover = product.images[0] ?? ''

  return (
    <div className="grid grid-cols-[32px_minmax(0,2.4fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-4 px-4 py-4 border-t border-sand">
      <div>
        <Checkbox checked={selected} onChange={onToggleSelected} ariaLabel="Select cart item" />
      </div>

      <div className="flex gap-3 min-w-0">
        <Link to={`/product/${product.id}`} className="shrink-0">
          <div className="w-20 h-20 rounded-pin bg-fog overflow-hidden border border-sand">
            {cover && (
              <img src={cover} alt={product.name} className="w-full h-full object-cover" />
            )}
          </div>
        </Link>
        <div className="flex flex-col min-w-0 gap-1">
          <Link
            to={`/product/${product.id}`}
            className="text-sm text-plum line-clamp-2 hover:text-brand-red transition-colors"
          >
            {product.name}
          </Link>
          {product.discount > 0 && (
            <span className="inline-flex items-center self-start bg-[color:var(--color-brand-red)] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-sm tracking-wide">
              VOUCHER
            </span>
          )}
          {product.categoryName && (
            <span className="text-xs text-olive">
              Category: {product.categoryName}
            </span>
          )}
        </div>
      </div>

      <div className="text-sm text-plum">
        {product.discount > 0 ? (
          <div className="flex flex-col">
            <span className="text-xs text-warm-silver line-through">
              {formatVnd(product.price)}
            </span>
            <span>{formatVnd(unit)}</span>
          </div>
        ) : (
          <span>{formatVnd(unit)}</span>
        )}
      </div>

      <div>
        <QuantitySelector value={item.quantity} onChange={onQuantityChange} />
      </div>

      <div className="text-sm font-semibold text-brand-red">
        {formatVnd(subtotal)}
      </div>

      <div className="flex flex-col items-start gap-1">
        <button
          type="button"
          onClick={onDelete}
          className="text-sm text-plum hover:text-brand-red transition-colors"
        >
          Delete
        </button>
        <button
          type="button"
          onClick={onToggleSimilar}
          className="text-sm text-brand-red inline-flex items-center gap-1 hover:text-[color:var(--color-brand-red-hover)] transition-colors"
        >
          Find similar products
          <ChevronDownIcon
            className={`transition-transform ${similarOpen ? 'rotate-180' : ''}`}
          />
        </button>
      </div>
    </div>
  )
}
