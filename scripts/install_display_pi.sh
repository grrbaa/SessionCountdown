#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y curl unclutter chromium-browser || \
    sudo apt-get install -y curl unclutter chromium
fi

chmod +x "$ROOT/scripts/start_display_pi.sh" "$ROOT/scripts/update_pi.sh"

echo
echo "Raspberry Pi display tools installed."
echo "Run: $ROOT/scripts/start_display_pi.sh"
