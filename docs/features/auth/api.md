---
feature: auth
doc_type: api
tags: [register, login, logout, me, jwt, bearer]
---

# Auth — API Reference

## Endpoints

All endpoints are prefixed `/api/v1/auth`.

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Register a new account |
| POST | `/api/v1/auth/login` | No | Log in, receive JWT |
| POST | `/api/v1/auth/logout` | No | Log out (client discards token) |
| GET | `/api/v1/auth/me` | Yes (Bearer) | Get current user info |

## Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "secret123",
    "fullname": "John Doe",
    "avatar": null
  }'
```

Response: `UserOut` — `{ id, email, username, fullname, avatar }`

## Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

Response: `{ "access_token": "<jwt>", "token_type": "bearer" }`

## Me (authenticated)

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

Response: `UserOut`

## Calling Authenticated Endpoints from Frontend

```typescript
const { token } = useAuth()
fetch('/api/v1/some/endpoint', {
  headers: { Authorization: `Bearer ${token}` }
})
```

Vite dev proxy forwards `/api/*` → `http://localhost:8000`.

## Backend Dependency

```python
from app.api.v1.endpoints.auth import get_current_user

@router.get("/protected")
def my_route(current_user: User = Depends(get_current_user)):
    ...
```
