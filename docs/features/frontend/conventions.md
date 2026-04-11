---
feature: frontend
doc_type: conventions
tags: [tailwind, clsx, proxy, social-login, forms]
---

# Frontend — Conventions

## Tailwind CSS v4

- Plugin: `@tailwindcss/vite` in `vite.config.ts` — **no `tailwind.config.*` file**
- Entry: `@import "tailwindcss"` in `index.css`
- Conditional classes: use `clsx`
  ```typescript
  clsx(inputBase, error ? 'border-red-500' : 'border-[#E0E0E0]')
  ```
- Complex gradients (radial/linear) → use inline `style` prop, not Tailwind utilities
- Custom keyframe animations defined in `index.css` with `@keyframes`, referenced via inline `style={{ animation: '...' }}`

## Vite Dev Proxy

`frontend/vite.config.ts` proxies `/api/*` → `http://localhost:8000`.
No CORS headers needed in development — all fetch calls use relative paths `/api/v1/...`.

## Forms

- Client-side validation before API call (e.g., password ≥ 8 chars in SignUp)
- API error messages mapped to per-field state for display
- Terms & Conditions checkbox: error state toggles `border-red-500` / `text-red-500` via `clsx`

## Social Login

Google and Facebook login buttons are rendered but non-functional: `disabled` attribute + `pointer-events: none` style. Placeholder only.

## Header Component

`components/Header.tsx` manages its own state:
- `scrolled` — hides top/bottom info bars and sticks the nav to the top
- `hoveredItem` — controls which dropdown is open; debounced via 80ms `setTimeout` to prevent flicker
- `searchOpen` — controls search overlay; locks `document.body.style.overflow = 'hidden'` while open

Header is rendered by `components/Layout.tsx` and present on all non-auth pages.

## Auth Pages Layout

`Login.tsx` and `SignUp.tsx` are **not** wrapped in `Layout` — they use their own full-page two-column gradient design.
