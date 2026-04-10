# Shope

Monorepo e-commerce gồm **Frontend** (React + Vite + TypeScript), **Backend** (FastAPI + SQLAlchemy), và **Infra** (Docker — MySQL 8 + Milvus).

## Cấu trúc thư mục

```
shope/
├── frontend/          # ReactJS + Vite + TypeScript
├── backend/           # Python + FastAPI + SQLAlchemy + Alembic
├── infra/             # docker-compose.yml
├── Makefile           # Lệnh tắt cho các tác vụ phổ biến
├── .env.example       # Mẫu biến môi trường
└── README.md
```

## Khởi động nhanh (dùng Makefile)

```bash
cp .env.example backend/.env   # 1. Cấu hình .env
make docker-up                 # 2. Khởi động MySQL + Milvus
make setup-backend             # 3. Tạo venv + cài packages
make migrate                   # 4. Tạo tables trong MySQL
make run-backend               # 5. Chạy API server
# Terminal khác:
make setup-frontend            # 6. Cài Node packages
make run-frontend              # 7. Chạy Vite dev server
```

Xem tất cả lệnh có sẵn: `make help`

---

---

## Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu |
|---|---|
| Docker + Docker Compose | 24.x |
| Python | 3.11+ |
| Node.js | 20+ |

---

## Bước 1 — Chuẩn bị file `.env`

```bash
cp .env.example backend/.env
```

Mở `backend/.env` và chỉnh sửa các giá trị:

```env
MYSQL_PASSWORD=shope_password
SECRET_KEY=<chuỗi ngẫu nhiên mạnh>
```

Tạo `SECRET_KEY` ngẫu nhiên:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Bước 2 — Khởi động Docker (MySQL + Milvus)

```bash
# Đứng tại thư mục gốc của project
docker compose -f infra/docker-compose.yml up -d
```

Kiểm tra trạng thái:

```bash
docker compose -f infra/docker-compose.yml ps
```

Dịch vụ | Cổng
---|---
MySQL | `localhost:3306`
Milvus gRPC | `localhost:19530`
Milvus HTTP | `localhost:9091`
MinIO Console | `localhost:9001`

---

## Bước 3 — Cài đặt Backend

**Cách nhanh (dùng Makefile — đứng tại thư mục gốc):**

```bash
make setup-backend
```

**Hoặc thủ công:**

```bash
cd backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt venv
source venv/bin/activate        # Linux / macOS
# hoặc
venv\Scripts\activate           # Windows

# Cài packages
pip install -r requirements.txt
```

---

## Bước 4 — Chạy Database Migration

Đảm bảo MySQL đang chạy (Bước 2), sau đó:

```bash
# Cách nhanh (đứng tại thư mục gốc):
make migrate

# Hoặc thủ công (trong backend/ với venv kích hoạt):
alembic upgrade head
```

Lệnh này tạo tất cả 9 bảng trong MySQL:
`users`, `brands`, `categories`, `products`, `orders`, `order_items`, `cart_items`, `addresses`, `reviews`

Tạo migration mới khi thay đổi model:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Bước 5 — Chạy Backend

```bash
# Cách nhanh (đứng tại thư mục gốc):
make run-backend

# Hoặc thủ công (trong backend/ với venv kích hoạt):
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Auth API

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/auth/register` | Đăng ký tài khoản mới |
| POST | `/api/v1/auth/login` | Đăng nhập, nhận JWT token |
| POST | `/api/v1/auth/logout` | Đăng xuất (client xóa token) |

**Ví dụ đăng ký:**

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

**Ví dụ đăng nhập:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

---

## Bước 6 — Cài đặt & Chạy Frontend

```bash
# Cách nhanh (đứng tại thư mục gốc):
make setup-frontend
make run-frontend

# Hoặc thủ công:
cd frontend && npm install && npm run dev
```

Frontend chạy tại: http://localhost:5173

Vite đã được cấu hình proxy: mọi request đến `/api/*` sẽ được forward đến `http://localhost:8000`.

---

## Dừng Docker

```bash
docker compose -f infra/docker-compose.yml down

# Dừng và xóa toàn bộ volumes (xóa data):
docker compose -f infra/docker-compose.yml down -v
```
