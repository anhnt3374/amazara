import { StarIcon } from './Icons'

interface StarRatingProps {
  value: number
  onChange?: (value: number) => void
  size?: number
}

export default function StarRating({ value, onChange, size = 18 }: StarRatingProps) {
  const interactive = typeof onChange === 'function'
  const stars = [1, 2, 3, 4, 5]

  return (
    <div className="inline-flex items-center gap-0.5">
      {stars.map(n => {
        const filled = n <= Math.round(value)
        const colorClass = filled ? 'text-brand-red' : 'text-sand'
        if (interactive) {
          return (
            <button
              key={n}
              type="button"
              onClick={() => onChange?.(n)}
              className={`p-0.5 hover:scale-110 transition-transform ${colorClass} hover:text-brand-red`}
              aria-label={`Rate ${n} star${n === 1 ? '' : 's'}`}
            >
              <StarIcon filled={filled} className={`w-[${size}px] h-[${size}px]`} />
            </button>
          )
        }
        return <StarIcon key={n} filled={filled} className={colorClass} />
      })}
    </div>
  )
}
