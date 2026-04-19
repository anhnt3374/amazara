import clsx from 'clsx'

interface CheckboxProps {
  checked: boolean
  indeterminate?: boolean
  onChange: (next: boolean) => void
  label?: React.ReactNode
  size?: 'sm' | 'md'
  disabled?: boolean
  ariaLabel?: string
}

export default function Checkbox({
  checked,
  indeterminate = false,
  onChange,
  label,
  size = 'md',
  disabled = false,
  ariaLabel,
}: CheckboxProps) {
  const box = size === 'sm' ? 'w-4 h-4' : 'w-[18px] h-[18px]'
  const active = checked || indeterminate

  return (
    <label
      className={clsx(
        'inline-flex items-center gap-2 select-none',
        disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
      )}
    >
      <span
        className={clsx(
          box,
          'rounded-pin-sm border flex items-center justify-center transition-colors',
          active
            ? 'bg-brand-red border-brand-red text-white'
            : 'bg-white border-sand hover:border-plum',
        )}
        aria-hidden
      >
        {checked && !indeterminate && (
          <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3">
            <path
              d="M3 8.5l3 3 7-7"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
        {indeterminate && (
          <span className="block w-2 h-[2px] bg-white rounded-full" />
        )}
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        disabled={disabled}
        aria-label={ariaLabel}
        className="sr-only"
      />
      {label && <span className="text-sm text-plum">{label}</span>}
    </label>
  )
}
