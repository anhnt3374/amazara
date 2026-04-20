---
doc_type: index
tags: [routing, task-map, workflows]
---

# Task Map

Use this file when you have a concrete task. Each entry lists the exact files to read, in order.

## Setup & First Run

**Task:** Set up the project from scratch
1. `docs/shared/setup.md` — env, docker, makefile commands
2. `docs/shared/architecture.md` — understand the monorepo

---

## Add a New API Endpoint

**Task:** Create a new backend feature (model + CRUD + route)
1. `docs/features/backend/flows.md` — 7-step checklist
2. `docs/features/database/schema.md` — understand FK conventions
3. `docs/features/backend/overview.md` — layer responsibilities (if unclear)

---

## Add a New Database Table

**Task:** Create a new model and migrate
1. `docs/features/database/schema.md` — existing tables + FK pattern
2. `docs/features/backend/flows.md` — migration workflow

---

## Work on Authentication

**Task:** Understand, debug, or extend auth
1. `docs/features/auth/overview.md` — JWT, password hashing, key files
2. `docs/features/auth/flows.md` — login/register/logout/session-restore flows
3. `docs/features/auth/api.md` — endpoint reference + how to call protected endpoints

---

## Work on Orders / Checkout

**Task:** Understand, debug, or extend the order flow
1. `docs/features/orders/overview.md` — data model, statuses, key files
2. `docs/features/orders/flows.md` — cart → checkout → placed; disabled affordances
3. `docs/features/orders/api.md` — endpoint reference

---

## Work on Frontend Pages / Routing

**Task:** Add a page, modify routing, or change route guards
1. `docs/features/frontend/overview.md` — pages, routes, guards
2. `docs/features/auth/flows.md` — ProtectedRoute / GuestRoute behavior

---

## Work on Frontend Styling / Components

**Task:** Add or modify UI components, Tailwind styles, Header
1. `docs/features/frontend/conventions.md` — Tailwind v4, clsx, Header state, proxy
2. `docs/features/frontend/overview.md` — component inventory

---

## Debug Auth on Frontend

**Task:** Session not restoring, redirect loops, token issues
1. `docs/features/auth/flows.md` — session bootstrap, route guard logic
2. `docs/features/auth/overview.md` — token strategy, localStorage key

---

## Debug Auth on Backend

**Task:** 401 errors, JWT decode fails, password mismatch
1. `docs/features/auth/overview.md` — password hashing, `get_current_user`
2. `docs/features/auth/api.md` — endpoint behavior

---

## Debug Migration / Alembic Issues

**Task:** Migration not applying, empty versions dir, downgrade needed
1. `docs/features/backend/flows.md` — migration workflow, two-step rule, manual commands

---

## Seed Mock Data

**Task:** Populate the database with test data for development
1. `docs/shared/setup.md` — seed commands and run order

---

## Understand Project Conventions

**Task:** Language rules, naming, patterns, model/schema/CRUD structure
1. `docs/shared/conventions.md` — cross-feature rules (language, API prefix)
2. `docs/features/backend/overview.md` — backend-specific patterns
3. `docs/features/frontend/conventions.md` — frontend-specific patterns
