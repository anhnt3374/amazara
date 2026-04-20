import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../contexts/ChatContext'
import { addToCart } from '../services/cart'
import { listOrders } from '../services/order'
import type { Order, OrderItem, OrderStatus } from '../types/order'
import { formatVnd } from '../utils/money'

type TabKey = 'all' | OrderStatus

interface TabDef {
  key: TabKey
  label: string
}

const TABS: TabDef[] = [
  { key: 'all', label: 'All' },
  { key: 'shipping', label: 'Shipping' },
  { key: 'awaiting_delivery', label: 'Awaiting Delivery' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
  { key: 'returning', label: 'Return/Refund' },
]

const STATUS_LABEL: Record<OrderStatus, string> = {
  shipping: 'SHIPPING',
  awaiting_delivery: 'AWAITING DELIVERY',
  completed: 'COMPLETED',
  cancelled: 'CANCELLED',
  returning: 'RETURN/REFUND',
}

type ShopBucket = {
  storeId: string
  storeName: string
  storeAvatar: string | null
  items: OrderItem[]
  subtotal: number
}

function bucketItemsByStore(order: Order): ShopBucket[] {
  const map = new Map<string, ShopBucket>()
  for (const item of order.orderItems) {
    const sid = item.store?.id ?? 'unknown'
    const sname = item.store?.name ?? 'Unknown Store'
    const avatar = item.store?.avatarUrl ?? null
    const existing = map.get(sid)
    const lineTotal = item.price * item.quantity
    if (existing) {
      existing.items.push(item)
      existing.subtotal += lineTotal
    } else {
      map.set(sid, {
        storeId: sid,
        storeName: sname,
        storeAvatar: avatar,
        items: [item],
        subtotal: lineTotal,
      })
    }
  }
  return [...map.values()]
}

export default function Orders() {
  const { token } = useAuth()
  const chat = useChat()
  const navigate = useNavigate()
  const [contactingKey, setContactingKey] = useState<string | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: TabKey = (searchParams.get('tab') as TabKey) ?? 'all'
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (!toast) return
    const h = setTimeout(() => setToast(null), 2400)
    return () => clearTimeout(h)
  }, [toast])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    setLoading(true)
    const statusFilter = activeTab === 'all' ? undefined : activeTab
    listOrders(token, statusFilter)
      .then(data => {
        if (!cancelled) {
          setOrders(data)
          setError(null)
        }
      })
      .catch(err => {
        if (!cancelled) setError(err?.message ?? 'Failed to load orders')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, activeTab])

  const setTab = useCallback(
    (key: TabKey) => {
      if (key === 'all') {
        searchParams.delete('tab')
      } else {
        searchParams.set('tab', key)
      }
      setSearchParams(searchParams, { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const filteredOrders = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return orders
    return orders.filter(o => {
      if (o.id.toLowerCase().includes(q)) return true
      return o.orderItems.some(
        it =>
          it.productName.toLowerCase().includes(q) ||
          (it.store?.name ?? '').toLowerCase().includes(q),
      )
    })
  }, [orders, query])

  const contactSeller = useCallback(
    async (order: Order, bucket: ShopBucket) => {
      if (!token || !bucket.storeId || bucket.storeId === 'unknown') {
        setToast('Seller unavailable')
        return
      }
      const key = `${order.id}-${bucket.storeId}`
      setContactingKey(key)
      try {
        const conv = await chat.openWithStore(bucket.storeId)
        const shortId = order.id.slice(0, 8).toUpperCase()
        await chat.sendMessage(conv.id, {
          content: `Hi, I have a question about order #${shortId}.`,
          ref_type: 'order',
          ref_id: order.id,
        })
        navigate(`/messages/${conv.id}`)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to open chat'
        setToast(msg)
      } finally {
        setContactingKey(null)
      }
    },
    [chat, navigate, token],
  )

  const buyAgain = useCallback(
    async (order: Order) => {
      if (!token) return
      try {
        for (const item of order.orderItems) {
          await addToCart(token, {
            productId: item.productId,
            quantity: item.quantity,
            notes: item.notes,
          })
        }
        navigate('/cart')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to re-buy'
        setToast(msg)
      }
    },
    [token, navigate],
  )

  return (
    <div className="bg-fog min-h-[calc(100vh-64px)]">
      <div className="max-w-[1200px] mx-auto px-6 py-6 flex flex-col gap-3">
        {/* Tabs */}
        <div className="bg-white rounded-pin-md border border-sand overflow-hidden">
          <div className="grid grid-cols-6 text-sm">
            {TABS.map(tab => {
              const active = activeTab === tab.key
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setTab(tab.key)}
                  className={`h-12 px-3 text-center transition-colors border-b-2 ${
                    active
                      ? 'text-brand-red border-brand-red font-semibold'
                      : 'text-plum border-transparent hover:text-brand-red'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Search */}
        <div className="bg-[color:var(--color-warm-light)] rounded-pin-md border border-sand px-4 h-12 flex items-center gap-3">
          <span aria-hidden="true" className="text-olive">🔍</span>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by shop name, order ID, or product name"
            className="flex-1 h-full bg-transparent text-sm text-plum placeholder:text-warm-silver focus:outline-none"
          />
        </div>

        {loading && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive">
            Loading orders...
          </div>
        )}

        {!loading && error && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-brand-red">
            {error}
          </div>
        )}

        {!loading && !error && filteredOrders.length === 0 && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive">
            No orders yet.
          </div>
        )}

        {!loading &&
          !error &&
          filteredOrders.flatMap(order => {
            const buckets = bucketItemsByStore(order)
            return buckets.map(bucket => (
              <div
                key={`${order.id}-${bucket.storeId}`}
                className="bg-white rounded-pin-md border border-sand overflow-hidden"
              >
                {/* Shop header */}
                <div className="flex items-center gap-3 px-6 py-3 border-b border-sand bg-fog/60">
                  <span className="text-[10px] font-bold text-white bg-brand-red px-1.5 py-0.5 rounded-sm">
                    Favorite
                  </span>
                  <span className="text-sm font-semibold text-plum">
                    {bucket.storeName.toUpperCase()}
                  </span>
                  <button
                    type="button"
                    onClick={() => contactSeller(order, bucket)}
                    disabled={contactingKey === `${order.id}-${bucket.storeId}`}
                    className="inline-flex items-center gap-1 h-7 px-2 text-xs text-white bg-brand-red rounded-sm hover:bg-[var(--color-brand-red-hover)] transition-colors disabled:opacity-60"
                  >
                    💬 Chat
                  </button>
                  <span
                    aria-disabled="true"
                    tabIndex={-1}
                    className="inline-flex items-center gap-1 h-7 px-2 text-xs text-plum border border-sand bg-white rounded-sm opacity-80 cursor-not-allowed select-none"
                    title="View Shop is not available yet"
                  >
                    🏬 View Shop
                  </span>
                  <div className="ml-auto flex items-center gap-4 text-sm">
                    <span className="text-[color:var(--color-brand-red)] inline-flex items-center gap-1">
                      🚚 Delivery in progress
                    </span>
                    <span className="text-brand-red font-semibold uppercase tracking-wide text-xs">
                      {STATUS_LABEL[order.status]}
                    </span>
                  </div>
                </div>

                {/* Items */}
                {bucket.items.map(item => {
                  const cover = item.productImages[0] ?? ''
                  return (
                    <div
                      key={item.id}
                      className="flex gap-4 px-6 py-4 border-b border-sand last:border-b-0"
                    >
                      <div className="w-20 h-20 rounded-pin bg-fog overflow-hidden border border-sand shrink-0">
                        {cover && (
                          <img
                            src={cover}
                            alt={item.productName}
                            className="w-full h-full object-cover"
                          />
                        )}
                      </div>
                      <div className="flex-1 min-w-0 flex flex-col gap-1">
                        <span className="text-sm text-plum line-clamp-2">
                          {item.productName}
                        </span>
                        {item.notes && (
                          <span className="text-xs text-olive">Variant: {item.notes}</span>
                        )}
                        <span className="text-xs text-olive">x{item.quantity}</span>
                      </div>
                      <div className="text-sm text-brand-red font-semibold whitespace-nowrap">
                        {formatVnd(item.price)}
                      </div>
                    </div>
                  )
                })}

                {/* Summary + actions */}
                <div className="px-6 py-4 flex flex-col gap-3 items-end bg-white">
                  <div className="text-sm text-plum">
                    Total:{' '}
                    <span className="text-brand-red font-semibold text-lg">
                      {formatVnd(bucket.subtotal)}
                    </span>
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => buyAgain(order)}
                      className="h-10 px-6 rounded-pin bg-brand-red text-white text-sm font-semibold hover:bg-[var(--color-brand-red-hover)] transition-colors"
                    >
                      Buy Again
                    </button>
                    <button
                      type="button"
                      onClick={() => contactSeller(order, bucket)}
                      disabled={contactingKey === `${order.id}-${bucket.storeId}`}
                      className="h-10 px-6 rounded-pin bg-white text-plum border border-sand text-sm font-semibold hover:border-[color:var(--color-border-hover)] transition-colors disabled:opacity-60"
                    >
                      {contactingKey === `${order.id}-${bucket.storeId}`
                        ? 'Opening...'
                        : 'Contact Seller'}
                    </button>
                  </div>
                </div>
              </div>
            ))
          })}
      </div>

      {toast && (
        <div
          role="status"
          className="fixed left-1/2 -translate-x-1/2 bottom-16 z-[60] bg-plum text-white text-sm px-4 py-2 rounded-pin shadow-[0_10px_30px_rgba(33,25,34,0.25)]"
        >
          {toast}
        </div>
      )}
    </div>
  )
}
