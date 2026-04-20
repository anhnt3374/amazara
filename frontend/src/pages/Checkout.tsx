import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { listAddresses } from '../services/address'
import { listCart } from '../services/cart'
import { createOrder } from '../services/order'
import type { Address } from '../types/address'
import type { EnrichedCartItem } from '../types/cart'
import { formatVnd, priceAfterDiscount } from '../utils/money'

const SHIPPING_FEE_VND = 63800

type ShopGroup = {
  storeId: string
  store: EnrichedCartItem['store']
  items: EnrichedCartItem[]
}

function groupByShop(items: EnrichedCartItem[]): ShopGroup[] {
  const map = new Map<string, ShopGroup>()
  for (const item of items) {
    const existing = map.get(item.store.id)
    if (existing) {
      existing.items.push(item)
    } else {
      map.set(item.store.id, {
        storeId: item.store.id,
        store: item.store,
        items: [item],
      })
    }
  }
  return [...map.values()]
}

interface LocationState {
  selectedItemIds?: string[]
}

export default function Checkout() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const selectedIds = useMemo(
    () => (location.state as LocationState | null)?.selectedItemIds ?? [],
    [location.state],
  )

  const [items, setItems] = useState<EnrichedCartItem[]>([])
  const [addresses, setAddresses] = useState<Address[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [note, setNote] = useState('')
  const [placing, setPlacing] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    document.body.style.setProperty('--bottom-bar-offset', '80px')
    return () => {
      document.body.style.removeProperty('--bottom-bar-offset')
    }
  }, [])

  useEffect(() => {
    if (!toast) return
    const h = setTimeout(() => setToast(null), 2400)
    return () => clearTimeout(h)
  }, [toast])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    setLoading(true)
    Promise.all([listCart(token), listAddresses(token)])
      .then(([cart, addrs]) => {
        if (cancelled) return
        const filtered =
          selectedIds.length > 0
            ? cart.items.filter(i => selectedIds.includes(i.id))
            : cart.items
        setItems(filtered)
        setAddresses(addrs)
        setError(null)
      })
      .catch(err => {
        if (!cancelled) setError(err?.message ?? 'Failed to load checkout')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, selectedIds])

  const shopGroups = useMemo(() => groupByShop(items), [items])
  const address = addresses[0] ?? null

  const itemsSubtotal = useMemo(
    () =>
      items.reduce(
        (sum, i) =>
          sum + priceAfterDiscount(i.product.price, i.product.discount) * i.quantity,
        0,
      ),
    [items],
  )
  const shippingTotal = items.length > 0 ? SHIPPING_FEE_VND : 0
  const grandTotal = itemsSubtotal + shippingTotal

  const placeOrder = useCallback(async () => {
    if (!token || !address || items.length === 0 || placing) return
    setPlacing(true)
    try {
      await createOrder(token, {
        place: address.place,
        phone: address.phone,
        clientName: address.clientName,
        totalAmount: grandTotal,
        note: note.trim() || null,
        items: items.map(i => ({
          productId: i.productId,
          productName: i.product.name,
          quantity: i.quantity,
          price: priceAfterDiscount(i.product.price, i.product.discount),
          notes: i.notes,
        })),
        cartItemIds: items.map(i => i.id),
      })
      navigate('/orders')
    } catch (err) {
      setPlacing(false)
      const msg = err instanceof Error ? err.message : 'Failed to place order'
      setToast(msg)
    }
  }, [token, address, items, grandTotal, note, placing, navigate])

  if (loading) {
    return (
      <div className="bg-fog min-h-[calc(100vh-64px)]">
        <div className="max-w-[1200px] mx-auto px-6 py-10">
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive">
            Loading checkout...
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-fog min-h-[calc(100vh-64px)]">
        <div className="max-w-[1200px] mx-auto px-6 py-10">
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-brand-red">
            {error}
          </div>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="bg-fog min-h-[calc(100vh-64px)]">
        <div className="max-w-[1200px] mx-auto px-6 py-10">
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive flex flex-col gap-3 items-center">
            <span>No items selected for checkout.</span>
            <Link
              to="/cart"
              className="h-10 inline-flex items-center px-5 rounded-pin bg-brand-red text-white text-sm font-semibold hover:bg-[var(--color-brand-red-hover)] transition-colors"
            >
              Back to Cart
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-fog min-h-[calc(100vh-64px)]">
      <div className="max-w-[1200px] mx-auto px-6 py-6 pb-[120px] flex flex-col gap-3">
        {/* Address card */}
        <div className="bg-white rounded-pin-md border border-sand px-6 py-5 relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-[repeating-linear-gradient(135deg,_var(--color-brand-red)_0_24px,_#4d90fe_24px_48px)]" />
          <div className="flex items-start gap-6 pt-2">
            <div className="flex items-center gap-2 text-brand-red font-semibold min-w-[180px]">
              <span aria-hidden="true">📍</span>
              <span>Delivery Address</span>
            </div>
            {address ? (
              <>
                <div className="flex-1 min-w-0 text-sm text-plum">
                  <span className="font-semibold">
                    {address.clientName} ({address.phone})
                  </span>
                  <span className="ml-3 text-olive">{address.place}</span>
                </div>
                <span className="px-2 py-0.5 text-[11px] text-brand-red border border-brand-red rounded-sm">
                  Default
                </span>
                <span
                  aria-disabled="true"
                  tabIndex={-1}
                  className="text-sm text-warm-silver cursor-not-allowed select-none"
                  title="Address change is not available yet"
                >
                  Change
                </span>
              </>
            ) : (
              <div className="flex-1 text-sm text-olive">
                No saved address. Please add one before placing an order.
              </div>
            )}
          </div>
        </div>

        {/* Table header */}
        <div className="bg-white rounded-pin-md border border-sand px-6 py-3 grid grid-cols-[minmax(0,2.6fr)_minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,1fr)] text-xs font-semibold text-olive uppercase tracking-wide">
          <span>Products</span>
          <span className="text-right">Unit Price</span>
          <span className="text-right">Qty</span>
          <span className="text-right">Subtotal</span>
        </div>

        {/* Shop groups */}
        {shopGroups.map(shop => (
          <div
            key={shop.storeId}
            className="bg-white rounded-pin-md border border-sand overflow-hidden"
          >
            <div className="flex items-center gap-3 px-6 py-3 border-b border-sand">
              <span aria-hidden="true">🏬</span>
              <span className="text-sm font-semibold text-plum">{shop.store.name}</span>
              <span
                aria-disabled="true"
                tabIndex={-1}
                className="inline-flex items-center gap-1 text-sm text-[color:var(--color-brand-red)] opacity-60 cursor-not-allowed select-none"
                title="Chat is not available yet"
              >
                💬 Chat Now
              </span>
            </div>
            {shop.items.map(item => {
              const unit = priceAfterDiscount(item.product.price, item.product.discount)
              const cover = item.product.images[0] ?? ''
              return (
                <div
                  key={item.id}
                  className="grid grid-cols-[minmax(0,2.6fr)_minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,1fr)] items-center gap-4 px-6 py-4 border-t border-sand first:border-t-0"
                >
                  <div className="flex gap-3 min-w-0">
                    <div className="w-20 h-20 rounded-pin bg-fog overflow-hidden border border-sand shrink-0">
                      {cover && (
                        <img
                          src={cover}
                          alt={item.product.name}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                    <div className="flex flex-col min-w-0 gap-1">
                      <span className="text-sm text-plum line-clamp-2">
                        {item.product.name}
                      </span>
                      {item.notes && (
                        <span className="text-xs text-olive">Variant: {item.notes}</span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-right">
                    {item.product.discount > 0 ? (
                      <div className="flex flex-col items-end">
                        <span className="text-xs text-warm-silver line-through">
                          {formatVnd(item.product.price)}
                        </span>
                        <span className="text-plum">{formatVnd(unit)}</span>
                      </div>
                    ) : (
                      <span className="text-plum">{formatVnd(unit)}</span>
                    )}
                  </div>
                  <div className="text-sm text-right text-plum">{item.quantity}</div>
                  <div className="text-sm font-semibold text-brand-red text-right">
                    {formatVnd(unit * item.quantity)}
                  </div>
                </div>
              )
            })}

            {/* Note + shipping (per shop) */}
            <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6 px-6 py-4 border-t border-sand bg-fog/60">
              <label className="flex items-center gap-3 text-sm text-plum">
                <span className="text-olive whitespace-nowrap">Message:</span>
                <input
                  type="text"
                  value={note}
                  onChange={e => setNote(e.target.value)}
                  placeholder="Leave a note for the seller..."
                  className="flex-1 h-9 px-3 rounded-pin border border-sand bg-white text-sm text-plum focus:outline-none focus:border-brand-red"
                />
              </label>
              <div className="flex items-center justify-end gap-6 text-sm">
                <div className="flex items-center gap-3">
                  <span className="text-olive">Shipping:</span>
                  <span className="text-plum font-medium">Standard</span>
                  <span
                    aria-disabled="true"
                    tabIndex={-1}
                    className="text-sm text-warm-silver cursor-not-allowed select-none"
                    title="Shipping method change is not available yet"
                  >
                    Change
                  </span>
                </div>
                <span className="text-plum font-semibold">{formatVnd(SHIPPING_FEE_VND)}</span>
              </div>
            </div>
          </div>
        ))}

        {/* Payment + totals */}
        <div className="bg-white rounded-pin-md border border-sand overflow-hidden">
          <div className="flex items-center px-6 py-4">
            <span className="text-sm font-semibold text-plum">Payment Method</span>
            <div className="ml-auto flex items-center gap-4">
              <span className="text-sm text-plum">Cash on Delivery</span>
              <span
                aria-disabled="true"
                tabIndex={-1}
                className="text-sm font-semibold text-warm-silver cursor-not-allowed select-none uppercase tracking-wide"
                title="Payment method change is not available yet"
              >
                Change
              </span>
            </div>
          </div>
          <div className="border-t border-sand px-6 py-5 flex flex-col gap-2 text-sm">
            <div className="flex justify-end gap-10">
              <span className="text-olive">Items subtotal</span>
              <span className="text-plum min-w-[120px] text-right">
                {formatVnd(itemsSubtotal)}
              </span>
            </div>
            <div className="flex justify-end gap-10">
              <span className="text-olive">Shipping total</span>
              <span className="text-plum min-w-[120px] text-right">
                {formatVnd(shippingTotal)}
              </span>
            </div>
            <div className="flex justify-end gap-10 items-baseline">
              <span className="text-olive">Grand total</span>
              <span className="text-brand-red font-semibold text-xl min-w-[120px] text-right">
                {formatVnd(grandTotal)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-sand shadow-[0_-6px_20px_rgba(33,25,34,0.06)]">
        <div className="max-w-[1200px] mx-auto h-20 px-6 flex items-center justify-end gap-6 text-sm">
          <div className="flex items-baseline gap-3">
            <span className="text-plum">
              Total ({items.length} {items.length === 1 ? 'item' : 'items'}):
            </span>
            <span className="text-brand-red font-semibold text-2xl">
              {formatVnd(grandTotal)}
            </span>
          </div>
          <button
            type="button"
            onClick={placeOrder}
            disabled={placing || !address}
            className="h-12 px-10 rounded-pin bg-brand-red text-white text-sm font-semibold hover:bg-[var(--color-brand-red-hover)] transition-colors disabled:bg-sand disabled:text-warm-silver disabled:cursor-not-allowed"
          >
            {placing ? 'Placing...' : 'Place Order'}
          </button>
        </div>
      </div>

      {toast && (
        <div
          role="status"
          className="fixed left-1/2 -translate-x-1/2 bottom-28 z-[60] bg-plum text-white text-sm px-4 py-2 rounded-pin shadow-[0_10px_30px_rgba(33,25,34,0.25)]"
        >
          {toast}
        </div>
      )}
    </div>
  )
}
