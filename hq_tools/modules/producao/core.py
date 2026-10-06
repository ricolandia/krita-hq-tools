"""Núcleo da produção (checklist do roteiro), sem dependência do Krita.

O checklist é derivado do mesmo texto do roteiro (``pages.roteiro``): cada
página do script vira um nó com os painéis do layout, e cada painel guarda o
estado de produção (esboço -> arte -> final) e as falas/personagens. O
progresso e a meta semanal ficam em ``producao.json`` na pasta do projeto, e o
texto do roteiro em ``roteiro.txt``; as páginas geradas são reconhecidas pelo
nome ``pagina_NNN.kra`` (mesma convenção do gerenciador de páginas).
"""

import json
import os
import re
from datetime import date, timedelta

from ..pages import roteiro

ESTADOS = ("esboco", "arte", "final")
ESTADO_PADRAO = "esboco"
ARQUIVO_ESTADOS = "producao.json"
ARQUIVO_ROTEIRO = "roteiro.txt"
ARQUIVO_CHECKLIST = "checklist.md"
PADRAO_PAGINA = re.compile(r"^pagina_(\d+)\.kra$", re.IGNORECASE)

ROTULOS_PT = {
    "esboco": "Esboço",
    "arte": "Arte",
    "final": "Final",
    "narracao": "Narração",
}

MARCAS = {"final": "[x]", "arte": "[-]", "esboco": "[ ]"}


def proximo_estado(estado):
    """Cicla esboço -> arte -> final -> esboço."""
    if estado not in ESTADOS:
        return ESTADO_PADRAO
    return ESTADOS[(ESTADOS.index(estado) + 1) % len(ESTADOS)]


def chave(pagina, painel):
    """Chave do estado de um painel no producao.json (``"1-2"``)."""
    return "{0}-{1}".format(int(pagina), int(painel))


def montar(texto, estados=None):
    """Checklist (páginas -> painéis) a partir do roteiro, preservando estados."""
    marcados = estados or {}
    checklist = []
    for pagina in roteiro.parse_script(texto):
        paineis = []
        for indice in range(1, len(pagina["panels"]) + 1):
            falas = [fala for fala in pagina["balloons"] if fala["panel"] == indice]
            paineis.append(
                {
                    "painel": indice,
                    "estado": marcados.get(
                        chave(pagina["index"], indice), ESTADO_PADRAO
                    ),
                    "falas": falas,
                }
            )
        checklist.append({"pagina": pagina["index"], "paineis": paineis})
    return checklist


def estados_do_checklist(checklist):
    """Estados no formato do producao.json (só o que está no checklist)."""
    return {
        chave(pagina["pagina"], painel["painel"]): painel["estado"]
        for pagina in checklist
        for painel in pagina["paineis"]
    }


def progresso(checklist):
    """Contagem de painéis por estado (mais ``total`` e ``finais``)."""
    contagem = {"total": 0, "finais": 0, "esboco": 0, "arte": 0, "final": 0}
    for pagina in checklist:
        for painel in pagina["paineis"]:
            estado = painel.get("estado", ESTADO_PADRAO)
            contagem["total"] += 1
            if estado in ESTADOS:
                contagem[estado] += 1
    contagem["finais"] = contagem["final"]
    return contagem


def progresso_da_pagina(pagina):
    """(finais, total) de uma página do checklist."""
    finais = sum(1 for painel in pagina["paineis"] if painel["estado"] == "final")
    return finais, len(pagina["paineis"])


def projecao(restantes, meta_semanal, hoje=None):
    """(semanas, data prevista) para concluir no ritmo da meta; None se pronto."""
    if restantes <= 0:
        return (0, None)
    meta = max(1, int(meta_semanal or 1))
    semanas = (int(restantes) + meta - 1) // meta
    base = hoje or date.today()
    return (semanas, base + timedelta(days=7 * semanas))


def falas_resumo(painel, rotulo_narracao="Narração"):
    """Prévia das falas do painel: ``JOAO: oi · Narração: era uma vez``."""
    partes = []
    for fala in painel.get("falas", []):
        if fala.get("kind") == "narracao":
            prefixo = rotulo_narracao
        else:
            prefixo = fala.get("character") or ""
        texto = fala.get("text", "")
        partes.append("{0}: {1}".format(prefixo, texto) if prefixo else texto)
    return " · ".join(partes)


