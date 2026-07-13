#!/usr/bin/env bash
#
# Launch the Accessibility Automator backend (FastAPI) and frontend (Vite) for
# local dev on macOS / Linux. The bash counterpart of run_server.ps1.
#
#   Backend:  uvicorn backend.app.main:app --reload   (http://localhost:8000)
#   Frontend: npm run dev                             (http://localhost:5173)
#
# Both run in THIS terminal (backgrounded); press Ctrl+C once to stop both.
#
# By default the backend runs through `uv run` (which self-heals the project
# .venv for the current OS — handy in a OneDrive folder shared with Windows).
# If you keep your own Mac venv (e.g. ~/.venvs/accessibility-automator),
# activate it and pass --no-uv to run uvicorn/alembic/python directly.
#
# First-time setup (deps, migrate, seed the admin) runs only with --setup.
#
# Usage:
#   ./run_server.sh                                      # start both servers
#   ./run_server.sh --setup --admin-email you@temple.edu # first-time setup, then start
#   ./run_server.sh --no-uv                              # use the activated venv
#
set -euo pipefail

ADMIN_EMAIL="you@temple.edu"
DO_SETUP=0
USE_UV=1

usage() { grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup) DO_SETUP=1; shift ;;
    --admin-email) ADMIN_EMAIL="${2:?--admin-email needs a value}"; shift 2 ;;
    --no-uv) USE_UV=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND="$ROOT/frontend"
[[ -d "$FRONTEND" ]] || { echo "frontend folder not found at $FRONTEND" >&2; exit 1; }

# Backend command prefix: "uv run" or empty (use the activated venv directly).
if [[ $USE_UV -eq 1 ]]; then PY=(uv run); else PY=(); fi

if [[ $DO_SETUP -eq 1 ]]; then
  echo "== First-time setup =="
  if [[ $USE_UV -eq 1 ]]; then
    echo "[backend] uv sync"
    ( cd "$ROOT" && uv sync )
  fi
  echo "[backend] alembic upgrade head"
  ( cd "$ROOT" && "${PY[@]}" alembic upgrade head )
  echo "[backend] seeding admin ($ADMIN_EMAIL)"
  ( cd "$ROOT" && "${PY[@]}" python -m backend.app.seed --admin "$ADMIN_EMAIL" )
  echo "[frontend] npm install"
  ( cd "$FRONTEND" && npm install )
  echo "== Setup complete =="
fi

echo "Starting backend  -> http://localhost:8000"
( cd "$ROOT" && exec "${PY[@]}" uvicorn backend.app.main:app --reload ) &
BACK_PID=$!

echo "Starting frontend -> http://localhost:5173"
( cd "$FRONTEND" && exec npm run dev ) &
FRONT_PID=$!

cleanup() {
  echo ""
  echo "Stopping servers..."
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
  wait "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo ""
echo "Both servers running. Open http://localhost:5173 and use the 'Local dev login'"
echo "box with a registered email (e.g. $ADMIN_EMAIL)."
echo "Press Ctrl+C to stop both."
wait
