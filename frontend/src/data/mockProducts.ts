import type { Brand, Category, Product } from '../types/product'

export const MOCK_BRANDS: Brand[] = [
  { id: 'brand-1', name: 'Nike' },
  { id: 'brand-2', name: 'Jordan' },
  { id: 'brand-3', name: 'Converse' },
  { id: 'brand-4', name: 'ACG' },
]

export const MOCK_CATEGORIES: Category[] = [
  { id: 'cat-1', name: 'Running Shoes', brandId: 'brand-1' },
  { id: 'cat-2', name: 'Lifestyle Shoes', brandId: 'brand-1' },
  { id: 'cat-3', name: 'Basketball Shoes', brandId: 'brand-2' },
  { id: 'cat-4', name: 'Casual Shoes', brandId: 'brand-2' },
  { id: 'cat-5', name: 'Sneakers', brandId: 'brand-3' },
  { id: 'cat-6', name: 'Trail Shoes', brandId: 'brand-4' },
]

export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'prod-1',
    name: 'Nike Air Max 90',
    description: 'Classic cushioned running shoe',
    price: 3200000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod1a/400/400',
      'https://picsum.photos/seed/prod1b/400/400',
      'https://picsum.photos/seed/prod1c/400/400',
    ],
    categoryId: 'cat-1',
  },
  {
    id: 'prod-2',
    name: 'Nike Pegasus 41',
    description: 'Responsive everyday running shoe',
    price: 3600000,
    discount: 15,
    images: [
      'https://picsum.photos/seed/prod2a/400/400',
      'https://picsum.photos/seed/prod2b/400/400',
    ],
    categoryId: 'cat-1',
  },
  {
    id: 'prod-3',
    name: 'Nike Dunk Low Retro',
    description: 'Iconic basketball-inspired lifestyle shoe',
    price: 2800000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod3a/400/400',
    ],
    categoryId: 'cat-2',
  },
  {
    id: 'prod-4',
    name: 'Nike Air Force 1 07',
    description: 'Timeless court classic',
    price: 2900000,
    discount: 20,
    images: [
      'https://picsum.photos/seed/prod4a/400/400',
      'https://picsum.photos/seed/prod4b/400/400',
      'https://picsum.photos/seed/prod4c/400/400',
    ],
    categoryId: 'cat-2',
  },
  {
    id: 'prod-5',
    name: 'Air Jordan 1 Retro High OG',
    description: 'The original high-top basketball shoe',
    price: 4500000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod5a/400/400',
      'https://picsum.photos/seed/prod5b/400/400',
    ],
    categoryId: 'cat-3',
  },
  {
    id: 'prod-6',
    name: 'Air Jordan 4 Retro',
    description: 'Performance meets street style',
    price: 5200000,
    discount: 10,
    images: [
      'https://picsum.photos/seed/prod6a/400/400',
      'https://picsum.photos/seed/prod6b/400/400',
      'https://picsum.photos/seed/prod6c/400/400',
    ],
    categoryId: 'cat-3',
  },
  {
    id: 'prod-7',
    name: 'Jordan Stadium 90',
    description: 'Casual everyday sneaker',
    price: 3100000,
    discount: 25,
    images: [
      'https://picsum.photos/seed/prod7a/400/400',
    ],
    categoryId: 'cat-4',
  },
  {
    id: 'prod-8',
    name: 'Jordan Series ES',
    description: 'Easy slip-on comfort',
    price: 2400000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod8a/400/400',
      'https://picsum.photos/seed/prod8b/400/400',
    ],
    categoryId: 'cat-4',
  },
  {
    id: 'prod-9',
    name: 'Converse Chuck Taylor All Star',
    description: 'The classic canvas high-top',
    price: 1500000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod9a/400/400',
    ],
    categoryId: 'cat-5',
  },
  {
    id: 'prod-10',
    name: 'Converse Chuck 70',
    description: 'Premium vintage sneaker',
    price: 2100000,
    discount: 30,
    images: [
      'https://picsum.photos/seed/prod10a/400/400',
      'https://picsum.photos/seed/prod10b/400/400',
      'https://picsum.photos/seed/prod10c/400/400',
    ],
    categoryId: 'cat-5',
  },
  {
    id: 'prod-11',
    name: 'Converse Run Star Hike',
    description: 'Platform chunky sneaker',
    price: 2600000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod11a/400/400',
      'https://picsum.photos/seed/prod11b/400/400',
    ],
    categoryId: 'cat-5',
  },
  {
    id: 'prod-12',
    name: 'Nike ACG Mountain Fly 2 Low',
    description: 'Trail-ready outdoor shoe',
    price: 4100000,
    discount: 15,
    images: [
      'https://picsum.photos/seed/prod12a/400/400',
      'https://picsum.photos/seed/prod12b/400/400',
    ],
    categoryId: 'cat-6',
  },
  {
    id: 'prod-13',
    name: 'Nike ACG Lowcate',
    description: 'Durable all-terrain shoe',
    price: 2800000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod13a/400/400',
    ],
    categoryId: 'cat-6',
  },
  {
    id: 'prod-14',
    name: 'Nike Vomero 18',
    description: 'Maximum cushioning for long runs',
    price: 4200000,
    discount: 20,
    images: [
      'https://picsum.photos/seed/prod14a/400/400',
      'https://picsum.photos/seed/prod14b/400/400',
      'https://picsum.photos/seed/prod14c/400/400',
    ],
    categoryId: 'cat-1',
  },
  {
    id: 'prod-15',
    name: 'Air Jordan 1 Low',
    description: 'Low-cut everyday classic',
    price: 3000000,
    discount: 0,
    images: [
      'https://picsum.photos/seed/prod15a/400/400',
      'https://picsum.photos/seed/prod15b/400/400',
    ],
    categoryId: 'cat-3',
  },
  {
    id: 'prod-16',
    name: 'Nike Blazer Mid 77 Vintage',
    description: 'Retro basketball style',
    price: 2700000,
    discount: 40,
    images: [
      'https://picsum.photos/seed/prod16a/400/400',
      'https://picsum.photos/seed/prod16b/400/400',
    ],
    categoryId: 'cat-2',
  },
]

export const PRICE_RANGES = [
  { value: '0-2000000', label: 'Under 2,000,000 \u20AB', range: [0, 2000000] as [number, number] },
  { value: '2000000-3000000', label: '2,000,000 \u20AB - 3,000,000 \u20AB', range: [2000000, 3000000] as [number, number] },
  { value: '3000000-4000000', label: '3,000,000 \u20AB - 4,000,000 \u20AB', range: [3000000, 4000000] as [number, number] },
  { value: '4000000-99999999', label: 'Over 4,000,000 \u20AB', range: [4000000, 99999999] as [number, number] },
]