def para_markdown(checklist, meta_semanal=0, hoje=None, rotulos=None, titulo=None):
    """Checklist em Markdown (para espelhar no Trilium, se quiser)."""
    rotulos = dict(ROTULOS_PT, **(rotulos or {}))
    contagem = progresso(checklist)
    linhas = ["# {0}".format(titulo or "Checklist de produção"), ""]
    linhas.append(
        "- Painéis: {total} · finais: {finais} · em arte: {arte} · em esboço: {esboco}".format(
            **contagem
        )
    )
    if meta_semanal:
        semanas, previsao = projecao(
            contagem["total"] - contagem["finais"], meta_semanal, hoje
        )
        if previsao is not None:
            linhas.append(
                "- Meta: {0} painéis/semana · ~{1} semana(s) · entrega ~{2}".format(
                    int(meta_semanal), semanas, previsao.strftime("%d/%m")
                )
            )
    linhas.append("")
    for pagina in checklist:
        finais, total = progresso_da_pagina(pagina)
        linhas.append(
            "## Página {0}: {1}/{2} finais".format(pagina["pagina"], finais, total)
        )
        for painel in pagina["paineis"]:
            resumo = falas_resumo(painel, rotulos.get("narracao", "Narração"))
            sufixo = " · {0}".format(resumo) if resumo else ""
            linhas.append(
                "- {0} Painel {1} ({2}){3}".format(
                    MARCAS.get(painel["estado"], "[ ]"),
                    painel["painel"],
                    rotulos.get(painel["estado"], painel["estado"]),
                    sufixo,
                )
            )
        linhas.append("")
    return "\n".join(linhas).rstrip() + "\n"


def caminho_estados(pasta):
    return os.path.join(pasta, ARQUIVO_ESTADOS)


def caminho_roteiro(pasta):
    return os.path.join(pasta, ARQUIVO_ROTEIRO)


def carregar(pasta):
    """(estados, meta_semanal) do producao.json; tolerante a arquivo quebrado."""
    try:
        with open(caminho_estados(pasta), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {}, 0
    if not isinstance(dados, dict):
        return {}, 0
    estados = dados.get("estados")
    if not isinstance(estados, dict):
        estados = {}
    estados = {
        str(marcada): valor
        for marcada, valor in estados.items()
        if isinstance(valor, str) and valor in ESTADOS
    }
    try:
        meta = max(0, int(dados.get("meta_semanal", 0)))
    except (TypeError, ValueError):
        meta = 0
    return estados, meta


def _meta_int(valor):
    """Meta como inteiro >= 0 (tolerante a texto vindo de config)."""
    try:
        return max(0, int(valor or 0))
    except (TypeError, ValueError):
        return 0


def salvar(pasta, estados, meta_semanal):
    """Grava o producao.json de forma atômica."""
    caminho = caminho_estados(pasta)
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(
            {
                "estados": dict(estados),
                "meta_semanal": _meta_int(meta_semanal),
            },
            arquivo,
            ensure_ascii=False,
            indent=2,
        )
    os.replace(temporario, caminho)


def carregar_roteiro(pasta):
    """Texto do roteiro salvo na pasta (vazio quando ainda não existe)."""
    try:
        with open(caminho_roteiro(pasta), encoding="utf-8") as arquivo:
            return arquivo.read()
    except OSError:
        return ""


def salvar_roteiro(pasta, texto):
    """Grava o roteiro.txt de forma atômica."""
    caminho = caminho_roteiro(pasta)
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        arquivo.write(str(texto))
    os.replace(temporario, caminho)


def pagina_do_arquivo(pasta, numero):
    """Caminho da ``pagina_NNN.kra`` do número (ou None quando não existe)."""
    try:
        nomes = os.listdir(pasta)
    except OSError:
        return None
    alvo = int(numero)
    for nome in sorted(nomes):
        achado = PADRAO_PAGINA.match(nome)
        if achado and int(achado.group(1)) == alvo:
            return os.path.join(pasta, nome)
    return None
