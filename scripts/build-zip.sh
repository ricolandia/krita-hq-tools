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
# O plugin em si, o .desktop e o .action.
itens = ["hq_tools", "hq_tools.desktop", "hq_tools.action"]
# Licença e créditos acompanham o ZIP: sem eles o pacote redistribui fontes de
# terceiros (13 fontes sob OFL, brushes de packs comunitários) sem a obrigação
# de declarar autoria e licença. A INSTALL.md também vai, porque é o passo a
# passo da instalação manual que o autor lê no celular, sem acesso ao GitHub.
documentos = ["LICENSE", "CREDITS.md", "README.md", "CHANGELOG.md", "INSTALL.md"]
faltando = [nome for nome in documentos if not os.path.isfile(nome)]
if faltando:
    sys.stderr.write(
        "aviso: {0} não entrou no ZIP (licença/créditos).\n".format(", ".join(faltando))
    )
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
    for nome in documentos:
        if os.path.isfile(nome):
            arquivo.write(nome, os.path.join("hq_tools", nome))
PY

echo "ZIP gerado: $DIST/$NAME"