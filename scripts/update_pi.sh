#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git pull origin agent/controller-display-v2
chmod +x scripts/*.sh

echo "SessionCountdown display updated."
