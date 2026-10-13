#!/usr/bin/env python3
"""Calibra as câmeras da galeria de prévias das poses (ícones do seletor).

Calcula, a partir do rig e das poses do repositório, o enquadramento que
fecha o quadro com ~6 px de margem em cada grupo: corpo = todas as poses de
corpo (mãos fechadas); mãos = todas as poses de mão (com o braço levantado ao
lado, para a mão sair da silhueta do corpo). Imprime os dicionários prontos
para colar em ``preview-poses3d.py``; rodar quando o rig ou as poses mudarem.

Uso:
    python3 scripts/calibrar-galeria-poses3d.py
"""

import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d  # noqa: E402
from hq_tools.core.paths import (  # noqa: E402
    VIEWER3D_MODELOS,
    VIEWER3D_POSES_CORPO_DIR,
    VIEWER3D_POSES_MAOS_DIR,
)

LARGURA, ALTURA = 120, 160
YAW_CORPO, YAW_MAOS, PITCH = 0.0, -15.0, -10.0
MARGEM = 6.0
ABRIR_MAO = 70.0


def _ler(pasta, nome):
    with open(os.path.join(pasta, nome), encoding="utf-8") as arquivo:
        return json.load(arquivo)["ossos"]


def _indices_da_mao(modelo):
    achados = []
    for i, pares in enumerate(modelo.pesos):
        for osso_indice, peso in pares:
            nome = modelo.ossos[osso_indice]["nome"]
            if modelo3d.osso_de_mao(nome) and nome.endswith(".r") and peso > 0.5:
                achados.append(i)
                break
    return achados


def _tela(modelo, pontos, zoom, pan_x, pan_y, yaw):
    visao, centro, escala, distancia = modelo._camera(
        yaw, PITCH, zoom, LARGURA, ALTURA, pan_x, pan_y, lente=None
    )
    na_camera = [modelo3d.aplicar_ponto(visao, ponto) for ponto in pontos]
    return modelo._projetar(
        na_camera, centro, escala, distancia, LARGURA, ALTURA, pan_x, pan_y
    )


def _calibrar(modelo, casos, yaw, indices=None):
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for semantica in casos:
        posados = modelo.vertices_em_pose(modelo.aplicar_semantica(semantica))
        pontos = posados if indices is None else [posados[i] for i in indices]
        tela = _tela(modelo, pontos, 1.0, 0.0, 0.0, yaw)
        xs = [ponto[0] for ponto in tela]
        ys = [ponto[1] for ponto in tela]
        x0, x1 = min(x0, min(xs)), max(x1, max(xs))
        y0, y1 = min(y0, min(ys)), max(y1, max(ys))
    zoom = round(
        min((LARGURA - 2 * MARGEM) / (x1 - x0), (ALTURA - 2 * MARGEM) / (y1 - y0)),
        3,
    )
    # zoom escala o deslocamento em relação ao centro do quadro.
    cx = ((x0 + x1) / 2.0 - LARGURA / 2.0) * zoom + LARGURA / 2.0
    cy = ((y0 + y1) / 2.0 - ALTURA / 2.0) * zoom + ALTURA / 2.0
    pan = (round(LARGURA / 2.0 - cx, 1), round(ALTURA / 2.0 - cy, 1))
    return (
        '{"yaw": %.1f, "pitch": %.1f, "zoom": %.3f, "pan_x": %.1f, "pan_y": %.1f}'
        % (yaw, PITCH, zoom, pan[0], pan[1])
    )


def main():
    modelo = modelo3d.Modelo.carregar(VIEWER3D_MODELOS[0][2])
    corpo = _ler(VIEWER3D_POSES_CORPO_DIR, "idle.json")
    fechada = _ler(VIEWER3D_POSES_MAOS_DIR, "fechada.json")

    casos_corpo = [
        modelo3d.combinar_poses(
            _ler(VIEWER3D_POSES_CORPO_DIR, nome), fechada, fechada
        )
        for nome in sorted(os.listdir(VIEWER3D_POSES_CORPO_DIR))
        if nome.endswith(".json")
    ]
    print("CAMERA_GALERIA_CORPO =", _calibrar(modelo, casos_corpo, YAW_CORPO))

    casos_maos = []
    for nome in sorted(os.listdir(VIEWER3D_POSES_MAOS_DIR)):
        if not nome.endswith(".json"):
            continue
        semantica = modelo3d.combinar_poses(
            corpo, _ler(VIEWER3D_POSES_MAOS_DIR, nome), {}
        )
        semantica.setdefault("arm_stretch.r", {})["abrir"] = ABRIR_MAO
        casos_maos.append(semantica)
    print(
        "CAMERA_GALERIA_MAOS =",
        _calibrar(modelo, casos_maos, YAW_MAOS, indices=_indices_da_mao(modelo)),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
