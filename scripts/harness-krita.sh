#!/usr/bin/env bash
# Roda um script Python dentro do Krita real, sem tela (xvfb), para smoke/QA.
#
# O molde fica aqui no repositório; os arquivos de execução (estrutura XDG,
# log, stdout) ficam em $HQ_HARNESS_DIR (padrão /tmp/opencode/hq-harness),
# recriados a cada rodada de propósito: estado limpo, nada acumula no repo.
#
# Uso:
#   scripts/harness-krita.sh <script.py> [log]
#
# O script roda com o Krita pronto: o harness põe o repositório no sys.path,
# então é só importar hq_tools. Convenção: acumule o resultado em
# HQ_HARNESS_LOG (o caminho vem no ambiente) e NÃO encerre o Krita — o
# harness encerra ao terminar. Diálogos (QInputDialog) travam: chame os
# internos dos dockers em vez dos handlers que abrem diálogo.
#
# Krita: $KRITA_BIN, senão ~/APP/APPIMAGE/krita.appimage, senão o Krita 6,
# senão `krita` no PATH. Timeout: $HQ_HARNESS_TIMEOUT (padrão 180 s);
# exit 124 = o timeout matou o app (normal, o log já foi escrito).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="${1:?uso: harness-krita.sh <script.py> [log]}"
LOG="${2:-/tmp/opencode/harness-krita.log}"

KRITA_BIN="${KRITA_BIN:-}"
if [ -z "$KRITA_BIN" ]; then
    for candidato in "$HOME/APP/APPIMAGE/krita.appimage" \
                     "$HOME/APP/krita-6.0.4-x86_64.AppImage"; do
        if [ -x "$candidato" ]; then
            KRITA_BIN="$candidato"
            break
        fi
    done
fi
if [ -z "$KRITA_BIN" ]; then
    KRITA_BIN="$(command -v krita || true)"
fi
if [ -z "$KRITA_BIN" ]; then
    echo "Krita não encontrado; defina KRITA_BIN" >&2
    exit 1
fi

BASE="${HQ_HARNESS_DIR:-/tmp/opencode/hq-harness}"
rm -rf "$BASE"
mkdir -p "$BASE/data/krita/pykrita/hq_harness" "$BASE/config"

cat > "$BASE/data/krita/pykrita/hq_harness.desktop" <<'EOF'
[Desktop Entry]
Type=Service
ServiceTypes=Krita/PythonPlugin
X-KDE-Library=hq_harness
Name=HQ Harness
EOF

cat > "$BASE/data/krita/pykrita/hq_harness/__init__.py" <<'EOF'
"""Runner do harness: executa HQ_HARNESS_SCRIPT dentro do Krita e sai."""
import os
import runpy
import sys
import traceback

LOG = os.environ.get("HQ_HARNESS_LOG", "/tmp/opencode/harness-krita.log")


def _rodar():
    try:
        sys.path.insert(0, os.environ["HQ_HARNESS_REPO"])
        runpy.run_path(os.environ["HQ_HARNESS_SCRIPT"])
    except Exception:
        with open(LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write("ERRO:\n" + traceback.format_exc() + "\n")
    from krita import Krita

    Krita.instance().quit()


try:  # Krita 5 usa PyQt5; o Krita 6, PyQt6.
    from PyQt5.QtCore import QTimer
except ImportError:
    from PyQt6.QtCore import QTimer

QTimer.singleShot(2000, _rodar)
EOF

cat > "$BASE/config/kritarc" <<'EOF'
[python]
enable_hq_harness=true
EOF

rm -f "$LOG"
export HQ_HARNESS_LOG="$LOG" HQ_HARNESS_REPO="$REPO" HQ_HARNESS_SCRIPT="$SCRIPT"

XDG_DATA_HOME="$BASE/data" XDG_CONFIG_HOME="$BASE/config" \
    timeout "${HQ_HARNESS_TIMEOUT:-180}" xvfb-run -a "$KRITA_BIN" \
    > "$BASE/stdout.log" 2>&1 || true  # 124 = timeout normal

echo "log: $LOG"
if [ -f "$LOG" ]; then
    cat "$LOG"
else
    echo "(sem log; stdout em $BASE/stdout.log)" >&2
    exit 1
fi
