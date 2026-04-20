export function formatVnd(n: number): string {
  return `${n.toLocaleString('vi-VN')}\u20AB`
}

export function priceAfterDiscount(price: number, discount: number): number {
  return discount > 0 ? Math.round(price * (1 - discount / 100)) : price
}
