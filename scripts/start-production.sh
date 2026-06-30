#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Building frontend..."
cd frontend
npm ci
npm run build

echo "Copying frontend build to backend/static..."
rm -rf "$ROOT/backend/static"
cp -r dist "$ROOT/backend/static"

echo "Starting production server on port ${PORT:-8000}..."
cd "$ROOT/backend"
source .venv/bin/activate 2>/dev/null || true
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
