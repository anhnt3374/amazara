import { Link } from 'react-router-dom'
import type { Account } from '../services/auth'

interface AccountMenuProps {
  account: Account
  onSignOut: () => void
}

export default function AccountMenu({ account, onSignOut }: AccountMenuProps) {
  const primary =
    account.type === 'store'
      ? { label: 'Manage Products', to: '/store/products' }
      : { label: 'View Orders', to: '/orders' }

  return (
    <div className="relative group">
      <button
        type="button"
        className="font-medium text-plum hover:underline max-w-[160px] truncate"
      >
        {account.displayName}
      </button>
      <div className="absolute right-0 top-full pt-1 hidden group-hover:block z-50">
        <div className="min-w-[180px] bg-white border border-sand rounded-pin-md shadow-[0_12px_24px_rgba(33,25,34,0.12)] py-1">
          <Link
            to={primary.to}
            className="block px-4 py-2 text-sm text-plum hover:bg-fog transition-colors"
          >
            {primary.label}
          </Link>
          <button
            type="button"
            onClick={onSignOut}
            className="w-full text-left px-4 py-2 text-sm text-plum hover:bg-fog transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}
