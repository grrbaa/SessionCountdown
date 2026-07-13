#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-pip curl chromium-browser avahi-daemon || \
    sudo apt-get install -y python3 python3-venv python3-pip curl chromium avahi-daemon
fi

python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt"

chmod +x "$ROOT/scripts/start_pi.sh" "$ROOT/scripts/start_kiosk.sh"

sudo systemctl enable --now avahi-daemon 2>/dev/null || true

echo
echo "SessionCountdown installed."
echo "Start server:  $ROOT/scripts/start_pi.sh"
echo "Start display: $ROOT/scripts/start_kiosk.sh"
echo "Controller:    http://session-countdown.local:8080/"
echo "Display:       http://session-countdown.local:8080/display"
