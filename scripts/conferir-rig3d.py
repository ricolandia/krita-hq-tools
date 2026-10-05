#!/usr/bin/env python3
"""Confere se um modelo 3D novo pode substituir o atual sem perder as poses.

As poses guardam valores semânticos (Dobrar/Abrir/Girar) por NOME de osso, e
o mapeamento de cada nome para um eixo do osso sai da orientação de repouso
(matriz) de cada osso. Trocar a malha por uma mais leve com o MESMO rig
(nomes, hierarquia e orientação de repouso) mantém tudo; se a orientação de
algum osso mudar, as poses saem diferentes naquele osso (foi o que aconteceu
entre `homem.json` e `mulher.json` em 4 ossos: shoulder e thumb1).

Uso:
    python3 scripts/conferir-rig3d.py [--referencia ARQ] [--candidato ARQ]

Sem argumentos, compara o modelo de referência com o outro modelo embarcado.
Sai com código 1 quando a troca não é segura.
"""

import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from hq_tools.core import modelo3d  # noqa: E402

MODELOS = os.path.join(RAIZ, "hq_tools", "modules", "viewer3d", "modelos")
PADRAO = os.path.join(MODELOS, "homem.json")


def carregar(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def comparar(referencia, candidato):
    """Diferenças entre dois modelos, do ponto de vista das poses.

    Devolve ``(faltando, extras, pais, mapas, maior_delta)``: nomes de osso
    que faltam/sobram, ossos cujo pai mudou, ossos cujo mapeamento semântico
    mudou e a maior diferença absoluta numa matriz de repouso (informativa).
    """
    ossos_ref = {osso["nome"]: osso for osso in referencia.get("ossos", [])}
    ossos_cand = {osso["nome"]: osso for osso in candidato.get("ossos", [])}
    faltando = sorted(set(ossos_ref) - set(ossos_cand))
    extras = sorted(set(ossos_cand) - set(ossos_ref))

    def nome_do_pai(lista, indice):
        if indice is None:
            return None
        if 0 <= indice < len(lista):
            return lista[indice]["nome"]
        return "?"

    pais_ref = {
        osso["nome"]: nome_do_pai(referencia.get("ossos", []), osso.get("pai"))
        for osso in referencia.get("ossos", [])
    }
    pais_cand = {
        osso["nome"]: nome_do_pai(candidato.get("ossos", []), osso.get("pai"))
        for osso in candidato.get("ossos", [])
    }
    pais = sorted(
        nome
        for nome in set(ossos_ref) & set(ossos_cand)
        if pais_ref[nome] != pais_cand[nome]
    )

    mapas = []
    maior_delta = 0.0
    for nome in sorted(set(ossos_ref) & set(ossos_cand)):
        osso_ref = ossos_ref[nome]
        osso_cand = ossos_cand[nome]
        mapa_ref = modelo3d.eixos_semanticos(osso_ref)
        mapa_cand = modelo3d.eixos_semanticos(osso_cand)
        if mapa_ref != mapa_cand:
            mapas.append((nome, mapa_ref, mapa_cand))
        for valor_ref, valor_cand in zip(osso_ref["matriz"], osso_cand["matriz"]):
            maior_delta = max(maior_delta, abs(valor_ref - valor_cand))
    return faltando, extras, pais, mapas, maior_delta


def relatar(caminho_ref, caminho_cand):
    referencia = carregar(caminho_ref)
    candidato = carregar(caminho_cand)
    faltando, extras, pais, mapas, maior_delta = comparar(referencia, candidato)

    print("referência: {0}".format(os.path.basename(caminho_ref)))
    print("candidato:  {0}".format(os.path.basename(caminho_cand)))
    print("osso(a)s:", len(referencia.get("ossos", [])), "->",
          len(candidato.get("ossos", [])))
    print("malha: {0} vértices / {1} faces -> {2} / {3}".format(
        len(referencia.get("vertices", [])), len(referencia.get("faces", [])),
        len(candidato.get("vertices", [])), len(candidato.get("faces", [])),
    ))
    print("maior diferença numa matriz de repouso: {0:.4f}".format(maior_delta))

    problemas = []
    if faltando:
        problemas.append("ossos que faltam: {0}".format(", ".join(faltando)))
    if extras:
        problemas.append("ossos a mais: {0}".format(", ".join(extras)))
    if pais:
        problemas.append("pai diferente: {0}".format(", ".join(pais)))
    if mapas:
        problemas.append(
            "mapeamento semântico diferente ({0}): {1}".format(
                len(mapas), ", ".join(nome for nome, _, _ in mapas)
            )
        )
        for nome, mapa_ref, mapa_cand in mapas:
            print("  {0}: {1} -> {2}".format(nome, mapa_ref, mapa_cand))

    if problemas:
        print("\nTROCA NÃO É SEGURA:")
        for problema in problemas:
            print("- {0}".format(problema))
        print(
            "\nAs poses guardadas valem por nome de osso e pela orientação de "
            "repouso. Para a troca ser segura, o rig novo precisa manter nomes, "
            "hierarquia e orientação (mesmo rest, mesmos rolls)."
        )
        return 1
    print("\nTroca segura para as poses: nomes, hierarquia e orientação batem.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--referencia", default=PADRAO)
    parser.add_argument("--candidato", default=None)
    opcoes = parser.parse_args(argv)
    candidato = opcoes.candidato
    if candidato is None:
        candidato = os.path.join(MODELOS, "mulher.json")
    return relatar(opcoes.referencia, candidato)


if __name__ == "__main__":
    raise SystemExit(main())
