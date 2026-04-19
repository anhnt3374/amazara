import type { Review, ReviewBreakdown, ReviewPage } from '../types/product'
import { ApiError } from './auth'

const API_BASE = '/api/v1'

function mapReview(r: Record<string, unknown>): Review {
  return {
    id: r.id as string,
    userFullname: r.user_fullname as string,
    rating: r.rating as number,
    content: r.content as string,
    createdAt: r.created_at as string,
  }
}

export interface GetReviewsParams {
  page?: number
  pageSize?: number
  rating?: number | null
}

export async function getProductReviews(
  productId: string,
  params: GetReviewsParams = {},
): Promise<ReviewPage> {
  const url = new URL(`${API_BASE}/products/${productId}/reviews`, window.location.origin)
  url.searchParams.set('page', String(params.page ?? 1))
  url.searchParams.set('page_size', String(params.pageSize ?? 5))
  if (params.rating) url.searchParams.set('rating', String(params.rating))

  const res = await fetch(url.pathname + url.search)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to load reviews')
  }
  const data = await res.json()
  const b = data.breakdown as Record<string, number>
  const breakdown: ReviewBreakdown = {
    1: b.one ?? 0,
    2: b.two ?? 0,
    3: b.three ?? 0,
    4: b.four ?? 0,
    5: b.five ?? 0,
  }
  return {
    reviews: (data.reviews as Record<string, unknown>[]).map(mapReview),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    overallCount: data.overall_count,
    overallAverage: data.overall_average ?? null,
    breakdown,
  }
}

export interface CreateReviewPayload {
  productId: string
  rating: number
  content: string
}

export async function createReview(token: string, payload: CreateReviewPayload): Promise<Review> {
  const res = await fetch(`${API_BASE}/reviews`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      product_id: payload.productId,
      rating: payload.rating,
      content: payload.content,
    }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new ApiError(res.status, data.detail ?? 'Failed to submit review')
  }
  return mapReview(await res.json())
}
