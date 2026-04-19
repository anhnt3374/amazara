import clsx from 'clsx'
import type { ReviewBreakdown } from '../types/product'
import StarRating from './StarRating'

interface ReviewStatsProps {
  average: number | null
  count: number
  breakdown: ReviewBreakdown
  selectedRating: number | null
  onSelect: (rating: number | null) => void
}

function formatCount(n: number): string {
  if (n >= 1000) {
    const k = n / 1000
    return `${k.toFixed(k >= 10 ? 0 : 1).replace(/\.0$/, '')}k`
  }
  return String(n)
}

export default function ReviewStats({
  average,
  count,
  breakdown,
  selectedRating,
  onSelect,
}: ReviewStatsProps) {
  const pills: { label: string; rating: number | null; count: number }[] = [
    { label: 'All', rating: null, count },
    { label: '5 Stars', rating: 5, count: breakdown[5] },
    { label: '4 Stars', rating: 4, count: breakdown[4] },
    { label: '3 Stars', rating: 3, count: breakdown[3] },
    { label: '2 Stars', rating: 2, count: breakdown[2] },
    { label: '1 Star', rating: 1, count: breakdown[1] },
  ]

  return (
    <div className="bg-[color:var(--color-warm-wash)] border border-sand rounded-pin-md px-6 py-5 flex items-center gap-8">
      <div className="flex-shrink-0 text-center">
        <div className="flex items-baseline justify-center gap-1 text-brand-red">
          <span className="text-3xl font-semibold">
            {average !== null ? average.toFixed(1) : '—'}
          </span>
          <span className="text-sm">out of 5</span>
        </div>
        <div className="mt-1">
          <StarRating value={average ?? 0} />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {pills.map(p => {
          const active =
            (p.rating === null && selectedRating === null) || p.rating === selectedRating
          return (
            <button
              key={p.label}
              type="button"
              onClick={() => onSelect(p.rating)}
              className={clsx(
                'px-4 h-9 rounded-pin border text-sm transition-colors bg-white',
                active
                  ? 'border-brand-red text-brand-red'
                  : 'border-sand text-plum hover:border-plum',
              )}
            >
              {p.label}
              {p.count > 0 && (
                <span className="ml-1 text-olive">({formatCount(p.count)})</span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
