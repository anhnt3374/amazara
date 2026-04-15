import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { BagIcon, HeartIcon, JordanLogo, NikeSwoosh, SearchIcon } from './Icons'

const NAV_ITEMS = ['New & Featured', 'Men', 'Women', 'Kids', 'Sale']

const PAGE_NAMES: Record<string, string> = {
  '/': 'Home',
  '/success': 'Profile',
  '/favorites': 'Favorites',
  '/cart': 'Cart',
}

const DROPDOWN_DATA: Record<string, { title: string; items: string[] }[]> = {
  'New & Featured': [
    {
      title: 'Featured',
      items: [
        'Upcoming Drops', 'New Arrivals', 'Trended', 'Limited Launch Calendars',
        'SNKRS Launch Calendar', 'Customize with Nike By You', 'Jordan',
        'Kobe Bryant', 'LeBron James', 'National Team Kits',
      ],
    },
    {
      title: 'Trending',
      items: [
        'Just Do the Work', 'More Colours. More Running', "What's Trending",
        '24.7 Collection', 'Colours of the Season', 'Retro Running',
        'Running Shoe Finder', 'Nike Mind',
      ],
    },
    {
      title: 'Shop Icons',
      items: ['Lifestyle', 'Air Force 1', 'Air Jordan 1', 'Air Max', 'Dunk', 'Cortez', 'Blazer', 'Pegasus', 'Vomero'],
    },
    {
      title: 'Shop By Sport',
      items: [
        'Running', 'Basketball', 'Football', 'Tennis & Pickleball',
        'Gym & Training', 'Yoga', 'Skateboarding', 'Trail Running', 'All Conditions Gear',
      ],
    },
  ],
  'Men': [
    {
      title: 'Featured',
      items: ['New Arrivals', 'Best Sellers', 'Member Exclusives', 'Sale'],
    },
    {
      title: 'Shoes',
      items: ['All Shoes', 'Lifestyle', 'Running', 'Basketball', 'Training & Gym', 'Football', 'Golf', 'Tennis'],
    },
    {
      title: 'Clothing',
      items: ['All Clothing', 'Tops & T-Shirts', 'Hoodies & Sweatshirts', 'Jackets', 'Trousers & Tights', 'Shorts'],
    },
    {
      title: 'Accessories',
      items: ['Bags & Backpacks', 'Socks', 'Hats & Headwear', 'Sunglasses'],
    },
  ],
  'Women': [
    {
      title: 'Featured',
      items: ['New Arrivals', 'Best Sellers', 'Member Exclusives', 'Sale'],
    },
    {
      title: 'Shoes',
      items: ['All Shoes', 'Lifestyle', 'Running', 'Training & Gym', 'Basketball', 'Football', 'Golf', 'Tennis'],
    },
    {
      title: 'Clothing',
      items: ['All Clothing', 'Tops & T-Shirts', 'Hoodies & Sweatshirts', 'Jackets', 'Trousers & Tights', 'Sports Bras'],
    },
    {
      title: 'Accessories',
      items: ['Bags & Backpacks', 'Socks', 'Hats & Headwear', 'Yoga & Training Gear'],
    },
  ],
  'Kids': [
    {
      title: 'Featured',
      items: ['New Arrivals', 'Best Sellers', 'Sale'],
    },
    {
      title: 'By Age',
      items: ["Baby (0–2 yrs)", "Toddler (2–4 yrs)", "Little Kids (4–7 yrs)", "Big Kids (7–15 yrs)"],
    },
    {
      title: 'Shoes',
      items: ['All Shoes', 'Lifestyle', 'Running', 'Basketball', 'Football'],
    },
    {
      title: 'Clothing',
      items: ['All Clothing', 'Tops', 'Hoodies & Sweatshirts', 'Jackets', 'Shorts'],
    },
  ],
  'Sale': [
    {
      title: "Men's Sale",
      items: ['Shoes', 'Clothing', 'Accessories'],
    },
    {
      title: "Women's Sale",
      items: ['Shoes', 'Clothing', 'Accessories'],
    },
    {
      title: "Kids' Sale",
      items: ['Shoes', 'Clothing', 'Accessories'],
    },
    {
      title: 'Up to',
      items: ['Up to 25% Off', 'Up to 40% Off', 'Up to 50% Off', 'Clearance'],
    },
  ],
}

const POPULAR_SEARCHES = ['air max', 'air force 1', 'jordan', 'nike mercurial vapor 16', 'jordan 1 low', 'basketball shoes', 'ja 3', 'structure plus']

