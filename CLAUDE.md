# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Language

All code, comments, error messages, UI strings, API responses, and documentation must be written in **English**.

## Development Commands

All commands run from the **project root** via Makefile:

```bash
make venv                       # Create backend/venv
make install-backend            # pip install into venv
make makemigrations msg=<name>  # Generate Alembic migration file
make migrate                    # Apply pending migrations
make run-backend                # uvicorn on :8000
make install-frontend           # npm install in frontend/
make run-frontend               # Vite dev server on :5173
make docker-up                  # Start MySQL + Milvus
make docker-down                # Stop Docker services
```

Backend commands run via `backend/venv/bin/` — never assume a globally activated venv.

## Documentation

Feature knowledge lives in `/docs/`. Always read docs before modifying a feature area.

### How to find relevant docs

1. **Start with the index:** Read `docs/index/feature-map.md` to map your question to a feature.
2. **For a concrete task:** Read `docs/index/task-map.md` for the exact reading order.
3. **Read only what is needed** — 2–4 files is the target. Do not scan all of `/docs/`.

### Docs structure

```
docs/
├── index/
│   ├── feature-map.md    ← keyword → feature → files to read
│   └── task-map.md       ← task → ordered reading list
├── features/
│   ├── auth/             overview, api, flows
│   ├── backend/          overview, flows
│   ├── database/         overview, schema
│   └── frontend/         overview, conventions
└── shared/
    ├── architecture.md   monorepo layout, ports
    ├── conventions.md    language, naming, patterns
    └── setup.md          install, env, docker, makefile
```

### How to update docs

- One file = one purpose. Do not mix flows + API + notes in a single file.
- When adding a new feature: create `docs/features/<name>/overview.md` at minimum, then `api.md` / `flows.md` as needed.
- Update `docs/index/feature-map.md` to add the new feature's keywords and file pointers.
- Update `docs/index/task-map.md` if the new feature introduces a common workflow.
- Keep files under ~300 lines. Split if they grow beyond that.
- Add frontmatter to every doc file:
  ```
  ---
  feature: <name>
  doc_type: overview | api | flows | schema | conventions | architecture | setup | index
  tags: [keyword1, keyword2]
  ---
  ```

## Quality Rules

- Do not add features, refactor, or "improve" code beyond what was asked.
- Do not add error handling for impossible cases — trust framework guarantees.
- Do not create helpers for one-time operations.
- Do not delete information from docs unless it is clearly redundant with content already moved elsewhere.
