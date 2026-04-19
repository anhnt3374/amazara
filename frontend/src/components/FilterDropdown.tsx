import { useState, useRef, useEffect } from 'react'
import clsx from 'clsx'
import { ChevronDownIcon } from './Icons'

interface Option {
  value: string
  label: string
}

interface FilterDropdownProps {
  label: string
  options: Option[]
  selected: string | null
  onSelect: (value: string | null) => void
  align?: 'left' | 'right'
  multi?: boolean
  selectedMulti?: string[]
  onSelectMulti?: (values: string[]) => void
}

export default function FilterDropdown({
  label, options, selected, onSelect, align = 'left',
  multi, selectedMulti = [], onSelectMulti,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const hasSelection = multi ? selectedMulti.length > 0 : selected !== null
  const triggerLabel = multi && selectedMulti.length > 0
    ? `${label} (${selectedMulti.length})`
    : multi
      ? label
      : options.find(o => o.value === selected)?.label ?? label

  function handleMultiToggle(value: string) {
    if (!onSelectMulti) return
    const next = selectedMulti.includes(value)
      ? selectedMulti.filter(v => v !== value)
      : [...selectedMulti, value]
    onSelectMulti(next)
  }

  function handleClear() {
    if (multi) {
      onSelectMulti?.([])
    } else {
      onSelect(null)
    }
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(prev => !prev)}
        className={clsx(
          'flex items-center gap-1 px-3.5 py-1 text-xs border rounded-pin transition-colors',
          open || hasSelection
            ? 'border-brand-red text-brand-red bg-white'
            : 'border-sand text-plum hover:border-plum bg-white'
        )}
      >
        <span>{triggerLabel}</span>
        <ChevronDownIcon className={clsx('transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div
          className={clsx(
            'absolute top-full mt-1.5 bg-white border border-sand rounded-pin-md shadow-lg min-w-[180px] z-20 overflow-hidden',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {hasSelection && (
            <button
              onClick={handleClear}
              className="w-full text-left px-3 py-1.5 text-xs text-olive hover:bg-fog border-b border-sand"
            >
              Clear
            </button>
          )}
          <div className="max-h-[260px] overflow-y-auto py-1.5">
          {options.map(option => {
            if (multi) {
              const checked = selectedMulti.includes(option.value)
              return (
                <button
                  key={option.value}
                  onClick={() => handleMultiToggle(option.value)}
                  className="w-full text-left px-3 py-1.5 text-xs hover:bg-fog flex items-center gap-2"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    readOnly
                    className="accent-[color:var(--color-brand-red)] pointer-events-none"
                  />
                  <span className={checked ? 'font-semibold text-brand-red' : 'text-plum'}>
                    {option.label}
                  </span>
                </button>
              )
            }
            return (
              <button
                key={option.value}
                onClick={() => { onSelect(option.value); setOpen(false) }}
                className={clsx(
                  'w-full text-left px-3 py-1.5 text-xs hover:bg-fog',
                  selected === option.value ? 'font-semibold text-brand-red' : 'text-plum'
                )}
              >
                {option.label}
              </button>
            )
          })}
          </div>
        </div>
      )}
    </div>
  )
}
