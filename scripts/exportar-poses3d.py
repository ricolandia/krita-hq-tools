"""Extrai a pose de um FBX animado para o JSON do visualizador 3D.

O FBX precisa carregar a pose numa ação (keyframes); um FBX só com a pose
"no viewport" sai igual ao repouso, como já aconteceu. O script roda dentro do
Blender, lê a pose avaliada no frame pedido, calcula a rotação local de cada
osso em relação ao repouso e converte para os valores semânticos do docker
(Dobrar/Abrir/Girar), usando o mesmo mapa do núcleo (``modelo3d``).

Uso:
    blender -b --factory-startup --python scripts/exportar-poses3d.py -- \
        pose.fbx poses/idle.json [--frame 1] [--nome idle]
"""

import json
import os
import sys

import bpy

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d  # noqa: E402


def _argumentos():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    frame = None
    nome = None
    if "--frame" in argv:
        posicao = argv.index("--frame")
        frame = int(argv[posicao + 1])
        del argv[posicao:posicao + 2]
    if "--nome" in argv:
        posicao = argv.index("--nome")
        nome = argv[posicao + 1]
        del argv[posicao:posicao + 2]
    if len(argv) < 2:
        raise SystemExit(
            "uso: blender -b --factory-startup --python scripts/exportar-poses3d.py "
            "-- pose.fbx saida.json [--frame 1] [--nome idle]"
        )
    return argv[0], argv[1], frame, nome


def _matriz_lista(matriz):
    return [float(valor) for linha in matriz for valor in linha]


def _ossos_em_ordem(armadura):
    ordem = []
    visitados = set()

    def visitar(osso):
        if osso.name in visitados:
            return
        if osso.parent is not None:
            visitar(osso.parent)
        visitados.add(osso.name)
        ordem.append(osso)

    for osso in armadura.data.bones:
        visitar(osso)
    return ordem


def main():
    entrada, saida, frame, nome = _argumentos()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=entrada)

    armaduras = [objeto for objeto in bpy.data.objects if objeto.type == "ARMATURE"]
    if len(armaduras) != 1:
        raise SystemExit("esperava 1 armadura; achei {0}".format(len(armaduras)))
    armadura = armaduras[0]

    if frame is None:
        frame = bpy.context.scene.frame_start
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    ossos = _ossos_em_ordem(armadura)
    indice = {osso.name: posicao for posicao, osso in enumerate(ossos)}
    repouso = {osso.name: osso.matrix_local.copy() for osso in ossos}
    posed = {osso.name: armadura.pose.bones[osso.name].matrix.copy() for osso in ossos}

    valores = {}
    for osso in ossos:
        nome_osso = osso.name
        if osso.parent is None:
            local_repouso = repouso[nome_osso]
            local_pose = posed[nome_osso]
        else:
            pai = osso.parent.name
            local_repouso = repouso[pai].inverted() @ repouso[nome_osso]
            local_pose = posed[pai].inverted() @ posed[nome_osso]
        delta = local_repouso.inverted() @ local_pose
        euler = delta.to_euler("XYZ")
        rotacao = (
            float(euler.x) * 57.29577951308232,
            float(euler.y) * 57.29577951308232,
            float(euler.z) * 57.29577951308232,
        )
        mapa = modelo3d.eixos_semanticos(
            {"nome": nome_osso, "matriz": _matriz_lista(repouso[nome_osso])}
        )
        entrada_pose = {}
        for chave, (eixo, sinal) in mapa.items():
            valor = rotacao[modelo3d.EIXOS[eixo]] * sinal
            if abs(valor) > 0.1:
                entrada_pose[chave] = round(valor, 2)
        if entrada_pose:
            valores[nome_osso] = entrada_pose

    documento = {
        "formato": "hq_tools.pose3d",
        "versao": 1,
        "nome": nome or os.path.splitext(os.path.basename(saida))[0],
        "ossos": valores,
    }
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False, separators=(",", ":"))
    print(
        "pose3d: {0} ossos com rotação no frame {1} -> {2}".format(
            len(valores), frame, saida
        )
    )


main()
