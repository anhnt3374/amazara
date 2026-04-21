# Amaraza

E-commerce monorepo with **Frontend** (React + Vite + TypeScript), **Backend** (FastAPI + SQLAlchemy), and **Infra** (Docker — MySQL 8 + Milvus).

## Project Structure

```
Amaraza/
├── frontend/          # React + Vite + TypeScript
├── backend/           # Python + FastAPI + SQLAlchemy + Alembic
├── infra/             # docker-compose.yml
├── mock/              # Seed scripts + CSV/JSON data
├── docs/              # Feature docs, indexes, shared conventions
├── Makefile           # Shortcuts for common tasks
├── .env.example       # Environment variable template
└── README.md
```

## Quick Start (via Makefile)

```bash
cp .env.example backend/.env   # 1. Configure .env
make docker-up                 # 2. Start MySQL + Milvus
make venv                      # 3a. Create virtual environment
make install-backend           # 3b. Install Python packages
make migrate                   # 4. Create tables in MySQL
make run-backend               # 5. Run API server
# In another terminal:
make install-frontend          # 6. Install Node packages
make run-frontend              # 7. Run Vite dev server
```

See all available commands: `make help`

---

## Requirements

| Tool | Minimum version |
|---|---|
| Docker + Docker Compose | 24.x |
| Python | 3.11+ |
| Node.js | 20+ |

---

## Step 1 — Configure `.env`

```bash
cp .env.example backend/.env
```

Open `backend/.env` and update the values:

```env
MYSQL_PASSWORD=shope_password
SECRET_KEY=<strong random string>
```

Generate a random `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 2 — Start Docker (MySQL + Milvus)

```bash
# From the project root
docker compose -f infra/docker-compose.yml up -d
```

Check status:

```bash
docker compose -f infra/docker-compose.yml ps
```

| Service | Port |
|---|---|
| MySQL | `localhost:3306` |
| Milvus gRPC | `localhost:19530` |
| Milvus HTTP | `localhost:9091` |
| MinIO Console | `localhost:9001` |

---

## Step 3 — Install Backend

**Quick (via Makefile — from project root):**

```bash
make venv
make install-backend
```

**Or manually:**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate venv
source venv/bin/activate        # Linux / macOS
# or
venv\Scripts\activate           # Windows

# Install packages
pip install -r requirements.txt
```

---

## Step 4 — Run Database Migrations

Make sure MySQL is running (Step 2), then:

```bash
# Quick (from project root):
make migrate

# Or manually (inside backend/ with venv active):
alembic upgrade head
```

This creates all 10 tables in MySQL:
`users`, `stores`, `brands`, `categories`, `products`, `orders`, `order_items`, `cart_items`, `addresses`, `reviews`

To generate a new migration after changing a model:

```bash
make makemigrations msg="describe your change"
make migrate
```

---

## Step 5 — Run Backend

```bash
# Quick (from project root):
make run-backend

# Or manually (inside backend/ with venv active):
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new account |
| POST | `/api/v1/auth/login` | Log in and receive a JWT token |
| POST | `/api/v1/auth/logout` | Log out (client discards token) |
| GET  | `/api/v1/auth/me` | Get current user info (Bearer token required) |
| CRUD | `/api/v1/addresses` | User addresses (create, list, get, update, delete) |

**Register example:**

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

**Login example:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

---

## Step 6 — Install & Run Frontend

```bash
# Quick (from project root):
make install-frontend
make run-frontend

# Or manually:
cd frontend && npm install && npm run dev
```

Frontend runs at: http://localhost:5173

Vite is configured with a proxy: all requests to `/api/*` are forwarded to `http://localhost:8000`.

---

## Seed Mock Data (Optional)

After running migrations, you can populate the database with mock data for development:

```bash
backend/venv/bin/python mock/seed_users.py       # 100 users
backend/venv/bin/python mock/seed_addresses.py    # 1–3 addresses per user
backend/venv/bin/python mock/seed_stores.py       # 20 stores
backend/venv/bin/python mock/seed_products.py     # ~9,350 products (random store assignment)
backend/venv/bin/python mock/seed_reviews.py      # 100–500 reviews per product
```

Scripts are idempotent — they skip records that already exist. Credentials are exported to CSV files in `mock/`.

---

## Stop Docker

```bash
docker compose -f infra/docker-compose.yml down

# Stop and remove all volumes (deletes data):
docker compose -f infra/docker-compose.yml down -v
```
