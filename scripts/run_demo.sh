#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=. uvicorn backend.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
npm run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

printf '\nARRIVA demo services started\n'
printf 'Dashboard:       http://localhost:5173/\n'
printf 'Station display: http://localhost:5173/station-display?train_id=ARRIVA-11017\n'
printf 'API docs:         http://127.0.0.1:8000/docs\n\n'
printf 'Press Ctrl+C to stop both services.\n'
wait
