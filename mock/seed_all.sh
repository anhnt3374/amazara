#!/usr/bin/env bash
# Full re-seed pipeline.
#
# 1. Reset schema: downgrade to base, upgrade to head.
# 2. Validate image URLs in products.json → products_clean.json (skipped
#    if products_clean.json already exists — delete it to force re-check).
# 3. Seed in dependency order. Orders are intentionally skipped until the
#    order UI lands.
#
# Run from repo root: bash mock/seed_all.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/backend/venv/bin"
PY="$VENV/python"
ALEMBIC="$VENV/alembic"

if [ ! -x "$PY" ]; then
  echo "ERROR: $PY not found. Run 'make venv && make install-backend' first."
  exit 1
fi

echo "[1/9] Resetting schema..."
(cd backend && "$ALEMBIC" downgrade base)
(cd backend && "$ALEMBIC" upgrade head)

echo "[2/9] Validating product image URLs..."
if [ ! -f mock/products_clean.json ]; then
  "$PY" mock/validate_products.py
else
  echo "  mock/products_clean.json already exists — skipping."
fi

echo "[3/9] Seeding users..."
"$PY" mock/seed_users.py

echo "[4/9] Seeding addresses..."
"$PY" mock/seed_addresses.py

echo "[5/9] Seeding stores..."
"$PY" mock/seed_stores.py

echo "[6/9] Seeding products..."
"$PY" mock/seed_products.py

echo "[7/9] Seeding reviews..."
"$PY" mock/seed_reviews.py

echo "[8/9] Seeding cart items..."
"$PY" mock/seed_cart_items.py

echo "[9/9] Seeding favorites..."
"$PY" mock/seed_favorites.py

echo
echo "Done. Orders were intentionally skipped."
