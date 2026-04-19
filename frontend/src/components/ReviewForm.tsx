import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { createReview } from '../services/review'
import type { Review } from '../types/product'
import StarRating from './StarRating'

interface ReviewFormProps {
  productId: string
  onCreated: (review: Review) => void
}

export default function ReviewForm({ productId, onCreated }: ReviewFormProps) {
  const { user, token } = useAuth()
  const [rating, setRating] = useState(5)
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!user || !token) {
    return (
      <div className="bg-fog text-olive text-sm rounded-pin-md px-5 py-4">
        <Link to="/login" className="underline text-brand-red font-medium">Log in</Link> to write a review.
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!content.trim()) {
      setError('Please write your review first.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const review = await createReview(token!, { productId, rating, content: content.trim() })
      onCreated(review)
      setContent('')
      setRating(5)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-sand rounded-pin-md p-5 space-y-3 bg-white">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-plum">Your rating:</span>
        <StarRating value={rating} onChange={setRating} />
      </div>
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="Share your thoughts about this product..."
        rows={3}
        className="w-full text-sm text-plum bg-white border border-warm-silver rounded-pin px-[15px] py-[11px] focus:outline-none focus:border-[color:var(--color-focus-blue)] focus:ring-2 focus:ring-[color:var(--color-focus-blue)]/30 placeholder:text-warm-silver resize-none"
      />
      {error && <p className="text-sm text-[color:var(--color-error-red)]">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="h-11 px-5 bg-brand-red text-white text-sm font-medium rounded-pin hover:bg-[var(--color-brand-red-hover)] transition-colors disabled:bg-warm-silver focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
      >
        {submitting ? 'Submitting...' : 'Submit review'}
      </button>
    </form>
  )
}
