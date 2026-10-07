#!/usr/bin/env python3
"""Renderiza prévias das poses do 3D para QA (corpo + mãos combinados).

Monta a mesma combinação do docker (corpo + as duas mãos, cada uma com a
própria pose) e chama o ``preview-modelo3d.py`` para gerar o SVG; com o
cairosvg instalado, converte para PNG (o QA de visão lê PNG).

Sem argumentos, renderiza o conjunto todo: cada pose de corpo e cada pose de
mão combinada com o Idle (na direita e nas duas mãos). Para um caso só:

    python3 scripts/preview-poses3d.py --corpo voa --mao-direita segura --mao-esquerda fechada

Uso:
    python3 scripts/preview-poses3d.py [--saida-dir DIR] [--corpo NOME]
        [--mao-direita NOME] [--mao-esquerda NOME] [--zoom N] [--yaw GRAUS]
        [--so-svg]
"""

import argparse
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d  # noqa: E402
from hq_tools.core.paths import (  # noqa: E402
    VIEWER3D_POSES_CORPO_DIR,
    VIEWER3D_POSES_MAOS_DIR,
)


def _ler(pasta, nome):
    if not nome.endswith(".json"):
        nome += ".json"
    with open(os.path.join(pasta, nome), encoding="utf-8") as arquivo:
        return json.load(arquivo).get("ossos", {})


def _listar(pasta):
    try:
        return sorted(
            nome for nome in os.listdir(pasta) if nome.endswith(".json")
        )
    except OSError:
        return []


def _montar(corpo, mao_direita, mao_esquerda):
    return modelo3d.combinar_poses(
        _ler(VIEWER3D_POSES_CORPO_DIR, corpo) if corpo else {},
        _ler(VIEWER3D_POSES_MAOS_DIR, mao_direita) if mao_direita else {},
        _ler(VIEWER3D_POSES_MAOS_DIR, mao_esquerda) if mao_esquerda else {},
    )


def _renderizar(corpo, mao_direita, mao_esquerda, saida_dir, zoom, yaw, pitch, so_svg):
    partes = []
    if corpo:
        partes.append(os.path.splitext(corpo)[0])
    if mao_direita:
        partes.append(os.path.splitext(mao_direita)[0] + "-direita")
    if mao_esquerda:
        partes.append(os.path.splitext(mao_esquerda)[0] + "-esquerda")
    nome = "-".join(partes) or "repouso"
    json_saida = os.path.join(saida_dir, nome + ".json")
    svg_saida = os.path.join(saida_dir, nome + ".svg")
    documento = {
        "formato": "hq_tools.pose3d",
        "versao": 1,
        "nome": nome,
        "ossos": _montar(corpo, mao_direita, mao_esquerda),
    }
    with open(json_saida, "w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False)
    comando = [
        sys.executable,
        os.path.join(RAIZ, "scripts", "preview-modelo3d.py"),
        "--pose-json", json_saida,
        "--saida", svg_saida,
        "--zoom", str(zoom),
        "--yaw", str(yaw),
        "--pitch", str(pitch),
    ]
    subprocess.run(comando, check=True)
    if so_svg:
        print(svg_saida)
        return
    try:
        import cairosvg
    except ImportError:
        print(svg_saida, "(cairosvg ausente: só SVG)")
        return
    png_saida = os.path.join(saida_dir, nome + ".png")
    cairosvg.svg2png(
        url=svg_saida, write_to=png_saida, output_width=520,
        background_color="white",
    )
    print(png_saida)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida-dir", default="/tmp/poses-preview")
    parser.add_argument("--corpo", default=None)
    parser.add_argument("--mao-direita", default=None)
    parser.add_argument("--mao-esquerda", default=None)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--yaw", type=float, default=0.0)
    parser.add_argument("--pitch", type=float, default=-10.0)
    parser.add_argument("--so-svg", action="store_true")
    opcoes = parser.parse_args(argv)

    os.makedirs(opcoes.saida_dir, exist_ok=True)
    if opcoes.corpo or opcoes.mao_direita or opcoes.mao_esquerda:
        _renderizar(opcoes.corpo, opcoes.mao_direita, opcoes.mao_esquerda,
                    opcoes.saida_dir, opcoes.zoom, opcoes.yaw, opcoes.pitch,
                    opcoes.so_svg)
        return 0

    for corpo in _listar(VIEWER3D_POSES_CORPO_DIR):
        _renderizar(corpo, None, None, opcoes.saida_dir, opcoes.zoom,
                    opcoes.yaw, opcoes.pitch, opcoes.so_svg)
    for maos in _listar(VIEWER3D_POSES_MAOS_DIR):
        _renderizar("idle.json", maos, None, opcoes.saida_dir, opcoes.zoom,
                    opcoes.yaw, opcoes.pitch, opcoes.so_svg)
        _renderizar("idle.json", maos, maos, opcoes.saida_dir, opcoes.zoom,
                    opcoes.yaw, opcoes.pitch, opcoes.so_svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
