"""Extrai a pose de um FBX animado (ou de um .blend) para o JSON do 3D.

O FBX precisa carregar a pose numa ação (keyframes); um FBX só com a pose
"no viewport" sai igual ao repouso, como já aconteceu. O ``.blend`` é aceito
como entrada para o caso de a pose só existir no arquivo do Blender. O script
roda dentro do Blender, lê a pose avaliada no frame pedido, calcula a rotação
local de cada osso em relação ao repouso e converte para os valores semânticos
do docker (Dobrar/Abrir/Girar), usando o mesmo mapa do núcleo (``modelo3d``).

``--parte`` recorta a saída: ``corpo`` tira os ossos de mão, ``maos`` deixa só
eles (para a biblioteca separada de mãos e corpo). As poses de mão são
autorais para a mão direita; o docker espelha para a esquerda.

Uso:
    blender -b --factory-startup --python scripts/exportar-poses3d.py -- \
        pose.fbx poses/corpo/idle.json [--frame 1] [--nome Idle] \
        [--parte corpo|maos|tudo]
"""

import json
import os
import sys

import bpy

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d  # noqa: E402

PREFIXOS_MAO = ("hand", "index", "middle", "pinky", "ring", "thumb")
PARTES = ("corpo", "maos", "tudo")
MODELO_PADRAO = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "modelos", "homem.json"
)


def _osso_de_mao(nome):
    """Ossos da mão: dedos, punho e as bases da palma (``index1_base``...)."""
    return nome.split(".")[0].startswith(PREFIXOS_MAO)


def _nomes_do_modelo():
    """Nomes de osso do modelo do plugin (o alvo das poses)."""
    try:
        with open(MODELO_PADRAO, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return set()
    return {osso["nome"] for osso in dados.get("ossos", [])}


def _escolher_armadura(armaduras, nomes_modelo):
    """Com mais de uma armadura no arquivo, fica com a do rig do modelo.

    Alguns FBX trazem o metarig junto do rig de controle (um com centenas de
    ossos auxiliares); a escolha é a que mais compartilha nomes com o modelo.
    """
    if len(armaduras) == 1:
        return armaduras[0]
    def comuns(armadura):
        return len({osso.name for osso in armadura.data.bones} & nomes_modelo)
    escolhida = max(armaduras, key=comuns)
    print(
        "aviso: {0} armaduras; usando '{1}' ({2} ossos do modelo)".format(
            len(armaduras), escolhida.name, comuns(escolhida)
        )
    )
    return escolhida


def _argumentos():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    frame = None
    nome = None
    parte = "tudo"
    if "--frame" in argv:
        posicao = argv.index("--frame")
        frame = int(argv[posicao + 1])
        del argv[posicao:posicao + 2]
    if "--nome" in argv:
        posicao = argv.index("--nome")
        nome = argv[posicao + 1]
        del argv[posicao:posicao + 2]
    if "--parte" in argv:
        posicao = argv.index("--parte")
        parte = argv[posicao + 1]
        del argv[posicao:posicao + 2]
    if parte not in PARTES:
        raise SystemExit("--parte aceita: {0}".format(", ".join(PARTES)))
    if len(argv) < 2:
        raise SystemExit(
            "uso: blender -b --factory-startup --python scripts/exportar-poses3d.py "
            "-- pose.fbx saida.json [--frame 1] [--nome idle] [--parte corpo|maos|tudo]"
        )
    return argv[0], argv[1], frame, nome, parte


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
    entrada, saida, frame, nome, parte = _argumentos()

    if entrada.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=entrada)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=entrada)

    armaduras = [objeto for objeto in bpy.data.objects if objeto.type == "ARMATURE"]
    if not armaduras:
        raise SystemExit("nenhuma armadura no arquivo")
    nomes_modelo = _nomes_do_modelo()
    armadura = _escolher_armadura(armaduras, nomes_modelo)

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
        if nomes_modelo and nome_osso not in nomes_modelo:
            # Fora do modelo do plugin: osso de controle ou de outro rig.
            continue
        if parte == "corpo" and _osso_de_mao(nome_osso):
            continue
        if parte == "maos" and not _osso_de_mao(nome_osso):
            continue
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
        "pose3d: {0} ossos com rotação no frame {1} (parte {2}) -> {3}".format(
            len(valores), frame, parte, saida
        )
    )


main()
