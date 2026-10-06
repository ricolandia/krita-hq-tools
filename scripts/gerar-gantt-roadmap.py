#!/usr/bin/env python3
"""Gera o canvas Excalidraw do roadmap (nota "Roadmap em Gantt" no Trilium).

O canvas é um JSON do Excalidraw com uma linha do tempo de 6 semanas (1 dia =
80 px), barras por tarefa e uma legenda. Para atualizar o roadmap, edite as
listas ``TAREFAS`` e ``FEITO`` aqui e rode de novo.

Uso:
    python3 scripts/gerar-gantt-roadmap.py [--saida ARQUIVO] [--enviar]

Sem ``--enviar``, só grava o JSON e imprime o comando de envio. Com
``--enviar``, faz o PUT na nota do Trilium usando ``TRILIUM_URL`` e
``TRILIUM_TOKEN`` (via ``env_hermes``/``~/.hermes/.env``).
"""

import argparse
import json
import os
import random
import sys
import time
import uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

NOTA_PADRAO = "8RHlNinCFSzc"  # "Roadmap em Gantt (Excalidraw)" no Trilium

# Cores da legenda
COR_PRIORIDADE = "#ffc9c9"
COR_FUNDACAO = "#a5d8ff"
COR_RAPIDO = "#b2f2bb"
COR_MEDIO = "#ffec99"
COR_NEUTRO = "#e9ecef"

TITULO = "Roadmap HQ Tools"
SUBTITULO = "Reavaliado em 05/10/2026 - prioridade: salvar pose, miniatura e joinha"
FEITO = "Feito: v0.1 a v0.9 (módulos base, pincéis, 3D, hub, perspectiva, PT/EN)"
PRIORIDADE = "Prioridade: o que falta das poses"
FORA_DO_ROADMAP = (
    "Fora do roadmap original (já feito): UI compartilhada, ícone/social preview, "
    "vídeos demo, CI Windows,\nautomação de release, auditorias (30/09 e 05/10) e "
    "documentação no Trilium."
)

# (rótulo, dia inicial, dia final, cor, duração)
TAREFAS = (
    ("Biblioteca de poses: corpo/mãos e espelho (feito)", 1, 7, COR_RAPIDO, "feito"),
    ("Validação no Krita da v0.9.0 (hub, perspectiva, i18n)", 1, 3, COR_RAPIDO, "3 dias"),
    ("Krita 6: validação e ferramentas novas", 8, 12, COR_FUNDACAO, "5 dias"),
    ("Lettering nas páginas geradas (balões + fontes)", 13, 17, COR_MEDIO, "5 dias"),
    ("Clique direto no canvas (PoC)", 18, 20, COR_RAPIDO, "3 dias"),
    ("Fillbucket em Python puro (sem numpy)", 21, 26, COR_MEDIO, "6 dias"),
    ("Balão paramétrico (pós-Krita 6)", 27, 30, COR_MEDIO, "4 dias"),
    ("Avaliar e decidir (joinha, painel, bundle, exportação)", 24, 30, COR_NEUTRO, "quando der"),
)

DIAS = 30
PIXEL_POR_DIA = 80
SEMANAS = 6

agora = int(time.time() * 1000)
elementos = []
indice = [0]


def proximo_index():
    indice[0] += 1
    return "a{0:02d}".format(indice[0])


def novo_id():
    return uuid.uuid4().hex[:20]


def semente():
    return random.randint(1, 2**31 - 1)


def texto(x, y, w, h, conteudo, tamanho=18, cor="#1e1e1e", alinhamento="left",
          container=None):
    return {
        "id": novo_id(), "type": "text", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": cor, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
        "index": proximo_index(), "roundness": None, "seed": semente(),
        "version": 1, "versionNonce": semente(), "isDeleted": False,
        "boundElements": [], "updated": agora, "link": None, "locked": False,
        "hasTextLink": False, "text": conteudo, "originalText": conteudo,
        "fontSize": tamanho, "fontFamily": 6, "textAlign": alinhamento,
        "verticalAlign": "middle" if container else "top",
        "containerId": container, "autoResize": True, "lineHeight": 1.25,
    }


def barra(x, y, w, h, cor, rotulo, tamanho=15):
    retangulo = {
        "id": novo_id(), "type": "rectangle", "x": x, "y": y, "width": w,
        "height": h, "angle": 0, "strokeColor": "#1e1e1e",
        "backgroundColor": cor, "fillStyle": "hachure", "strokeWidth": 0.5,
        "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "index": proximo_index(),
        "roundness": {"type": 3}, "seed": semente(), "version": 1,
        "versionNonce": semente(), "isDeleted": False, "boundElements": [],
        "updated": agora, "link": None, "locked": False, "hasTextLink": False,
    }
    texto_barra = texto(x, y, w, h, rotulo, tamanho=tamanho, alinhamento="center",
                        container=retangulo["id"])
    retangulo["boundElements"] = [{"type": "text", "id": texto_barra["id"]}]
    elementos.append(retangulo)
    elementos.append(texto_barra)


