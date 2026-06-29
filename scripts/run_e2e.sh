#!/usr/bin/env bash
# Run the REST API e2e suite against a real stack.
# Brings up Postgres + Qdrant via compose, launches the backend with a
# deterministic fake embedder (no OpenRouter key needed), waits for health,
# runs `pytest -m e2e`, and tears everything down on exit.
#
# Usage: ./scripts/run_e2e.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

BASE_URL="http://localhost:8000"
UVICORN_PID=""

cleanup() {
    if [ -n "$UVICORN_PID" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
        echo "=== Stopping backend (pid $UVICORN_PID) ==="
        kill "$UVICORN_PID" 2>/dev/null || true
        wait "$UVICORN_PID" 2>/dev/null || true
    fi
    echo "=== Stopping db + qdrant ==="
    (cd "$ROOT_DIR" && docker compose stop db qdrant >/dev/null 2>&1) || true
}
trap cleanup EXIT

echo "=== Stopping any compose backend/frontend (frees port 8000) ==="
(cd "$ROOT_DIR" && docker compose stop backend frontend >/dev/null 2>&1) || true

echo "=== Starting db + qdrant ==="
(cd "$ROOT_DIR" && docker compose up -d db qdrant)

echo "=== Waiting for db + qdrant to be healthy ==="
for _ in $(seq 1 60); do
    db_ok=$(cd "$ROOT_DIR" && docker compose ps db --format '{{.Health}}' 2>/dev/null || echo "")
    qd_ok=$(cd "$ROOT_DIR" && docker compose ps qdrant --format '{{.Health}}' 2>/dev/null || echo "")
    if [ "$db_ok" = "healthy" ] && [ "$qd_ok" = "healthy" ]; then
        break
    fi
    sleep 1
done

if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    echo "ERROR: something is already serving $BASE_URL — stop it before running e2e" >&2
    exit 1
fi

echo "=== Launching backend (fake embedder, localhost deps) ==="
(
    cd "$BACKEND_DIR"
    USE_FAKE_EMBEDDER=true \
    POSTGRES_HOST=localhost \
    QDRANT_URL=http://localhost:6333 \
        uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
) &
UVICORN_PID=$!

echo "=== Waiting for backend health ==="
healthy=0
for _ in $(seq 1 60); do
    if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
        healthy=1
        break
    fi
    sleep 1
done
if [ "$healthy" -ne 1 ]; then
    echo "ERROR: backend did not become healthy" >&2
    exit 1
fi

echo "=== Running e2e tests ==="
(cd "$BACKEND_DIR" && E2E_BASE_URL="$BASE_URL" uv run pytest tests/e2e -m e2e -v)
