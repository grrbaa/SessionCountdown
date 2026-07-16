#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROLLER_FILE="$ROOT/.display_controller"
NAME_FILE="$ROOT/.display_name"

if [[ -f "$CONTROLLER_FILE" ]]; then
  CONTROLLER="$(tr -d '\r\n' < "$CONTROLLER_FILE")"
else
  read -rp "Controller IP or hostname: " CONTROLLER
  printf '%s\n' "$CONTROLLER" > "$CONTROLLER_FILE"
fi

if [[ -f "$NAME_FILE" ]]; then
  DISPLAY_NAME="$(tr -d '\r\n' < "$NAME_FILE")"
else
  read -rp "Display name [Garage]: " DISPLAY_NAME
  DISPLAY_NAME="${DISPLAY_NAME:-Garage}"
  printf '%s\n' "$DISPLAY_NAME" > "$NAME_FILE"
fi

ENCODED_NAME="${DISPLAY_NAME// /%20}"
URL="http://${CONTROLLER}:8080/display?display_id=${ENCODED_NAME}"
CHROMIUM="$(command -v chromium || command -v chromium-browser || true)"

if [[ -z "$CHROMIUM" ]]; then
  echo "Chromium is not installed. Run scripts/install_display_pi.sh first."
  exit 1
fi

unclutter -idle 0.5 -root >/dev/null 2>&1 &
exec "$CHROMIUM" --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble "$URL"
