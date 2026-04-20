import { formatVnd } from '../../utils/money'
import Checkbox from '../Checkbox'

interface CartBottomBarProps {
  totalItemCount: number
  selectedCount: number
  allSelected: boolean
  someSelected: boolean
  totalAmount: number
  onToggleAll: (next: boolean) => void
  onDeleteSelected: () => void
  onRemoveInactive: () => void
  onSaveToFavorites: () => void
  onBuy: () => void
}

export default function CartBottomBar({
  totalItemCount,
  selectedCount,
  allSelected,
  someSelected,
  totalAmount,
  onToggleAll,
  onDeleteSelected,
  onRemoveInactive,
  onSaveToFavorites,
  onBuy,
}: CartBottomBarProps) {
  const canAct = selectedCount > 0

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-sand shadow-[0_-6px_20px_rgba(33,25,34,0.06)]">
      <div className="max-w-[1400px] mx-auto h-16 pl-6 pr-[96px] flex items-center gap-5">
        <Checkbox
          checked={allSelected}
          indeterminate={someSelected && !allSelected}
          onChange={onToggleAll}
          label={<span className="text-sm text-plum">Select All ({totalItemCount})</span>}
          ariaLabel="Select all cart items"
        />

        <button
          type="button"
          onClick={onDeleteSelected}
          disabled={!canAct}
          className="text-sm text-plum hover:text-brand-red transition-colors disabled:text-warm-silver disabled:cursor-not-allowed"
        >
          Delete
        </button>

        <button
          type="button"
          onClick={onRemoveInactive}
          className="text-sm text-plum hover:text-brand-red transition-colors"
        >
          Remove Inactive Products
        </button>

        <button
          type="button"
          onClick={onSaveToFavorites}
          disabled={!canAct}
          className="text-sm text-brand-red hover:text-[color:var(--color-brand-red-hover)] transition-colors disabled:text-warm-silver disabled:cursor-not-allowed"
        >
          Save to Favorites
        </button>

        <div className="ml-auto flex items-center gap-4">
          <span className="text-sm text-plum">
            Total ({selectedCount} items):{' '}
            <span className="text-brand-red font-semibold text-base">
              {formatVnd(totalAmount)}
            </span>
          </span>
          <button
            type="button"
            onClick={onBuy}
            disabled={!canAct}
            className="h-11 px-8 rounded-pin bg-brand-red text-white text-sm font-semibold hover:bg-[var(--color-brand-red-hover)] transition-colors disabled:bg-sand disabled:text-warm-silver disabled:cursor-not-allowed"
          >
            Buy Now
          </button>
        </div>
      </div>
    </div>
  )
}
