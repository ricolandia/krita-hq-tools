#!/usr/bin/env bash
# Instala o ícone do HQ Tools no tema do usuário (hicolor), para o gerenciador
# de plugins e os menus do Krita acharem pelo nome "hq_tools".
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ICONS="${HOME}/.local/share/icons/hicolor"
instalados=0
for size in 16 32 64 128 256 512; do
    origem="$REPO/assets/icon-light-${size}.png"
    [ -f "$origem" ] || continue
    destino="${ICONS}/${size}x${size}/apps"
    mkdir -p "$destino"
    cp -f "$origem" "$destino/hq_tools.png"
    instalados=$((instalados + 1))
done
if [ "$instalados" -eq 0 ]; then
    echo "erro: nenhum PNG de ícone encontrado em assets/" >&2
    exit 1
fi
echo "Ícone hq_tools instalado em ${ICONS} (${instalados} tamanhos)."
echo "Reinicie o Krita para o gerenciador de plugins recarregar o ícone."
