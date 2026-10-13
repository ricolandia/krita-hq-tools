#!/usr/bin/env python3
"""Renderiza prévias das poses do 3D para QA (corpo + mãos combinados).

Monta a mesma combinação do docker (corpo + as duas mãos, cada uma com a
própria pose) e chama o ``preview-modelo3d.py`` para gerar o SVG; com o
cairosvg instalado, converte para PNG (o QA de visão lê PNG).

Sem argumentos, renderiza o conjunto todo: cada pose de corpo e cada pose de
mão combinada com o Idle (na direita e nas duas mãos). Para um caso só:

    python3 scripts/preview-poses3d.py --corpo voa --mao-direita segura --mao-esquerda fechada

Com ``--galeria``, gera os ícones do seletor de poses do docker:
``hq_tools/resources/poses-preview/{corpo,maos}/<pose>.png`` (corpo na
câmera padrão; mãos em close na mão direita, a autoral). Rodar quando uma
pose entrar ou mudar; o teste da galeria acusa se ficar fora de sincronia.

Uso:
    python3 scripts/preview-poses3d.py [--saida-dir DIR] [--corpo NOME]
        [--mao-direita NOME] [--mao-esquerda NOME] [--zoom N] [--yaw GRAUS]
        [--so-svg] [--galeria]
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
    RESOURCES_DIR,
    VIEWER3D_MODELOS,
    VIEWER3D_POSES_CORPO_DIR,
    VIEWER3D_POSES_MAOS_DIR,
)

# Galeria dos ícones do seletor: o corpo usa o enquadramento padrão da vista
# (yaw 0, pitch -10) fechando o quadro com ~6 px de margem; as mãos usam um
# close na mão direita (a autoral; o docker espelha na aplicação) com o braço
# levantado ao lado, para a mão sair da silhueta do corpo e o fundo ficar
# limpo (o antebraço entra pela borda, natural). Calibrar/recalibrar com
# ``scripts/calibrar-galeria-poses3d.py`` (mudou o rig ou as poses).
TAMANHO_GALERIA = (120, 160)
CAMERA_GALERIA_CORPO = {"yaw": 0.0, "pitch": -10.0, "zoom": 1.708, "pan_x": 1.8, "pan_y": -0.3}
CAMERA_GALERIA_MAOS = {"yaw": -15.0, "pitch": -10.0, "zoom": 11.142, "pan_x": 356.7, "pan_y": 362.5}
ABRIR_MAO_GALERIA = 70.0


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


def _galeria():
    """Gera os ícones do seletor de poses em ``resources/poses-preview``."""
    try:
        import cairosvg
    except ImportError:
        print("cairosvg é necessário para a galeria (pip install cairosvg)")
        return 1
    modelo = modelo3d.Modelo.carregar(VIEWER3D_MODELOS[0][2])
    largura, altura = TAMANHO_GALERIA
    destino = os.path.join(RESOURCES_DIR, "poses-preview")
    for parte, camera in (
        ("corpo", CAMERA_GALERIA_CORPO),
        ("maos", CAMERA_GALERIA_MAOS),
    ):
        fonte = VIEWER3D_POSES_CORPO_DIR if parte == "corpo" else VIEWER3D_POSES_MAOS_DIR
        saida = os.path.join(destino, parte)
        os.makedirs(saida, exist_ok=True)
        for arquivo in _listar(fonte):
            if parte == "corpo":
                semantica = modelo3d.combinar_poses(
                    _ler(fonte, arquivo),
                    _ler(VIEWER3D_POSES_MAOS_DIR, "fechada.json"),
                    _ler(VIEWER3D_POSES_MAOS_DIR, "fechada.json"),
                )
            else:
                semantica = modelo3d.combinar_poses(
                    _ler(VIEWER3D_POSES_CORPO_DIR, "idle.json"),
                    _ler(fonte, arquivo),
                    {},
                )
                # Braço levantado ao lado: a mão sai da silhueta do corpo (que
                # ficaria atrás dela na ortográfica) e o close fica limpo.
                semantica.setdefault("arm_stretch.r", {})["abrir"] = ABRIR_MAO_GALERIA
            posados = modelo.vertices_em_pose(modelo.aplicar_semantica(semantica))
            svg = modelo.renderizar(
                yaw=camera["yaw"],
                pitch=camera["pitch"],
                zoom=camera["zoom"],
                pan_x=camera["pan_x"],
                pan_y=camera["pan_y"],
                largura=largura,
                altura=altura,
                posados=posados,
            )
            png = os.path.join(saida, arquivo[:-5] + ".png")
            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                write_to=png,
                output_width=largura,
                output_height=altura,
            )
            print(png)
    return 0


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
    parser.add_argument(
        "--galeria", action="store_true",
        help="gera os ícones do seletor em resources/poses-preview",
    )
    opcoes = parser.parse_args(argv)

    if opcoes.galeria:
        return _galeria()
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
