interface QuantitySelectorProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
}

export default function QuantitySelector({ value, onChange, min = 1, max = 99 }: QuantitySelectorProps) {
  const dec = () => onChange(Math.max(min, value - 1))
  const inc = () => onChange(Math.min(max, value + 1))

  return (
    <div className="inline-flex items-center border border-sand rounded-pin overflow-hidden bg-white">
      <button
        type="button"
        onClick={dec}
        disabled={value <= min}
        className="w-10 h-10 flex items-center justify-center text-lg text-plum hover:bg-fog disabled:text-warm-silver disabled:hover:bg-transparent transition-colors"
        aria-label="Decrease quantity"
      >
        −
      </button>
      <span className="w-10 text-center text-sm font-medium text-plum select-none">{value}</span>
      <button
        type="button"
        onClick={inc}
        disabled={value >= max}
        className="w-10 h-10 flex items-center justify-center text-lg text-plum hover:bg-fog disabled:text-warm-silver disabled:hover:bg-transparent transition-colors"
        aria-label="Increase quantity"
      >
        +
      </button>
    </div>
  )
}
