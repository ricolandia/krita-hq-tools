"""Renderiza o modelo 3D do HQ Tools em SVG, fora do Krita.

Serve para desenvolvimento e QA visual: gera o mesmo SVG que o docker vai
mostrar, sem abrir o Krita e sem Blender.

Exemplos:
    python3 scripts/preview-modelo3d.py --saida /tmp/repouso.svg
    python3 scripts/preview-modelo3d.py --pose aceno --yaw 30 --saida /tmp/aceno.svg
    python3 scripts/preview-modelo3d.py --rot "arm_stretch.l=0,0,60" --saida /tmp/teste.svg
"""

import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d

MODELO_PADRAO = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "modelos", "homem.json"
)

POSES = {
    "repouso": {},
    "aceno": {
        "arm_stretch.l": (100.0, 0.0, 0.0),
        "forearm_stretch.l": (-55.0, 0.0, 0.0),
        "head.x": (0.0, 0.0, -8.0),
    },
    "bracos_cima": {
        "arm_stretch.l": (100.0, 0.0, 0.0),
        "arm_stretch.r": (100.0, 0.0, 0.0),
    },
    "passo": {
        "thigh_stretch.l": (0.0, 0.0, -30.0),
        "leg_stretch.l": (0.0, 0.0, 15.0),
        "thigh_stretch.r": (0.0, 0.0, -25.0),
        "leg_stretch.r": (0.0, 0.0, -35.0),
        "arm_stretch.l": (0.0, 0.0, 20.0),
        "arm_stretch.r": (0.0, 0.0, 20.0),
    },
    "sentado": {
        "thigh_stretch.l": (0.0, 0.0, -85.0),
        "leg_stretch.l": (0.0, 0.0, 85.0),
        "thigh_stretch.r": (0.0, 0.0, 85.0),
        "leg_stretch.r": (0.0, 0.0, -85.0),
        "arm_stretch.l": (25.0, 0.0, 0.0),
        "arm_stretch.r": (25.0, 0.0, 0.0),
    },
}


def _rotacoes(textos):
    rotacoes = {}
    for texto in textos or []:
        nome, valores = texto.split("=", 1)
        partes = [float(valor) for valor in valores.split(",")]
        if len(partes) != 3:
            raise SystemExit("rotação esperada como nome=rx,ry,rz: {0}".format(texto))
        rotacoes[nome.strip()] = tuple(partes)
    return rotacoes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default=MODELO_PADRAO)
    parser.add_argument("--saida", default="preview-modelo3d.svg")
    parser.add_argument("--pose", choices=sorted(POSES), default="repouso")
    parser.add_argument("--pose-json", default=None, help="arquivo de pose (hq_tools.pose3d)")
    parser.add_argument("--rot", action="append", help="rotação avulsa: osso=rx,ry,rz")
    parser.add_argument("--yaw", type=float, default=0.0)
    parser.add_argument("--pitch", type=float, default=-10.0)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--largura", type=int, default=700)
    parser.add_argument("--altura", type=int, default=700)
    parser.add_argument("--cor", default=None)
    parser.add_argument("--fundo", default=None)
    parser.add_argument(
        "--estilo", choices=("sombreado", "chapado", "contorno"), default="sombreado"
    )
    argumentos = parser.parse_args()

    modelo = modelo3d.Modelo.carregar(argumentos.modelo)
    rotacoes = dict(POSES[argumentos.pose])
    if argumentos.pose_json:
        pose = modelo3d.carregar_pose(argumentos.pose_json)
        rotacoes.update(modelo.aplicar_semantica(pose["ossos"]))
    rotacoes.update(_rotacoes(argumentos.rot))

    svg = modelo.renderizar(
        rotacoes,
        yaw=argumentos.yaw,
        pitch=argumentos.pitch,
        zoom=argumentos.zoom,
        largura=argumentos.largura,
        altura=argumentos.altura,
        cor=argumentos.cor,
        fundo=argumentos.fundo,
        estilo=argumentos.estilo,
    )
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(svg)
    print("pose '{0}': {1} rotações -> {2}".format(argumentos.pose, len(rotacoes), argumentos.saida))


if __name__ == "__main__":
    main()
