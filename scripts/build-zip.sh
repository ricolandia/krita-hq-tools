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
python3 - "$DIST/$NAME" <<'PY'
import os
import sys
import zipfile

out = sys.argv[1]
itens = ["hq_tools", "hq_tools.desktop", "hq_tools.action"]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as arquivo:
    for item in itens:
        if os.path.isfile(item):
            arquivo.write(item, item)
            continue
        for raiz, dirs, nomes in os.walk(item):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in nomes:
                if nome.endswith((".pyc", ".pyo")):
                    continue
                caminho = os.path.join(raiz, nome)
                arquivo.write(caminho, caminho)
PY

echo "ZIP gerado: $DIST/$NAME"