#!/usr/bin/env python3
"""Gera os conjuntos de linhas de perspectiva do HQ Tools.

O núcleo (geometria e montagem do SVG) vive em
``hq_tools/modules/perspectiva/linhas.py``; aqui fica só a linha de comando
que grava os assets versionados em ``hq_tools/resources/perspectivas/``.

Uso:
    python3 scripts/gerar-perspectivas.py [--destino DIR] [--largura N] [--altura N] [--listar]
"""

import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.modules.perspectiva import linhas  # noqa: E402

DESTINO_PADRAO = os.path.join(RAIZ, "hq_tools", "resources", "perspectivas")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", default=DESTINO_PADRAO)
    parser.add_argument("--largura", type=int, default=900)
    parser.add_argument("--altura", type=int, default=1200)
    parser.add_argument("--listar", action="store_true")
    opcoes = parser.parse_args(argv)
    if opcoes.listar:
        for arquivo, titulo, _, legenda in linhas.PRESETS:
            print("{0}: {1} | {2}".format(arquivo, titulo, legenda))
        return 0
    for caminho in linhas.gerar_todos(opcoes.destino, opcoes.largura, opcoes.altura):
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
