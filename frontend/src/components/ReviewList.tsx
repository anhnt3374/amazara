import type { Review } from '../types/product'
import StarRating from './StarRating'

interface ReviewListProps {
  reviews: Review[]
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return (
      <p className="text-sm text-olive py-6">No reviews yet. Be the first to write one.</p>
    )
  }

  return (
    <ul className="divide-y divide-[color:var(--color-sand)]">
      {reviews.map(r => (
        <li key={r.id} className="py-5">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-plum">{r.userFullname}</span>
            <span className="text-xs text-olive">{formatDate(r.createdAt)}</span>
          </div>
          <div className="mt-1">
            <StarRating value={r.rating} />
          </div>
          <p className="mt-2 text-sm text-olive leading-relaxed whitespace-pre-line">{r.content}</p>
        </li>
      ))}
    </ul>
  )
}
