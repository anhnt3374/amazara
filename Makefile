.PHONY: help \
        venv install-backend install-frontend \
        makemigrations migrate \
        run-backend run-frontend \
        docker-up docker-down docker-logs \
        seed

help:
	@echo "Backend"
	@echo "  make venv                  Create virtual environment at backend/venv"
	@echo "  make install-backend       Install Python packages from requirements.txt"
	@echo "  make makemigrations msg=x  Generate Alembic migration file from models"
	@echo "  make migrate               Apply pending migrations to the database"
	@echo "  make run-backend           Run FastAPI dev server (port 8000)"
	@echo ""
	@echo "Frontend"
	@echo "  make install-frontend      Install Node packages (npm install)"
	@echo "  make run-frontend          Run Vite dev server (port 5173)"
	@echo ""
	@echo "Docker"
	@echo "  make docker-up             Start MySQL + Milvus"
	@echo "  make docker-down           Stop Docker services"
	@echo "  make docker-logs           View Docker service logs"
	@echo ""
	@echo "Data"
	@echo "  make seed                  Reset schema + validate + re-run all seeds"

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

# ── Data ──────────────────────────────────────────────────────────────────────

seed:
	bash mock/seed_all.sh
