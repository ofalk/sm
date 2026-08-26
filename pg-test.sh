#!/bin/bash
# Run the test suite against PostgreSQL inside a rootless podman container,
# mirroring CI (which uses a postgres sidecar).
#
# Usage:
#   ./pg-test.sh                                  # full test discovery
#   ./pg-test.sh --tag=browser                    # any manage.py test args
#   ./pg-test.sh servermodel clustersoftware      # or specific modules
#   ./pg-test.sh --down                           # stop and remove the container
set -euo pipefail

NAME=sm-pg-test
PORT=5433
URL="postgresql://sm_user:sm_password@localhost:${PORT}/sm_db"

if [[ "${1:-}" == "--down" ]]; then
  podman rm -f "$NAME" >/dev/null
  echo "Removed container $NAME."
  exit 0
fi

if ! podman container exists "$NAME"; then
  echo "Starting PostgreSQL container $NAME (port $PORT)..."
  podman run -d --name "$NAME" \
    -e POSTGRES_DB=sm_db \
    -e POSTGRES_USER=sm_user \
    -e POSTGRES_PASSWORD=sm_password \
    -p "${PORT}:5432" \
    docker.io/library/postgres:latest >/dev/null
elif [[ "$(podman inspect -f '{{.State.Running}}' "$NAME")" != "true" ]]; then
  podman start "$NAME" >/dev/null
fi

echo "Waiting for PostgreSQL..."
until podman exec "$NAME" pg_isready -U sm_user >/dev/null 2>&1; do
  sleep 1
done

ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

cd "$ROOT/sm"
echo "Running tests against $URL"
DATABASE_URL="$URL" \
  SECRET_KEY="${SECRET_KEY:-local-test-secret-key}" \
  DEBUG=False \
  ALLOWED_HOSTS='*' \
  "$PYTHON" manage.py test "$@"
