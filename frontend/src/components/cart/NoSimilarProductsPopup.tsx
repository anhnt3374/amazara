import { HelpCircleIcon, XIcon } from '../Icons'

interface NoSimilarProductsPopupProps {
  onClose: () => void
}

export default function NoSimilarProductsPopup({ onClose }: NoSimilarProductsPopupProps) {
  return (
    <div className="border-t border-sand bg-white rounded-b-pin-md px-6 py-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold text-plum">Other Sellers</span>
          <HelpCircleIcon className="w-4 h-4 text-warm-silver" />
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="w-7 h-7 rounded-full flex items-center justify-center text-olive hover:bg-fog hover:text-plum transition-colors"
        >
          <XIcon />
        </button>
      </div>
      <div className="mt-4 flex flex-col items-center justify-center gap-3 py-6">
        <EmptyShopIllustration />
        <p className="text-sm text-warm-silver">No other shops</p>
      </div>
    </div>
  )
}

function EmptyShopIllustration() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 96 96"
      fill="none"
      className="text-[color:var(--color-sand)]"
    >
      <path
        d="M20 36L28 22H68L76 36"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M22 36H74V70C74 72.2091 72.2091 74 70 74H26C23.7909 74 22 72.2091 22 70V36Z"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        d="M28 36V42C28 45.3137 30.6863 48 34 48C37.3137 48 40 45.3137 40 42V36M40 36V42C40 45.3137 42.6863 48 46 48C49.3137 48 52 45.3137 52 42V36M52 36V42C52 45.3137 54.6863 48 58 48C61.3137 48 64 45.3137 64 42V36"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <text
        x="48"
        y="65"
        textAnchor="middle"
        fontSize="18"
        fontWeight="600"
        fill="currentColor"
      >
        ?
      </text>
    </svg>
  )
}
