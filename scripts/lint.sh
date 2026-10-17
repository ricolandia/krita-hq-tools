#!/usr/bin/env bash
# Lint local igual ao do CI: recria o venv em /tmp quando preciso e usa a
# versão fixada do ruff (o mesmo pin do tests.yml).
#
# Rodar ANTES de todo push — foi o portão que faltou em 17/10, quando três
# chaves duplicadas no i18n_en.py passaram e o job `lint` do CI ficou
# vermelho em todos os pushes seguintes.
#
# Uso:
#   scripts/lint.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${HQ_LINT_VENV:-/tmp/opencode/venv-lint}"
RUFF="${RUFF_VERSION:-0.17.0}"

if [ ! -x "$VENV/bin/ruff" ]; then
    echo "criando o venv do ruff em $VENV..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet "ruff==$RUFF"
fi

cd "$REPO"
"$VENV/bin/ruff" check hq_tools scripts tests
echo "lint ok (ruff $("$VENV/bin/ruff" --version | awk '{print $2}'))"
