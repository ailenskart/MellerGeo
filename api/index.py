"""Vercel serverless entrypoint for MELLER Geo Intelligence API."""

import sys
from pathlib import Path

# Make backend package importable from the Vercel function root.
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: F401 — Vercel ASGI entrypoint