def montar():
    elementos.append(texto(-430, -290, 1000, 45, TITULO, tamanho=36))
    elementos.append(texto(-430, -226, 1400, 22, SUBTITULO, tamanho=18, cor="#868e96"))
    barra(-430, -170, 900, 40, COR_RAPIDO, FEITO)
    barra(-430, -118, 430, 40, COR_PRIORIDADE, PRIORIDADE)

    for semana in range(SEMANAS):
        barra(semana * 400, -40, 400, 36, COR_NEUTRO,
              "Semana {0}".format(semana + 1), tamanho=20)
    for dia in range(1, DIAS + 1):
        elementos.append(
            texto(30 + (dia - 1) * PIXEL_POR_DIA, 2, 20, 15, str(dia), tamanho=15)
        )

    y = 60
    for rotulo, dia_ini, dia_fim, cor, duracao in TAREFAS:
        elementos.append(texto(-430, y + 9, 400, 22, rotulo, tamanho=18))
        x = (dia_ini - 1) * PIXEL_POR_DIA
        largura = (dia_fim - dia_ini + 1) * PIXEL_POR_DIA
        barra(x, y, largura, 40, cor, duracao)
        y += 72

    elementos.append(texto(-430, y + 26, 90, 18, "Legenda:", tamanho=15))
    for x, cor, rotulo in (
        (-340, COR_PRIORIDADE, "prioridade"),
        (-160, COR_FUNDACAO, "fundação"),
        (20, COR_RAPIDO, "rápido/feito"),
        (200, COR_MEDIO, "médio"),
    ):
        retangulo = {
            "id": novo_id(), "type": "rectangle", "x": x, "y": y + 24,
            "width": 22, "height": 22, "angle": 0, "strokeColor": "#1e1e1e",
            "backgroundColor": cor, "fillStyle": "hachure", "strokeWidth": 0.5,
            "strokeStyle": "solid", "roughness": 0, "opacity": 100,
            "groupIds": [], "frameId": None, "index": proximo_index(),
            "roundness": None, "seed": semente(), "version": 1,
            "versionNonce": semente(), "isDeleted": False, "boundElements": [],
            "updated": agora, "link": None, "locked": False, "hasTextLink": False,
        }
        elementos.append(retangulo)
        elementos.append(texto(x + 30, y + 26, 140, 18, rotulo, tamanho=15))

    barra(-430, y + 74, 2830, 56, COR_NEUTRO, FORA_DO_ROADMAP)


def _do_env(nome):
    """Lê a chave do ``~/.hermes/.env`` (ou do ambiente, se não houver)."""
    caminho = os.path.expanduser("~/.hermes/.env")
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                if chave.strip() == nome:
                    return valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return os.environ.get(nome)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="gantt-roadmap.json")
    parser.add_argument("--nota", default=NOTA_PADRAO)
    parser.add_argument("--enviar", action="store_true")
    opcoes = parser.parse_args(argv)

    montar()
    documento = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elementos,
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }
    with open(opcoes.saida, "w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False)
    print("canvas: {0} elementos -> {1}".format(len(elementos), opcoes.saida))

    if not opcoes.enviar:
        print(
            "para enviar ao Trilium:\n"
            "  curl -X PUT -H \"Authorization: Bearer $TRILIUM_TOKEN\" "
            "-H \"Content-Type: text/plain\" --data-binary @{0} "
            "\"$TRILIUM_URL/etapi/notes/{1}/content\"".format(opcoes.saida, opcoes.nota)
        )
        return 0

    from urllib import request

    url = _do_env("TRILIUM_URL")
    token = _do_env("TRILIUM_TOKEN")
    if not url or not token:
        raise SystemExit("TRILIUM_URL/TRILIUM_TOKEN não definidos (~/.hermes/.env)")
    destino = "{0}/etapi/notes/{1}/content".format(url.rstrip("/"), opcoes.nota)
    with open(opcoes.saida, "rb") as arquivo:
        dados = arquivo.read()
    requisicao = request.Request(
        destino, data=dados, method="PUT",
        headers={"Authorization": "Bearer {0}".format(token),
                 "Content-Type": "text/plain"},
    )
    with request.urlopen(requisicao, timeout=60) as resposta:
        print("Trilium: HTTP {0}".format(resposta.status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
