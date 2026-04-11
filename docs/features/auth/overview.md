---
feature: auth
doc_type: overview
tags: [jwt, bcrypt, session, localStorage, password-hashing]
---

# Auth — Overview

## Responsibility

Authentication covers user registration, login, logout, session persistence, and protecting routes on both frontend and backend.

## Password Hashing

`passlib` was removed due to incompatibility with `bcrypt>=4.0`. The project uses `bcrypt` directly in `backend/app/core/security.py`.

**SHA-256 pre-hash:** Passwords are SHA-256 pre-hashed before being passed to bcrypt. This removes bcrypt's 72-byte input limit and is fully transparent to callers of `hash_password()` / `verify_password()`.

## Token Strategy

- JWT issued on login, signed with `SECRET_KEY`
- Token stored in browser `localStorage` under key `access_token`
- Token sent as `Authorization: Bearer <token>` on all authenticated requests
- No refresh token — expired/invalid tokens are detected and cleared automatically

## Session Bootstrap

On every page load, `AuthContext` (`frontend/src/contexts/AuthContext.tsx`):
1. Reads `access_token` from `localStorage`
2. Calls `GET /api/v1/auth/me` with the token
3. If valid → restores `user` state
4. If expired/invalid → clears token and sets `user = null`

## Backend Auth Dependency

`get_current_user` in `backend/app/api/v1/endpoints/auth.py`:
- Reads `Authorization: Bearer <token>`
- Decodes JWT
- Returns the `User` ORM object
- Reuse as `Depends(get_current_user)` on any protected endpoint

## Key Files

| File | Role |
|---|---|
| `backend/app/core/security.py` | `hash_password()`, `verify_password()`, JWT encode/decode |
| `backend/app/api/v1/endpoints/auth.py` | Auth routes + `get_current_user` dependency |
| `frontend/src/contexts/AuthContext.tsx` | Central auth state, session bootstrap |
| `frontend/src/hooks/useAuth.ts` | `useAuth()` hook — consumes AuthContext |
| `frontend/src/services/auth.ts` | Raw fetch wrappers for auth API |
