import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Pagination from '../components/Pagination'
import QuantitySelector from '../components/QuantitySelector'
import ReviewForm from '../components/ReviewForm'
import ReviewList from '../components/ReviewList'
import ReviewStats from '../components/ReviewStats'
import StarRating from '../components/StarRating'
import { ChevronLeftIcon, ChevronRightIcon, HeartFilledIcon, HeartIcon } from '../components/Icons'
import { useAuth } from '../hooks/useAuth'
import { addToCart } from '../services/cart'
import { addFavorite, removeFavorite } from '../services/favorite'
import { getProductDetail } from '../services/product'
import { getProductReviews } from '../services/review'
import type { ProductDetail, Review, ReviewBreakdown, ReviewPage } from '../types/product'

const REVIEWS_PAGE_SIZE = 5

const EMPTY_BREAKDOWN: ReviewBreakdown = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const { account, token } = useAuth()
  const user = account?.type === 'user' ? account : null
  const navigate = useNavigate()

  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [reviewPage, setReviewPage] = useState(1)
  const [reviewTotal, setReviewTotal] = useState(0)
  const [reviewFilter, setReviewFilter] = useState<number | null>(null)
  const [reviewBreakdown, setReviewBreakdown] = useState<ReviewBreakdown>(EMPTY_BREAKDOWN)
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [currentImage, setCurrentImage] = useState(0)
  const [quantity, setQuantity] = useState(1)
  const [favoriteBusy, setFavoriteBusy] = useState(false)
  const [cartBusy, setCartBusy] = useState(false)
  const [buyBusy, setBuyBusy] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return
    setLoading(true)
    setReviewPage(1)
    setReviewFilter(null)
    Promise.all([
      getProductDetail(productId, token),
      getProductReviews(productId, { page: 1, pageSize: REVIEWS_PAGE_SIZE }),
    ])
      .then(([p, rp]) => {
        setProduct(p)
        applyReviewPage(rp)
        setCurrentImage(0)
        setQuantity(1)
      })
      .catch(() => setProduct(null))
      .finally(() => setLoading(false))
  }, [productId, token])

  useEffect(() => {
    if (!productId || loading) return
    setReviewsLoading(true)
    getProductReviews(productId, {
      page: reviewPage,
      pageSize: REVIEWS_PAGE_SIZE,
      rating: reviewFilter,
    })
      .then(applyReviewPage)
      .catch(() => {})
      .finally(() => setReviewsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reviewPage, reviewFilter])

  function applyReviewPage(rp: ReviewPage) {
    setReviews(rp.reviews)
    setReviewTotal(rp.total)
    setReviewBreakdown(rp.breakdown)
  }

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 2400)
    return () => clearTimeout(t)
  }, [toast])

  if (loading) {
    return <div className="min-h-screen bg-fog px-12 py-16 text-sm text-olive">Loading...</div>
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-fog px-12 py-16">
        <p className="text-sm text-olive mb-4">Product not found.</p>
        <Link to="/list" className="text-sm underline text-brand-red">Back to products</Link>
      </div>
    )
  }

  const discountedPrice = product.discount > 0
    ? Math.round(product.price * (1 - product.discount / 100))
    : null
  const hasMultipleImages = product.images.length > 1

  function requireAuth(): boolean {
    if (!user || !token) {
      navigate('/login')
      return false
    }
    return true
  }

  function prevImage() {
    setCurrentImage(i => (i === 0 ? product!.images.length - 1 : i - 1))
  }

  function nextImage() {
    setCurrentImage(i => (i === product!.images.length - 1 ? 0 : i + 1))
  }

  async function toggleFavorite() {
    if (!requireAuth() || !product) return
    const wasFavorited = product.isFavorited
    setProduct({ ...product, isFavorited: !wasFavorited })
    setFavoriteBusy(true)
    try {
      if (wasFavorited) {
        await removeFavorite(token!, product.id)
        setToast('Removed from favorites')
      } else {
        await addFavorite(token!, product.id)
        setToast('Added to favorites')
      }
    } catch {
      setProduct(p => (p ? { ...p, isFavorited: wasFavorited } : p))
      setToast('Something went wrong')
    } finally {
      setFavoriteBusy(false)
    }
  }

  async function handleAddToCart() {
    if (!requireAuth() || !product) return
    setCartBusy(true)
    try {
      await addToCart(token!, { productId: product.id, quantity })
      setToast(`Added ${quantity} to cart`)
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Add to cart failed')
    } finally {
      setCartBusy(false)
    }
  }

  async function handleBuyNow() {
    if (!requireAuth() || !product) return
    setBuyBusy(true)
    try {
      const cartItem = await addToCart(token!, { productId: product.id, quantity })
      navigate('/checkout', { state: { selectedItemIds: [cartItem.id] } })
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Buy now failed')
      setBuyBusy(false)
    }
  }

  function handleReviewCreated(newReview: Review) {
    setProduct(p => {
      if (!p) return p
      const count = p.reviewCount + 1
      const prevSum = (p.averageRating ?? 0) * p.reviewCount
      const avg = (prevSum + newReview.rating) / count
      return { ...p, reviewCount: count, averageRating: avg }
    })
    setReviewBreakdown(b => ({ ...b, [newReview.rating as 1 | 2 | 3 | 4 | 5]: b[newReview.rating as 1 | 2 | 3 | 4 | 5] + 1 }))
    if (reviewFilter === null || reviewFilter === newReview.rating) {
      if (reviewPage === 1) {
        setReviews(prev => [newReview, ...prev].slice(0, REVIEWS_PAGE_SIZE))
        setReviewTotal(t => t + 1)
      } else {
        setReviewPage(1)
      }
    } else {
      setReviewTotal(t => t)
    }
    setToast('Review submitted')
  }

  function handleFilterChange(rating: number | null) {
    setReviewFilter(rating)
    setReviewPage(1)
  }

  const infoRows: { label: string; value: string }[] = [
    { label: 'Shipping', value: 'Free shipping on orders over 500,000 ₫' },
    { label: 'Returns', value: 'Free return within 15 days' },
    { label: 'Warranty', value: '12-month manufacturer warranty' },
    { label: 'Authenticity', value: '100% genuine, authorized seller' },
  ]

  return (
    <div className="min-h-screen bg-fog">
      <div className="max-w-[1100px] mx-auto px-12 py-8 space-y-6">
        {/* MAIN CARD — image + info */}
        <div className="bg-white rounded-pin-lg border border-sand p-8">
          <div className="flex gap-8 items-stretch">
            {/* Left — image carousel */}
            <div className="flex-1 min-w-0">
              <div className="relative aspect-square bg-fog rounded-pin-md overflow-hidden group">
                {product.images.length > 0 ? (
                  <img
                    src={product.images[currentImage]}
                    alt={product.name}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-sm text-olive">
                    No image
                  </div>
                )}

                {product.discount > 0 && (
                  <span className="absolute top-3 left-3 bg-brand-red text-white text-xs font-semibold px-2 py-1 rounded-pin-sm">
                    {product.discount}% OFF
                  </span>
                )}

                {hasMultipleImages && (
                  <>
                    <button
                      type="button"
                      onClick={prevImage}
                      className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-warm-light hover:bg-[color:var(--color-border-hover)] text-plum rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="Previous image"
                    >
                      <ChevronLeftIcon />
                    </button>
                    <button
                      type="button"
                      onClick={nextImage}
                      className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-warm-light hover:bg-[color:var(--color-border-hover)] text-plum rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="Next image"
                    >
                      <ChevronRightIcon />
                    </button>
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                      {product.images.map((_, idx) => (
                        <span
                          key={idx}
                          className={`w-1.5 h-1.5 rounded-full transition-colors ${
                            idx === currentImage ? 'bg-brand-red' : 'bg-white/70'
                          }`}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Right — product info, stretches to image height */}
            <div className="w-[380px] flex-shrink-0 flex flex-col self-stretch">
              {/* Title block */}
              <div>
                <h1 className="text-2xl font-semibold text-plum leading-snug tracking-[-0.3px]">{product.name}</h1>

                <div className="mt-2 flex items-center gap-3 flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-semibold text-brand-red underline">
                      {product.averageRating ? product.averageRating.toFixed(1) : '—'}
                    </span>
                    <StarRating value={product.averageRating ?? 0} />
                  </div>
                  <span className="text-xs text-olive">
                    {product.reviewCount} {product.reviewCount === 1 ? 'Rating' : 'Ratings'}
                  </span>
                  <span className="text-warm-silver">|</span>
                  <span className="text-xs text-olive">
                    {(product.reviewCount * 12 + 348).toLocaleString('en-US')} Sold
                  </span>
                </div>
              </div>

              {/* Price block — prominent */}
              <div className="mt-4 bg-[color:var(--color-warm-wash)] border border-sand rounded-pin-md px-5 py-4">
                {discountedPrice !== null ? (
                  <>
                    <div className="flex items-baseline gap-3 flex-wrap">
                      <span className="text-sm text-warm-silver line-through">
                        {product.price.toLocaleString('vi-VN')} &#8363;
                      </span>
                      <span className="text-xs font-semibold text-brand-red bg-white border border-brand-red rounded-pin-sm px-1.5 py-0.5">
                        -{product.discount}%
                      </span>
                    </div>
                    <div className="mt-1 text-[36px] leading-none font-bold text-brand-red tracking-[-0.5px]">
                      {discountedPrice.toLocaleString('vi-VN')} &#8363;
                    </div>
                  </>
                ) : (
                  <div className="text-[36px] leading-none font-bold text-brand-red tracking-[-0.5px]">
                    {product.price.toLocaleString('vi-VN')} &#8363;
                  </div>
                )}
              </div>

              {/* Info rows — fill height */}
              <div className="mt-4 flex-1 min-h-0 flex flex-col">
                <dl className="divide-y divide-[color:var(--color-sand)] border border-sand rounded-pin-md">
                  {(product.categoryName || product.brandName) && (
                    <div className="flex items-start gap-3 px-4 py-3">
                      <dt className="w-28 flex-shrink-0 text-xs text-olive">Category</dt>
                      <dd className="flex-1 text-xs text-plum">
                        {product.categoryName ?? '—'}
                        {product.brandName ? <> <span className="mx-1 text-warm-silver">•</span>{product.brandName}</> : null}
                      </dd>
                    </div>
                  )}
                  {infoRows.map(row => (
                    <div key={row.label} className="flex items-start gap-3 px-4 py-3">
                      <dt className="w-28 flex-shrink-0 text-xs text-olive">{row.label}</dt>
                      <dd className="flex-1 text-xs text-plum">{row.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              {/* Quantity + Buttons — anchored bottom */}
              <div className="mt-4">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-olive w-28 flex-shrink-0">Quantity</span>
                  <QuantitySelector value={quantity} onChange={setQuantity} />
                </div>

                <div className="flex gap-2 mt-4">
                  <button
                    type="button"
                    onClick={toggleFavorite}
                    disabled={favoriteBusy}
                    className={`w-12 h-[46px] rounded-pin flex items-center justify-center transition-colors ${
                      product.isFavorited
                        ? 'bg-warm-light text-brand-red hover:bg-[color:var(--color-border-hover)]'
                        : 'bg-warm-light text-plum hover:bg-[color:var(--color-border-hover)]'
                    }`}
                    aria-label={product.isFavorited ? 'Remove from favorites' : 'Add to favorites'}
                  >
                    {product.isFavorited ? <HeartFilledIcon /> : <HeartIcon />}
                  </button>
                  <button
                    type="button"
                    onClick={handleAddToCart}
                    disabled={cartBusy}
                    className="flex-1 h-[46px] border border-brand-red text-brand-red text-sm font-semibold rounded-pin bg-[color:var(--color-warm-wash)] hover:bg-white transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
                  >
                    {cartBusy ? 'Adding...' : 'Add to Cart'}
                  </button>
                  <button
                    type="button"
                    onClick={handleBuyNow}
                    disabled={buyBusy}
                    className="flex-1 h-[46px] bg-brand-red text-white text-sm font-semibold rounded-pin hover:bg-[var(--color-brand-red-hover)] transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[color:var(--color-focus-blue)] focus:ring-offset-2"
                  >
                    {buyBusy ? 'Processing...' : 'Buy Now'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* DESCRIPTION CARD */}
        <div className="bg-white rounded-pin-lg border border-sand p-8">
          <h2 className="text-xl font-semibold text-plum tracking-[-0.6px] mb-4">Product Description</h2>
          <p className="text-sm text-olive leading-relaxed whitespace-pre-line">
            {product.description ?? 'No description available.'}
          </p>
        </div>

        {/* REVIEWS CARD */}
        <div className="bg-white rounded-pin-lg border border-sand p-8">
          <h2 className="text-xl font-semibold text-plum tracking-[-0.6px] mb-4">Reviews</h2>

          <ReviewStats
            average={product.averageRating}
            count={product.reviewCount}
            breakdown={reviewBreakdown}
            selectedRating={reviewFilter}
            onSelect={handleFilterChange}
          />

          <div className="mt-6 mb-6">
            <ReviewForm productId={product.id} onCreated={handleReviewCreated} />
          </div>

          {reviewsLoading ? (
            <p className="text-sm text-olive py-6">Loading reviews...</p>
          ) : (
            <ReviewList reviews={reviews} />
          )}

          {reviewTotal > REVIEWS_PAGE_SIZE && (
            <div className="mt-6">
              <Pagination
                currentPage={reviewPage}
                totalPages={Math.max(1, Math.ceil(reviewTotal / REVIEWS_PAGE_SIZE))}
                onPageChange={setReviewPage}
              />
            </div>
          )}
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-[color:var(--color-dark-surface)] text-white text-sm px-5 py-2.5 rounded-pin shadow-lg">
          {toast}
        </div>
      )}
    </div>
  )
}