export default function Header() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const currentPage = PAGE_NAMES[location.pathname] ?? ''
  const [scrolled, setScrolled] = useState(false)
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchClosing, setSearchClosing] = useState(false)
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 0)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (searchOpen && !searchClosing) {
      document.body.style.overflow = 'hidden'
      setTimeout(() => searchInputRef.current?.focus(), 50)
    }
    if (!searchOpen) {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [searchOpen, searchClosing])

  function closeSearch() {
    setSearchClosing(true)
  }

  function handleSearchAnimEnd() {
    if (searchClosing) {
      setSearchOpen(false)
      setSearchClosing(false)
    }
  }

  function handleNavEnter(item: string) {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current)
    setHoveredItem(item)
  }

  function handleNavLeave() {
    hoverTimeoutRef.current = setTimeout(() => setHoveredItem(null), 80)
  }

  function handleDropdownEnter() {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current)
  }

  function handleDropdownLeave() {
    hoverTimeoutRef.current = setTimeout(() => setHoveredItem(null), 80)
  }

  function handleProtectedNav(dest: string) {
    if (!user) navigate('/login')
    else navigate(dest)
  }

  const dropdownColumns = hoveredItem ? DROPDOWN_DATA[hoveredItem] : null

  return (
    <>
      <header className="relative z-40">
        {/* TOP BAR */}
        <div
          className="overflow-hidden transition-all duration-300 ease-in-out"
          style={{ maxHeight: scrolled ? '0' : '32px', opacity: scrolled ? 0 : 1 }}
        >
          <div className="bg-[#f5f5f5] flex items-center justify-between px-12 h-8">
            <JordanLogo className="w-5 h-5 text-black" />
            <div className="flex items-center gap-4 text-xs text-[#111]">
              <Link to="/" className="hover:underline">Find a Store</Link>
              <span className="text-[#ccc]">|</span>
              <Link to="/" className="hover:underline">Help</Link>
              <span className="text-[#ccc]">|</span>
              <Link to="/login" className="hover:underline font-medium">Sign In</Link>
            </div>
          </div>
        </div>

        {/* MAIN NAV */}
        <div
          className="bg-[#111] transition-shadow duration-200"
          style={{ position: scrolled ? 'fixed' : 'relative', top: 0, left: 0, right: 0, zIndex: 40, boxShadow: scrolled && location.pathname !== '/list' ? '0 1px 4px rgba(0,0,0,0.25)' : 'none' }}
        >
          <div className="relative flex items-center px-12 h-[46px]">
            {/* Nike logo — left */}
            <div className="flex-1 flex items-center">
              <Link to="/" className="flex-shrink-0">
                <svg width="50" height="18" viewBox="0 0 60 22" fill="white" xmlns="http://www.w3.org/2000/svg">
                  <path d="M57.6 0.6L18.2 16.4C14.8 17.8 11.9 18.4 9.6 18.4C6.8 18.4 4.8 17.4 3.8 15.6C2.4 13.2 3.2 9.4 5.8 6.4C4 8 3 10.2 3.4 12C3.8 13.6 5.2 14.6 7.2 14.6C8.8 14.6 10.8 14.2 13.2 13.2L60 0L57.6 0.6Z" />
                </svg>
              </Link>
            </div>

            {/* Nav items — absolutely centered */}
            <nav className="absolute left-1/2 -translate-x-1/2 flex items-center gap-6">
              {NAV_ITEMS.map(item => (
                <div
                  key={item}
                  className="relative"
                  onMouseEnter={() => handleNavEnter(item)}
                  onMouseLeave={handleNavLeave}
                >
                  <button
                    className={`text-sm font-medium pb-1 border-b-2 transition-colors duration-150 ${
                      hoveredItem === item
                        ? 'border-white text-white'
                        : 'border-transparent text-[#ccc] hover:text-white'
                    }`}
                  >
                    {item}
                  </button>
                </div>
              ))}
            </nav>

            {/* Right actions */}
            <div className="flex-1 flex items-center justify-end gap-2">
              {/* Search */}
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 bg-[#333] rounded-full pl-3 pr-4 py-1.5 text-sm font-medium text-white hover:bg-[#444] transition-colors"
              >
                <SearchIcon className="text-white w-4 h-4" />
                <span>Search</span>
              </button>
              {/* Heart */}
              <button
                onClick={() => handleProtectedNav('/favorites')}
                className="p-1.5 rounded-full hover:bg-[#333] transition-colors text-white"
                aria-label="Favorites"
              >
                <HeartIcon />
              </button>
              {/* Bag */}
              <button
                onClick={() => handleProtectedNav('/cart')}
                className="p-1.5 rounded-full hover:bg-[#333] transition-colors text-white"
                aria-label="Cart"
              >
                <BagIcon />
              </button>
            </div>
          </div>

          {/* DROPDOWN */}
          {hoveredItem && dropdownColumns && (
            <div
              className="absolute left-0 right-0 bg-white border-t border-[#e5e5e5] shadow-lg"
              style={{ top: '100%' }}
              onMouseEnter={handleDropdownEnter}
              onMouseLeave={handleDropdownLeave}
            >
              <div className="max-w-6xl mx-auto px-8 py-8 grid grid-cols-4 gap-8">
                {dropdownColumns.map(col => (
                  <div key={col.title}>
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-[#757575] mb-3">{col.title}</h4>
                    <ul className="space-y-1.5">
                      {col.items.map(item => (
                        <li key={item}>
                          <a href="#" className="text-sm text-[#111] hover:underline">{item}</a>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* BOTTOM BAR */}
        <div
          className="overflow-hidden transition-all duration-300 ease-in-out"
          style={{ maxHeight: scrolled ? '0' : '40px', opacity: scrolled ? 0 : 1 }}
        >
          <div className="bg-[#f5f5f5] flex items-center justify-center h-10 text-xs text-[#111]">
            {currentPage}
          </div>
        </div>

        {/* Spacer when nav is fixed */}
        {scrolled && <div style={{ height: '46px' }} />}
      </header>

      {/* DROPDOWN BACKDROP — dims page content behind the header when a nav item is hovered */}
      {hoveredItem && (
        <div
          className="fixed inset-0 z-30 pointer-events-none transition-opacity duration-150"
          style={{ backgroundColor: 'rgba(0,0,0,0.2)' }}
        />
      )}

      {/* SEARCH OVERLAY */}
      {searchOpen && (
        <div
          className="fixed inset-0 z-50 flex flex-col"
          style={{
            animation: searchClosing
              ? 'backdropOut 0.2s ease-in forwards'
              : 'backdropIn 0.2s ease-out',
          }}
          onAnimationEnd={handleSearchAnimEnd}
        >
          {/* Search panel:
              - mobile/tablet (< lg): flex-1 = full screen
              - desktop (>= lg): fixed 40vh, backdrop fills the rest */}
          <div
            className="bg-white flex-1 lg:flex-none lg:h-[40vh] flex flex-col overflow-y-auto shadow-lg"
            style={{
              animation: searchClosing
                ? 'searchPanelOut 0.2s ease-in forwards'
                : 'searchPanelIn 0.25s ease-out',
            }}
          >
            {/* Top row: logo + search input + cancel */}
            <div className="flex items-center gap-5 px-6 sm:px-10 lg:px-16 pt-5 pb-4 border-b border-[#e5e5e5]">
              <svg width="52" height="20" viewBox="0 0 60 22" fill="black" xmlns="http://www.w3.org/2000/svg" className="flex-shrink-0">
                <path d="M57.6 0.6L18.2 16.4C14.8 17.8 11.9 18.4 9.6 18.4C6.8 18.4 4.8 17.4 3.8 15.6C2.4 13.2 3.2 9.4 5.8 6.4C4 8 3 10.2 3.4 12C3.8 13.6 5.2 14.6 7.2 14.6C8.8 14.6 10.8 14.2 13.2 13.2L60 0L57.6 0.6Z" />
              </svg>
              <div className="flex items-center gap-3 flex-1 bg-[#f5f5f5] rounded-full px-4 py-2.5">
                <SearchIcon className="text-[#757575] w-5 h-5 flex-shrink-0" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search"
                  className="flex-1 text-base outline-none border-none bg-transparent text-[#111] placeholder-[#757575]"
                />
              </div>
              <button
                onClick={closeSearch}
                className="text-sm font-medium text-[#111] hover:underline flex-shrink-0 ml-1"
              >
                Cancel
              </button>
            </div>

            {/* Popular search terms */}
            <div className="px-6 sm:px-10 lg:px-16 pt-6 pb-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#757575] mb-4">Popular Search Terms</p>
              <div className="flex flex-wrap gap-3">
                {POPULAR_SEARCHES.map(term => (
                  <button
                    key={term}
                    className="border border-[#e5e5e5] rounded-full px-5 py-2 text-sm text-[#111] hover:border-[#111] transition-colors"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Backdrop — hidden on mobile (panel covers full screen), visible on desktop */}
          <div
            className="flex-none h-0 lg:flex-1 lg:h-auto cursor-default"
            style={{ backgroundColor: 'rgba(0,0,0,0.2)' }}
            onClick={closeSearch}
          />
        </div>
      )}
    </>
  )
}
