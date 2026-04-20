#!/usr/bin/env bash
# Full re-seed pipeline.
#
# 1. Reset schema: downgrade to base, upgrade to head.
# 2. Validate image URLs in products.json → products_clean.json (skipped
#    if products_clean.json already exists — delete it to force re-check).
# 3. Seed in dependency order.
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

echo "[1/10] Resetting schema..."
(cd backend && "$ALEMBIC" downgrade base)
(cd backend && "$ALEMBIC" upgrade head)

echo "[2/10] Validating product image URLs..."
if [ ! -f mock/products_clean.json ]; then
  "$PY" mock/validate_products.py
else
  echo "  mock/products_clean.json already exists — skipping."
fi

echo "[3/10] Seeding users..."
"$PY" mock/seed_users.py

echo "[4/10] Seeding addresses..."
"$PY" mock/seed_addresses.py

echo "[5/10] Seeding stores..."
"$PY" mock/seed_stores.py

echo "[6/10] Seeding products..."
"$PY" mock/seed_products.py

echo "[7/10] Seeding reviews..."
"$PY" mock/seed_reviews.py

echo "[8/10] Seeding cart items..."
"$PY" mock/seed_cart_items.py

echo "[9/10] Seeding favorites..."
"$PY" mock/seed_favorites.py

echo "[10/10] Seeding orders..."
"$PY" mock/seed_orders.py

echo
echo "Done."
