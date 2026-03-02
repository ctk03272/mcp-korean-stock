#!/bin/sh
set -eu

APP_ROOT="$1"
ENV_FILE="$APP_ROOT/shared/.env"
PYTHON_BIN="$APP_ROOT/current/.venv/bin/python"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing environment file: $ENV_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

exec "$PYTHON_BIN" -m korean_stock_mcp.server
