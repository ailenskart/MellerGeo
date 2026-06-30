#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Meller Geo Intelligence Setup ==="

# Backend
echo "Setting up backend..."
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python train_model.py

# Frontend
echo "Setting up frontend..."
cd "$ROOT/frontend"
npm install --silent

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Start backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "Start frontend: cd frontend && npm run dev"
echo "Open:           http://localhost:5173"
