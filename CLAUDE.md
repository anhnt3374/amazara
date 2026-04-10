# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

All commands run from the **project root** via Makefile:

```bash
make setup-backend              # Create backend/venv + pip install -r requirements.txt
make makemigrations msg=<name>  # Generate Alembic migration file from current models
make migrate                    # Apply pending migrations to MySQL (alembic upgrade head)
make run-backend                # uvicorn app.main:app --reload on :8000
make setup-frontend             # npm install in frontend/
make run-frontend               # Vite dev server on :5173
make docker-up                  # Start MySQL + Milvus via infra/docker-compose.yml
make docker-down                # Stop Docker services
```

Backend commands execute via `backend/venv/bin/` — never assume a globally activated venv.

**Migration workflow** — two steps always required in order:
```bash
make makemigrations msg="describe_change"   # creates a file in alembic/versions/
make migrate                                # applies it to MySQL
```
Running `make migrate` with an empty `alembic/versions/` does nothing. Always generate a migration file first.

Manual Alembic commands (from `backend/` with venv active):
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Architecture Overview

### Monorepo layout
- `frontend/` — React 18 + Vite + TypeScript; react-router-dom v6 for routing
- `backend/` — FastAPI application with SQLAlchemy ORM + Alembic migrations
- `infra/` — Docker Compose: MySQL 8.0 (port 3306) + Milvus standalone (port 19530) + supporting etcd/MinIO

### Backend structure (`backend/app/`)

| Layer | Path | Responsibility |
|---|---|---|
| Entry point | `main.py` | Imports `app.db.base` first (registers all ORM models); creates FastAPI app, CORS (allows `localhost:5173`), mounts `api_router` |
| Config | `core/config.py` | Pydantic `Settings` reads `backend/.env`; exposes `settings` singleton and `settings.DATABASE_URL` |
| Security | `core/security.py` | Password hashing via `bcrypt` directly (no passlib); SHA-256 pre-hash before bcrypt to remove 72-byte limit; JWT via `python-jose` |
| DB session | `db/session.py` | SQLAlchemy `engine` + `SessionLocal`; `get_db()` FastAPI dependency |
| Model registry | `db/base.py` | Imports all 9 models — **must be updated** when adding a new model; imported in `main.py` to ensure SQLAlchemy mapper resolution before first request |
| Models | `models/` | One file per table; all inherit `Base` + `UUIDMixin` (string UUID PK, auto-generated) |
| Schemas | `schemas/` | Pydantic v2 models for request/response validation |
| CRUD | `crud/` | Plain functions accepting `Session`; no repository class pattern |
| API | `api/v1/endpoints/` | FastAPI routers; mounted via `api/v1/router.py` at prefix `/api/v1` |
| Auth dependency | `api/v1/endpoints/auth.py` → `get_current_user` | Reads `Authorization: Bearer <token>`, decodes JWT, returns `User`; reuse as `Depends(get_current_user)` on any protected endpoint |

### Password hashing note

`passlib` was removed due to incompatibility with `bcrypt>=4.0`. `core/security.py` uses `bcrypt` directly. Passwords are SHA-256 pre-hashed before bcrypt to bypass bcrypt's 72-byte limit — this is transparent to callers of `hash_password()` / `verify_password()`.

### Database schema (MySQL)

9 tables with string UUID PKs:
`users` ← `orders`, `cart_items`, `addresses`, `reviews`
`brands` ← `categories` ← `products` ← `order_items`, `cart_items`, `reviews`

### Environment

`backend/.env` is loaded by `core/config.py`. Required variables are in `.env.example` at the project root. Copy with `cp .env.example backend/.env`.

Swagger UI available at `http://localhost:8000/docs` only when `APP_ENV=development`.

### Frontend structure (`frontend/src/`)

| Path | Responsibility |
|---|---|
| `App.tsx` | BrowserRouter + `AuthProvider` wrapper; `ProtectedRoute` (redirects to `/login` if no user), `GuestRoute` (redirects to `/success` if already logged in) |
| `contexts/AuthContext.tsx` | Central auth state: `user`, `token`, `loading`; `login()`, `register()` (auto-login after register), `logout()`; bootstraps from `localStorage` on mount by calling `GET /api/v1/auth/me` |
| `hooks/useAuth.ts` | `useAuth()` — consumes `AuthContext`; throws if used outside `AuthProvider` |
| `index.css` | Global CSS reset; imported in `main.tsx` |
| `auth.css` | Shared styles for Login and SignUp pages (split-panel card layout, error states) |
| `components/Icons.tsx` | SVG icon components: `ButterflyLogo`, `EyeIcon`, `EyeOffIcon`, `ArrowLeftIcon`, `GoogleIcon`, `FacebookIcon` |
| `services/auth.ts` | Raw fetch wrappers: `login()` → `{access_token}`, `register()` → `UserOut`, `getMe(token)` → `UserOut`; exports `ApiError`, `UserOut`, `RegisterPayload` |
| `pages/Login.tsx` | Login form; uses `useAuth().login()`; maps `"Invalid email or password"` to Vietnamese |
| `pages/SignUp.tsx` | SignUp form (fullname, username, email, password); uses `useAuth().register()`; client-side password ≥8 chars; maps API conflict errors to per-field messages |
| `pages/Success.tsx` | Shows logged-in user's fullname/username/email and a logout button |

### Auth identity flow

Token stored in `localStorage` key `access_token`. On any page load, `AuthContext` reads the stored token and calls `GET /api/v1/auth/me` to restore the session — if the token is expired or invalid it is cleared automatically.

To call authenticated APIs from any component:
```typescript
const { token } = useAuth()
fetch('/api/v1/some/endpoint', {
  headers: { Authorization: `Bearer ${token}` }
})
```

Vite dev proxy forwards `/api/*` → `http://localhost:8000` — no CORS issues in development.

Social login buttons (Google, Facebook) are rendered but non-functional: `disabled` + `pointer-events: none`.

Terms & Condition checkbox: submitting without checking applies `terms-checkbox--error` / `terms-label--error` CSS classes, turning the row red.

### Adding a new API endpoint

1. Create model in `backend/app/models/<name>.py` (inherit `Base`, `UUIDMixin`)
2. Add import to `backend/app/db/base.py`
3. Add Pydantic schema in `backend/app/schemas/<name>.py`
4. Add CRUD functions in `backend/app/crud/<name>.py`
5. Create router in `backend/app/api/v1/endpoints/<name>.py`
6. Register router in `backend/app/api/v1/router.py`
7. `make makemigrations msg="add_<name>"` then `make migrate`
