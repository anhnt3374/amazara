---
doc_type: conventions
tags: [language, api-prefix, english]
---

# Project Conventions — Cross-Feature Rules

These rules apply everywhere in the codebase. Feature-specific conventions live in their own docs.

## Language

All code, comments, error messages, UI strings, API responses, and documentation must be written in **English**. No other language anywhere in the codebase.

## API Versioning

All backend endpoints are mounted under the `/api/v1` prefix.
Router registration is centralised in `backend/app/api/v1/router.py`.
Swagger UI is available at `http://localhost:8000/docs` only when `APP_ENV=development`.

## Feature-Specific Conventions

| Area | Where to read |
|---|---|
| Backend (models, CRUD, schemas, layers) | `docs/features/backend/overview.md` |
| Database (UUIDs, table patterns, migrations) | `docs/features/database/overview.md` |
| Frontend (Tailwind, clsx, routing guards) | `docs/features/frontend/conventions.md` |
