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
documentos = [
    "LICENSE",
    "CREDITS.md",
    "README.md",
    "README.en.md",
    "CHANGELOG.md",
    "INSTALL.md",
    "INSTALL.en.md",
]
faltando = [nome for nome in documentos if not os.path.isfile(nome)]
if faltando:
    # Falha, e não aviso: o ZIP redistribui fontes de terceiros (13 fontes sob
    # OFL, brushes de packs comunitários) e sair sem a licença e os créditos é
    # distribuir sem declarar autoria. Melhor o build quebrar.
    sys.stderr.write(
        "erro: {0} não existe; o ZIP não pode sair sem licença e créditos.\n".format(
            ", ".join(faltando)
        )
    )
    sys.exit(1)
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
        arquivo.write(nome, os.path.join("hq_tools", nome))

    # Confere o que o Krita vai encontrar depois de importar: o .desktop e o
    # .action na raiz, o pacote com __init__.py e a licença dentro.
    contigo = set(arquivo.namelist())
    obrigatorios = {
        "hq_tools/__init__.py",
        "hq_tools.desktop",
        "hq_tools.action",
        "hq_tools/LICENSE",
        "hq_tools/CREDITS.md",
    }
    faltando = sorted(obrigatorios - contigo)
    if faltando:
        sys.stderr.write("erro: faltou no ZIP: {0}\n".format(", ".join(faltando)))
        sys.exit(1)
    tem_cache = [n for n in contigo if "__pycache__" in n or n.endswith(".pyc")]
    if tem_cache:
        sys.stderr.write(
            "erro: cache de Python entrou no ZIP ({0}).\n".format(tem_cache[0])
        )
        sys.exit(1)
PY

echo "ZIP gerado: $DIST/$NAME"