#!/usr/bin/env bash
set -euo pipefail
CONTROLLER_URL="${1:-${CONTROLLER_URL:-http://192.168.1.100:8080}}"
DISPLAY_ID="${DISPLAY_ID:-Garage}"
BROWSER="$(command -v chromium || command -v chromium-browser || true)"
if [[ -z "$BROWSER" ]]; then echo "Chromium is required"; exit 1; fi
exec "$BROWSER" --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble "${CONTROLLER_URL}/display?display_id=${DISPLAY_ID}"
