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
}

export default function FilterDropdown({ label, options, selected, onSelect, align = 'left' }: FilterDropdownProps) {
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

  const selectedLabel = options.find(o => o.value === selected)?.label

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(prev => !prev)}
        className={clsx(
          'flex items-center gap-1 px-3.5 py-1 text-xs border rounded-full transition-colors',
          open || selected
            ? 'border-[#111] text-[#111]'
            : 'border-[#e5e5e5] text-[#111] hover:border-[#111]'
        )}
      >
        <span>{selectedLabel ?? label}</span>
        <ChevronDownIcon className={clsx('transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div
          className={clsx(
            'absolute top-full mt-1.5 bg-white border border-[#e5e5e5] rounded-lg shadow-lg py-1.5 min-w-[180px] z-20',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {selected && (
            <button
              onClick={() => { onSelect(null); setOpen(false) }}
              className="w-full text-left px-3 py-1.5 text-xs text-[#757575] hover:bg-[#f5f5f5]"
            >
              Clear
            </button>
          )}
          {options.map(option => (
            <button
              key={option.value}
              onClick={() => { onSelect(option.value); setOpen(false) }}
              className={clsx(
                'w-full text-left px-3 py-1.5 text-xs hover:bg-[#f5f5f5]',
                selected === option.value ? 'font-semibold text-[#111]' : 'text-[#111]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
