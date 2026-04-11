---
feature: frontend
doc_type: overview
tags: [react, vite, typescript, routing, components, pages]
---

# Frontend — Overview

## Stack

React 18 + Vite + TypeScript + react-router-dom v6 + Tailwind CSS v4. All source code under `frontend/src/`.

## Key Files

| Path | Responsibility |
|---|---|
| `App.tsx` | BrowserRouter + `AuthProvider` wrapper; defines `ProtectedRoute` and `GuestRoute`; declares all routes |
| `contexts/AuthContext.tsx` | Central auth state: `user`, `token`, `loading`; `login()`, `register()` (auto-login after register), `logout()`; bootstraps session from `localStorage` on mount |
| `hooks/useAuth.ts` | `useAuth()` — consumes `AuthContext`; throws if used outside `AuthProvider` |
| `index.css` | Tailwind v4 entry: `@import "tailwindcss"` + base layer (font, link, button resets) |
| `components/Icons.tsx` | SVG icon components |
| `services/auth.ts` | Raw fetch wrappers: `login()`, `register()`, `getMe()`; exports `ApiError`, `UserOut`, `RegisterPayload` |
| `components/Layout.tsx` | Shared layout wrapper — renders `<Header>` above `{children}` |
| `components/Header.tsx` | Two-row header: top info bar + sticky nav bar with dropdown, search overlay, auth-gated icons |

## Pages

| Page | Route | Guard | Description |
|---|---|---|---|
| `Home` | `/` | None | Landing page with header |
| `Login` | `/login` | GuestRoute | Email/password login form |
| `SignUp` | `/signup` | GuestRoute | Registration form (fullname, username, email, password) |
| `Success` | `/success` | ProtectedRoute | Logged-in user profile + logout |
| `Favorites` | `/favorites` | ProtectedRoute | Placeholder favorites page |
| `Cart` | `/cart` | ProtectedRoute | Placeholder cart page |

## Route Guards

- **`ProtectedRoute`**: redirects to `/login` if `user === null`
- **`GuestRoute`**: redirects to `/` if `user !== null`
- Both render `null` while `loading === true` to prevent flash redirects

## Icons

`components/Icons.tsx` exports: `ButterflyLogo`, `EyeIcon`, `EyeOffIcon`, `ArrowLeftIcon`, `GoogleIcon`, `FacebookIcon`, `NikeSwoosh`, `JordanLogo`, `SearchIcon`, `HeartIcon`, `BagIcon`
