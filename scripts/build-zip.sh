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
import configparser
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
    "CREDITS.en.md",
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
            # Entrada de diretório com a barra final: o importador do Krita
            # procura "hq_tools/" para achar o módulo; sem ela, ele responde
            # "No plugins found in archive" (o erro que aparecia ao importar
            # os ZIPs até a 0.12.2).
            arquivo.write(raiz, raiz)
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
        "hq_tools/",
        "hq_tools/__init__.py",
        "hq_tools.desktop",
        "hq_tools.action",
        "hq_tools/LICENSE",
        "hq_tools/CREDITS.md",
        "hq_tools/CREDITS.en.md",
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

    # Espelha a busca do importador do Krita (plugin_importer.py): acha os
    # .desktop, lê o X-KDE-Library e exige a entrada "<nome>/" com
    # "<nome>/__init__.py" dentro. É o contrato que garante o "Importar
    # plugin Python" funcionando; sem ele o build quebra.
    def modulo_do_importador(namelist, nome):
        for candidato in namelist:
            if candidato.endswith("/%s/" % nome) or candidato == "%s/" % nome:
                if ("%s__init__.py" % candidato) in namelist:
                    return candidato
        return None

    desktops = sorted(n for n in contigo if n.endswith(".desktop"))
    if not desktops:
        sys.stderr.write(
            "erro: o ZIP não tem arquivo .desktop; o Krita não acharia o plugin.\n"
        )
        sys.exit(1)
    for desktop in desktops:
        parser = configparser.ConfigParser()
        parser.read_string(arquivo.read(desktop).decode("utf-8"))
        nome = parser["Desktop Entry"].get("X-KDE-Library", "")
        modulo = modulo_do_importador(arquivo.namelist(), nome) if nome else None
        if not modulo:
            sys.stderr.write(
                "erro: o importador do Krita não acharia o módulo '{0}' no ZIP "
                "(falta a entrada de diretório '{0}/' com '{0}/__init__.py').\n".format(
                    nome or "?"
                )
            )
            sys.exit(1)
        print("importador do Krita: ok ({0} -> {1})".format(desktop, modulo))
PY

echo "ZIP gerado: $DIST/$NAME"