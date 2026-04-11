---
feature: auth
doc_type: flows
tags: [login, register, logout, session-restore, protected-route]
---

# Auth — Flows

## Login Flow

1. User submits email + password on `pages/Login.tsx`
2. `useAuth().login()` calls `services/auth.ts → POST /api/v1/auth/login`
3. On success: token stored in `localStorage["access_token"]`, `user` state set
4. Router redirects authenticated user away from `/login` via `GuestRoute`

## Register Flow

1. User submits fullname, username, email, password on `pages/SignUp.tsx`
2. `useAuth().register()` calls `services/auth.ts → POST /api/v1/auth/register`
3. On success: **auto-login** — `register()` immediately calls `login()` with the same credentials
4. User lands on the home page already authenticated

## Logout Flow

1. User clicks logout button
2. `useAuth().logout()` clears `localStorage["access_token"]` and sets `user = null`
3. Router redirects to `/login` via `ProtectedRoute`

## Session Restore (Page Load)

```
Page loads
  → AuthContext mounts
  → reads localStorage["access_token"]
  → GET /api/v1/auth/me (with token)
      ├── 200 OK  → set user state, loading = false
      └── 401/error → clear token, user = null, loading = false
```

During `loading = true`, `ProtectedRoute` and `GuestRoute` both render `null` to prevent flash redirects.

## Route Guards

| Component | Behavior |
|---|---|
| `ProtectedRoute` | Redirects to `/login` if `user === null` |
| `GuestRoute` | Redirects to `/` if `user !== null` |

Both check `loading` first — render nothing until auth state is resolved.

## Frontend Auth State Shape

```typescript
// from AuthContext
{
  user: UserOut | null,
  token: string | null,
  loading: boolean,
  login(email, password): Promise<void>,
  register(payload): Promise<void>,
  logout(): void,
}
```
