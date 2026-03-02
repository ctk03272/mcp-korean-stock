#!/bin/sh
set -eu

APP_ROOT="$1"
OUTPUT_PATH="$2"

mkdir -p "$(dirname "$OUTPUT_PATH")"

sed \
  -e "s|__APP_ROOT__|$APP_ROOT|g" \
  -e "s|__PYTHON_BIN__|$APP_ROOT/current/.venv/bin/python|g" \
  "$APP_ROOT/current/deploy/launchd/com.ctk03272.mcp-korean-stock.plist" > "$OUTPUT_PATH"
