.PHONY: help \
        venv install-backend install-frontend \
        makemigrations migrate \
        run-backend run-frontend \
        docker-up docker-down docker-logs

help:
	@echo "Backend"
	@echo "  make venv                  Tạo virtual environment tại backend/venv"
	@echo "  make install-backend       Cài packages Python từ requirements.txt"
	@echo "  make makemigrations msg=x  Tạo migration file từ models"
	@echo "  make migrate               Áp dụng migration vào database"
	@echo "  make run-backend           Chạy FastAPI dev server (port 8000)"
	@echo ""
	@echo "Frontend"
	@echo "  make install-frontend      Cài Node packages (npm install)"
	@echo "  make run-frontend          Chạy Vite dev server (port 5173)"
	@echo ""
	@echo "Docker"
	@echo "  make docker-up             Khởi động MySQL + Milvus"
	@echo "  make docker-down           Dừng Docker services"
	@echo "  make docker-logs           Xem logs Docker services"

# ── Backend ───────────────────────────────────────────────────────────────────

venv:
	python -m venv backend/venv

install-backend:
	backend/venv/bin/pip install --upgrade pip
	backend/venv/bin/pip install -r backend/requirements.txt

makemigrations:
	cd backend && ../backend/venv/bin/alembic revision --autogenerate -m "$(msg)"

migrate:
	cd backend && ../backend/venv/bin/alembic upgrade head

run-backend:
	cd backend && ../backend/venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ── Frontend ──────────────────────────────────────────────────────────────────

install-frontend:
	cd frontend && npm install

run-frontend:
	cd frontend && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	docker compose -f infra/docker-compose.yml up -d

docker-down:
	docker compose -f infra/docker-compose.yml down

docker-logs:
	docker compose -f infra/docker-compose.yml logs -f
