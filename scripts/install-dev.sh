#!/usr/bin/env bash
# Instala o plugin em modo de desenvolvimento no Krita do usuário.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
PYKRITA="${DATA}/krita/pykrita"
ACTIONS="${DATA}/krita/actions"

mkdir -p "$PYKRITA" "$ACTIONS"

ln -sfn "$REPO/hq_tools" "$PYKRITA/hq_tools"
ln -sfn "$REPO/hq_tools.desktop" "$PYKRITA/hq_tools.desktop"
cp -f "$REPO/hq_tools.action" "$ACTIONS/hq_tools.action"

bash "$REPO/scripts/install-icons.sh"

echo "Plugin instalado em modo de desenvolvimento:"
echo "  $PYKRITA/hq_tools"
echo "  $PYKRITA/hq_tools.desktop"
echo "  $ACTIONS/hq_tools.action"
echo
echo "Abra o Krita, ative em Configurar Krita > Gerenciador de plugins Python"
echo "e reinicie. Os dockers aparecem em Configuracoes > Dockers (HQ Tools)."
