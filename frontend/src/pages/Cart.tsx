import { useCallback, useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import {
  bulkDeleteCartItems,
  deleteCartItem,
  listCart,
  updateCartItem,
} from '../services/cart'
import { addFavorite } from '../services/favorite'
import { getSimilarProducts } from '../services/product'
import type { EnrichedCartItem } from '../types/cart'
import Checkbox from '../components/Checkbox'
import CartShopGroup, {
  type ShopSelectionState,
  type SimilarState,
} from '../components/cart/CartShopGroup'
import CartBottomBar from '../components/cart/CartBottomBar'

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

function priceAfterDiscount(price: number, discount: number) {
  return discount > 0 ? Math.round(price * (1 - discount / 100)) : price
}

export default function Cart() {
  const { token } = useAuth()
  const [items, setItems] = useState<EnrichedCartItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [openSimilarFor, setOpenSimilarFor] = useState<string | null>(null)
  const [similarState, setSimilarState] = useState<SimilarState | null>(null)
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
    listCart(token)
      .then(res => {
        if (!cancelled) {
          setItems(res.items)
          setError(null)
        }
      })
      .catch(err => {
        if (!cancelled) setError(err?.message ?? 'Failed to load cart')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  const shopGroups = useMemo(() => groupByShop(items), [items])
  const allIds = useMemo(() => items.map(i => i.id), [items])

  const selectedCount = selected.size
  const allSelected = allIds.length > 0 && selectedCount === allIds.length
  const someSelected = selectedCount > 0

  const totalAmount = useMemo(() => {
    return items
      .filter(i => selected.has(i.id))
      .reduce(
        (sum, i) =>
          sum + priceAfterDiscount(i.product.price, i.product.discount) * i.quantity,
        0,
      )
  }, [items, selected])

  const toggleItem = useCallback((id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleShop = useCallback(
    (shop: ShopGroup, next: boolean) => {
      setSelected(prev => {
        const out = new Set(prev)
        for (const it of shop.items) {
          if (next) out.add(it.id)
          else out.delete(it.id)
        }
        return out
      })
    },
    [],
  )

  const toggleAll = useCallback(
    (next: boolean) => {
      setSelected(next ? new Set(allIds) : new Set())
    },
    [allIds],
  )

  const applyQuantity = useCallback(
    async (id: string, next: number) => {
      if (!token) return
      setItems(prev => prev.map(i => (i.id === id ? { ...i, quantity: next } : i)))
      try {
        await updateCartItem(token, id, { quantity: next })
      } catch {
        setItems(prev =>
          prev.map(i => (i.id === id ? { ...i, quantity: i.quantity } : i)),
        )
        setToast('Failed to update quantity')
      }
    },
    [token],
  )

  const removeOne = useCallback(
    async (id: string) => {
      if (!token) return
      const snapshot = items
      setItems(prev => prev.filter(i => i.id !== id))
      setSelected(prev => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
      if (openSimilarFor === id) {
        setOpenSimilarFor(null)
        setSimilarState(null)
      }
      try {
        await deleteCartItem(token, id)
      } catch {
        setItems(snapshot)
        setToast('Failed to delete item')
      }
    },
    [token, items, openSimilarFor],
  )

  const deleteSelected = useCallback(async () => {
    if (!token || selected.size === 0) return
    const ids = [...selected]
    const snapshot = items
    setItems(prev => prev.filter(i => !selected.has(i.id)))
    setSelected(new Set())
    if (openSimilarFor && selected.has(openSimilarFor)) {
      setOpenSimilarFor(null)
      setSimilarState(null)
    }
    try {
      await bulkDeleteCartItems(token, ids)
      setToast(`Deleted ${ids.length} items`)
    } catch {
      setItems(snapshot)
      setToast('Bulk delete failed')
    }
  }, [token, selected, items, openSimilarFor])

  const saveToFavorites = useCallback(async () => {
    if (!token || selected.size === 0) return
    const selectedItems = items.filter(i => selected.has(i.id))
    const uniqueProductIds = [...new Set(selectedItems.map(i => i.productId))]
    try {
      await Promise.all(uniqueProductIds.map(pid => addFavorite(token, pid)))
      const ids = selectedItems.map(i => i.id)
      await bulkDeleteCartItems(token, ids)
      setItems(prev => prev.filter(i => !selected.has(i.id)))
      setSelected(new Set())
      setToast(`Saved ${uniqueProductIds.length} items to favorites`)
    } catch {
      setToast('Save to favorites failed')
    }
  }, [token, selected, items])

  const removeInactive = useCallback(() => {
    setToast('No inactive items to remove')
  }, [])

  const buy = useCallback(() => {
    if (selected.size === 0) return
    setToast('Checkout is not yet available')
  }, [selected])

  const handleToggleSimilar = useCallback(
    async (item: EnrichedCartItem) => {
      if (openSimilarFor === item.id) {
        setOpenSimilarFor(null)
        setSimilarState(null)
        return
      }
      setOpenSimilarFor(item.id)
      setSimilarState({ status: 'loading', total: 0, pageSize: 20, products: [] })
      try {
        const res = await getSimilarProducts(item.productId, 1)
        setSimilarState({
          status: 'loaded',
          total: res.total,
          pageSize: res.pageSize,
          products: res.products,
        })
      } catch {
        setSimilarState({
          status: 'loaded',
          total: 0,
          pageSize: 20,
          products: [],
        })
      }
    },
    [openSimilarFor],
  )

  const handleCloseSimilar = useCallback(() => {
    setOpenSimilarFor(null)
    setSimilarState(null)
  }, [])

  const selectionStateForShop = (shop: ShopGroup): ShopSelectionState => {
    const count = shop.items.reduce((acc, it) => acc + (selected.has(it.id) ? 1 : 0), 0)
    if (count === 0) return 'none'
    if (count === shop.items.length) return 'all'
    return 'some'
  }

  return (
    <div className="bg-fog min-h-[calc(100vh-64px)]">
      <div className="max-w-[1200px] mx-auto px-6 py-6 pb-[96px] flex flex-col gap-3">
        {/* Table header */}
        <div className="bg-white rounded-pin-md border border-sand px-4 py-3 grid grid-cols-[32px_minmax(0,2.4fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-4 text-xs font-semibold text-olive uppercase tracking-wide">
          <Checkbox
            checked={allSelected}
            indeterminate={someSelected && !allSelected}
            onChange={toggleAll}
            ariaLabel="Select all cart items"
          />
          <span>Product</span>
          <span>Unit Price</span>
          <span>Quantity</span>
          <span>Total</span>
          <span>Actions</span>
        </div>

        {loading && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive">
            Loading your cart...
          </div>
        )}

        {!loading && error && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-brand-red">
            {error}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="bg-white rounded-pin-md border border-sand p-10 text-center text-sm text-olive">
            Your cart is empty.
          </div>
        )}

        {!loading &&
          !error &&
          shopGroups.map(shop => {
            const selectionState = selectionStateForShop(shop)
            return (
              <CartShopGroup
                key={shop.storeId}
                store={shop.store}
                items={shop.items}
                selected={selected}
                selectionState={selectionState}
                onToggleShop={next => toggleShop(shop, next)}
                onToggleItem={toggleItem}
                onQuantityChange={applyQuantity}
                onDelete={removeOne}
                onToggleSimilar={handleToggleSimilar}
                onCloseSimilar={handleCloseSimilar}
                openSimilarFor={openSimilarFor}
                similarState={similarState}
              />
            )
          })}
      </div>

      <CartBottomBar
        totalItemCount={items.length}
        selectedCount={selectedCount}
        allSelected={allSelected}
        someSelected={someSelected}
        totalAmount={totalAmount}
        onToggleAll={toggleAll}
        onDeleteSelected={deleteSelected}
        onRemoveInactive={removeInactive}
        onSaveToFavorites={saveToFavorites}
        onBuy={buy}
      />

      {toast && (
        <div
          role="status"
          className="fixed left-1/2 -translate-x-1/2 bottom-24 z-[60] bg-plum text-white text-sm px-4 py-2 rounded-pin shadow-[0_10px_30px_rgba(33,25,34,0.25)]"
        >
          {toast}
        </div>
      )}

    </div>
  )
}
