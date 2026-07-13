#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -m uvicorn session_countdown.main:app --host 0.0.0.0 --port "${PORT:-8080}"
