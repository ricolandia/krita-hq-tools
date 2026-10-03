"""Exporta um FBX (malha + armadura + pesos) para o JSON do visualizador 3D.

O FBX é binário: o Python do Krita não lê esse arquivo. Este script roda dentro
do Blender, importa **apenas o FBX** (o .blend de origem não é usado) e grava o
JSON que o plugin consome em tempo de execução. O Blender entra só na conversão.

Uso:
    blender -b --factory-startup --python scripts/exportar-modelo3d.py -- \
        entrada.fbx saida.json

O JSON tem o formato ``hq_tools.modelo3d`` versão 1:
- ``ossos``: nome, pai e matriz de repouso no espaço do mundo (16 floats,
  linha por linha), em ordem de hierarquia (pai antes do filho);
- ``vertices``: posições de repouso no espaço do mundo;
- ``pesos``: até 4 pares (índice do osso, peso) por vértice, normalizados;
- ``faces``: índices dos vértices de cada polígono.
"""

import json
import sys

import bpy


def _argumentos():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    if len(argv) < 2:
        raise SystemExit(
            "uso: blender -b --factory-startup --python scripts/exportar-modelo3d.py "
            "-- entrada.fbx saida.json"
        )
    return argv[0], argv[1]


def _matriz_lista(matriz):
    return [float(valor) for linha in matriz for valor in linha]


def _ossos_em_ordem(armadura):
    """Devolve os ossos com os pais antes dos filhos (ordem topológica)."""
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
    entrada, saida = _argumentos()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=entrada)

    malhas = [
        objeto
        for objeto in bpy.data.objects
        if objeto.type == "MESH" and len(objeto.data.polygons) > 0
    ]
    armaduras = [objeto for objeto in bpy.data.objects if objeto.type == "ARMATURE"]
    if len(malhas) != 1 or len(armaduras) != 1:
        raise SystemExit(
            "esperava 1 malha com polígonos e 1 armadura; achei {0} e {1}".format(
                len(malhas), len(armaduras)
            )
        )
    malha, armadura = malhas[0], armaduras[0]

    ossos = _ossos_em_ordem(armadura)
    indice_do_osso = {osso.name: indice for indice, osso in enumerate(ossos)}
    matriz_da_armadura = armadura.matrix_world
    dados_ossos = []
    for osso in ossos:
        pai = indice_do_osso.get(osso.parent.name) if osso.parent is not None else None
        dados_ossos.append(
            {
                "nome": osso.name,
                "pai": pai,
                "matriz": _matriz_lista(matriz_da_armadura @ osso.matrix_local),
            }
        )

    grupo_para_osso = {}
    for grupo in malha.vertex_groups:
        if grupo.name in indice_do_osso:
            grupo_para_osso[grupo.index] = indice_do_osso[grupo.name]

    matriz_da_malha = malha.matrix_world
    dados_vertices = []
    dados_pesos = []
    for vertice in malha.data.vertices:
        mundo = matriz_da_malha @ vertice.co
        dados_vertices.append([round(mundo.x, 6), round(mundo.y, 6), round(mundo.z, 6)])
        pares = []
        for elemento in vertice.groups:
            osso = grupo_para_osso.get(elemento.group)
            if osso is not None and elemento.weight > 0.0:
                pares.append((elemento.weight, osso))
        pares.sort(reverse=True)
        pares = pares[:4]
        total = sum(peso for peso, _ in pares)
        if total > 0.0:
            dados_pesos.append(
                [[osso, round(peso / total, 6)] for peso, osso in pares]
            )
        else:
            dados_pesos.append([])

    dados_faces = [list(poligono.vertices) for poligono in malha.data.polygons]

    documento = {
        "formato": "hq_tools.modelo3d",
        "versao": 1,
        "nome": malha.name,
        "cor_padrao": "#d8c3b0",
        "ossos": dados_ossos,
        "vertices": dados_vertices,
        "pesos": dados_pesos,
        "faces": dados_faces,
    }

    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False, separators=(",", ":"))

    sem_peso = sum(1 for pares in dados_pesos if not pares)
    print(
        "modelo3d: {0} ossos, {1} vertices, {2} faces, {3} sem peso -> {4}".format(
            len(dados_ossos), len(dados_vertices), len(dados_faces), sem_peso, saida
        )
    )


main()
