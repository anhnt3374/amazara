.PHONY: help \
        venv install-backend install-frontend \
        makemigrations migrate \
        run-backend run-frontend \
        check-ml-env install-ml-cpu install-ml-gpu reindex \
        seed

help:
	@echo "Backend"
	@echo "  make venv                  Create virtual environment at backend/venv"
	@echo "  make install-backend       Install Python packages from requirements.txt"
	@echo "  make makemigrations msg=x  Generate Alembic migration file from models"
	@echo "  make migrate               Apply pending migrations to Supabase Postgres"
	@echo "  make run-backend           Run FastAPI dev server (port 8000)"
	@echo ""
	@echo "Semantic Search"
	@echo "  make install-ml-gpu        Install PyTorch (CUDA 12.4) and ML deps"
	@echo "  make install-ml-cpu        Install PyTorch (CPU) and ML deps (fallback)"
	@echo "  make check-ml-env          Smoke-test ML stack (loads BGE encoder)"
	@echo "  make reindex               Rebuild Weaviate Cloud collections from Supabase products"
	@echo ""
	@echo "Frontend"
	@echo "  make install-frontend      Install Node packages (npm install)"
	@echo "  make run-frontend          Run Vite dev server (port 5173)"
	@echo ""
	@echo "Data"
	@echo "  make seed                  Reset schema + validate + re-run all seeds"
	@echo ""
	@echo "Note: this branch uses cloud-only services — Supabase Postgres,"
	@echo "Weaviate Cloud, and Redis Cloud. No docker-compose required."

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

# ── Semantic search ───────────────────────────────────────────────────────────

check-ml-env:
	cd backend && ../backend/venv/bin/python scripts/check_ml_env.py

install-ml-cpu:
	backend/venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0+cpu torchvision==0.26.0+cpu
	backend/venv/bin/pip install -r backend/requirements-ml.txt

install-ml-gpu:
	backend/venv/bin/pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.11.0+cu124 torchvision==0.26.0+cu124
	backend/venv/bin/pip install -r backend/requirements-ml.txt

reindex:
	cd backend && ../backend/venv/bin/python scripts/reindex_products.py

# ── Data ──────────────────────────────────────────────────────────────────────

seed:
	bash mock/seed_all.sh
