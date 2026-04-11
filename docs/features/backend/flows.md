---
feature: backend
doc_type: flows
tags: [new-endpoint, migration, alembic, crud, router]
---

# Backend — Flows

## Adding a New API Endpoint

Follow these steps in order:

1. **Model** — Create `backend/app/models/<name>.py`
   - Inherit `Base`, `UUIDMixin`
   - Define columns and relationships

2. **Register model** — Add import to `backend/app/db/base.py`
   - Required so SQLAlchemy resolves the mapper before first request

3. **Schema** — Create `backend/app/schemas/<name>.py`
   - Pydantic v2 models for request body + response shape

4. **CRUD** — Create `backend/app/crud/<name>.py`
   - Plain functions accepting `db: Session`
   - No class-based repository pattern

5. **Router** — Create `backend/app/api/v1/endpoints/<name>.py`
   - FastAPI `APIRouter`
   - Import CRUD functions and schemas
   - Use `Depends(get_db)` for session, `Depends(get_current_user)` for auth

6. **Register router** — Add to `backend/app/api/v1/router.py`
   ```python
   from app.api.v1.endpoints import <name>
   api_router.include_router(<name>.router, prefix="/<name>", tags=["<name>"])
   ```

7. **Migrate** — Two steps, always in order:
   ```bash
   make makemigrations msg="add_<name>"
   make migrate
   ```

## Migration Workflow

**Always two steps:**
```bash
make makemigrations msg="describe_change"   # creates alembic/versions/<id>_describe_change.py
make migrate                                # applies it: alembic upgrade head
```

Running `make migrate` on an empty `alembic/versions/` does nothing — always generate the migration file first.

**Manual Alembic commands** (from `backend/` with venv active):
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## CORS

`main.py` configures CORS to allow `http://localhost:5173` (Vite dev server). Add production origins to the `allow_origins` list before deploying.
