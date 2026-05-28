#!/usr/bin/env bash
set -euo pipefail

# Start Breathe ESG with Podman
# Run: bash podman-start.sh

NETWORK="breathe-esg"
PG_IMAGE="docker.io/library/postgres:15-alpine"
BACKEND_IMAGE="localhost/breathe-esg_backend:latest"
FRONTEND_IMAGE="localhost/breathe-esg_frontend:latest"

PG_PORT="${DB_PORT:-5432}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

# Create network if needed
if ! podman network exists "$NETWORK" 2>/dev/null; then
    echo "Creating network: $NETWORK"
    podman network create "$NETWORK"
fi

# Clean up any existing containers
for name in postgres backend frontend; do
    podman rm -f "$name" 2>/dev/null || true
done

# --- PostgreSQL ---
echo "Starting PostgreSQL..."
podman run -d \
    --name postgres \
    --network "$NETWORK" \
    --restart unless-stopped \
    -e POSTGRES_DB="${DB_NAME:-breathe_esg}" \
    -e POSTGRES_USER="${DB_USER:-postgres}" \
    -e POSTGRES_PASSWORD="${DB_PASSWORD:-postgres}" \
    -e POSTGRES_INITDB_ARGS="--encoding=UTF8" \
    -p "$PG_PORT:5432" \
    -v "pg_data:/var/lib/postgresql/data" \
    --health-cmd "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-breathe_esg}" \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 5 \
    --health-start-period 10s \
    "$PG_IMAGE"

echo "Waiting for PostgreSQL to become healthy..."
for i in $(seq 1 30); do
    sleep 2
    status=$(podman inspect postgres --format '{{.State.Health.Status}}' 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ]; then
        echo "PostgreSQL is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: PostgreSQL did not become healthy in time"
        podman logs postgres
        exit 1
    fi
done

# --- Backend ---
echo "Starting Backend..."
podman run -d \
    --name backend \
    --network "$NETWORK" \
    --restart unless-stopped \
    -e "DEBUG=${DEBUG:-False}" \
    -e "SECRET_KEY=${SECRET_KEY:-django-insecure-change-this-in-production}" \
    -e "DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@postgres:5432/${DB_NAME:-breathe_esg}" \
    -e "DB_NAME=${DB_NAME:-breathe_esg}" \
    -e "DB_USER=${DB_USER:-postgres}" \
    -e "DB_PASSWORD=${DB_PASSWORD:-postgres}" \
    -e "DB_HOST=postgres" \
    -e "DB_PORT=5432" \
    -e "ALLOWED_HOSTS=localhost,127.0.0.1,backend,0.0.0.0" \
    -e "CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80,http://localhost" \
    -e "CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80,http://localhost" \
    -p "$BACKEND_PORT:8000" \
    "$BACKEND_IMAGE"

echo "Waiting for Backend to become healthy..."
for i in $(seq 1 60); do
    sleep 2
    status=$(podman inspect backend --format '{{.State.Status}}' 2>/dev/null || echo "starting")
    if [ "$status" = "running" ]; then
        echo "Backend is running!"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "ERROR: Backend did not start in time"
        podman logs backend
        exit 1
    fi
done

# --- Frontend ---
echo "Starting Frontend..."
podman run -d \
    --name frontend \
    --network "$NETWORK" \
    --restart unless-stopped \
    -p "$FRONTEND_PORT:80" \
    "$FRONTEND_IMAGE"

echo "============================================"
echo "All services started!"
echo "  Frontend:   http://localhost:$FRONTEND_PORT"
echo "  Backend:    http://localhost:$BACKEND_PORT"
echo "  PostgreSQL: localhost:$PG_PORT"
echo "============================================"
echo ""
echo "To stop: podman rm -f postgres backend frontend"
