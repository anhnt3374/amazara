import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'
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

  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ top: number; right: number }>({ top: 0, right: 0 })
  const anchorRef = useRef<HTMLDivElement>(null)
  const closeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function handleEnter() {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current)
      closeTimeoutRef.current = null
    }
    if (anchorRef.current) {
      const rect = anchorRef.current.getBoundingClientRect()
      setPos({ top: rect.bottom + 4, right: window.innerWidth - rect.right })
    }
    setOpen(true)
  }

  function handleLeave() {
    closeTimeoutRef.current = setTimeout(() => setOpen(false), 80)
  }

  return (
    <div
      ref={anchorRef}
      className="relative"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      <Link
        to={primary.to}
        className="block text-xs font-medium text-plum hover:underline max-w-[140px] truncate"
      >
        {account.displayName}
      </Link>
      {open && createPortal(
        <div
          className="fixed z-[60]"
          style={{ top: pos.top, right: pos.right }}
          onMouseEnter={handleEnter}
          onMouseLeave={handleLeave}
        >
          <div className="w-[120px] overflow-hidden bg-white border border-sand rounded-md shadow-[0_12px_24px_rgba(33,25,34,0.12)] py-1 px-1">
            <Link
              to={primary.to}
              className="block px-2 py-1.5 text-xs text-plum rounded-sm hover:bg-fog transition-colors"
              onClick={() => setOpen(false)}
            >
              {primary.label}
            </Link>
            <button
              type="button"
              onClick={() => { setOpen(false); onSignOut() }}
              className="w-full text-left px-2 py-1.5 text-xs text-plum rounded-sm hover:bg-fog transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
