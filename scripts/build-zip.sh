#!/usr/bin/env bash
# Gera o ZIP instalável pelo Krita (Ferramentas > Scripts > Importar plugin Python).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$REPO/hq_tools/core/version.py")"
DIST="$REPO/dist"
NAME="hq_tools-${VERSION}.zip"

mkdir -p "$DIST"
rm -f "$DIST/$NAME"

cd "$REPO"
zip -r "$DIST/$NAME" \
    hq_tools \
    hq_tools.desktop \
    hq_tools_manual.html \
    -x '*/__pycache__/*' '*.pyc' >/dev/null

echo "ZIP gerado: $DIST/$NAME"
