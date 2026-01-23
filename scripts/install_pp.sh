#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-$HOME/.local/bin}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/../pp.py"

mkdir -p "$TARGET_DIR"
cp "$SOURCE" "$TARGET_DIR/pp"
chmod +x "$TARGET_DIR/pp"
printf "Installed pp to %s/pp\n" "$TARGET_DIR"
