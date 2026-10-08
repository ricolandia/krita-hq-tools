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
PASTA = "producao"
ARQUIVO_ESTADOS = "producao.json"
ARQUIVO_ROTEIRO = "roteiro.txt"
ARQUIVO_CHECKLIST = "checklist.md"
ARQUIVO_TEMPOS = "tempos.json"
PADRAO_PAGINA = re.compile(r"^pagina_(\d+)\.kra$", re.IGNORECASE)

ROTULOS_PT = {
    "esboco": "Esboço",
    "arte": "Arte",
    "final": "Final",
    "narracao": "Narração",
    "plano": "Plano",
}

EMOJIS = {"final": "🟩", "arte": "🟧", "esboco": "⬜"}


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
        planos = pagina.get("planos") or {}
        paineis = []
        for indice in range(1, len(pagina["panels"]) + 1):
            falas = [fala for fala in pagina["balloons"] if fala["panel"] == indice]
            paineis.append(
                {
                    "painel": indice,
                    "estado": marcados.get(
                        chave(pagina["index"], indice), ESTADO_PADRAO
                    ),
                    "plano": planos.get(indice, ""),
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


def formatar_cronometro(segundos):
    """``HH:MM:SS`` para o cronômetro da sessão."""
    segundos = max(0, int(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    return "{0:02d}:{1:02d}:{2:02d}".format(horas, minutos, segs)


def formatar_duracao(segundos):
    """Duração curta para relatórios: ``3h20min``, ``45min`` ou ``30s``."""
    segundos = max(0, int(segundos))
    if segundos < 60:
        return "{0}s".format(segundos)
    minutos = segundos // 60
    if minutos < 60:
        return "{0}min".format(minutos)
    horas, minutos = divmod(minutos, 60)
    return "{0}h{1:02d}min".format(horas, minutos)


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


def para_markdown(checklist, meta_semanal=0, hoje=None, rotulos=None, titulo=None, tempos=None):
    """Checklist em Markdown (checkboxes e emojis de estado; tempo opcional)."""
    rotulos = dict(ROTULOS_PT, **(rotulos or {}))
    contagem = progresso(checklist)
    linhas = ["# {0}".format(titulo or "Checklist de produção"), ""]
    linhas.append(
        "- Painéis: {total} · {0} finais · {1} em arte · {2} em esboço".format(
            "{0} {1}".format(EMOJIS["final"], contagem["finais"]),
            "{0} {1}".format(EMOJIS["arte"], contagem["arte"]),
            "{0} {1}".format(EMOJIS["esboco"], contagem["esboco"]),
            total=contagem["total"],
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
    tempos = tempos or {}
    if _segundos_int(tempos.get("total")):
        por_pagina = [
            _segundos_int(valor)
            for valor in (tempos.get("por_pagina") or {}).values()
            if _segundos_int(valor) > 0
        ]
        media = ""
        if por_pagina:
            media = " · média {0} por página".format(
                formatar_duracao(sum(por_pagina) // len(por_pagina))
            )
        linhas.append(
            "- Tempo: {0} no total{1}".format(
                formatar_duracao(tempos["total"]), media
            )
        )
    linhas.append("")
    for pagina in checklist:
        finais, total = progresso_da_pagina(pagina)
        titulo_pagina = "## Página {0} · {1}/{2} finais".format(
            pagina["pagina"], finais, total
        )
        segundos = _segundos_int(
            (tempos.get("por_pagina") or {}).get(str(pagina["pagina"]))
        )
        if segundos > 0:
            titulo_pagina += " · ⏱ {0}".format(formatar_duracao(segundos))
        linhas.append(titulo_pagina)
        for painel in pagina["paineis"]:
            estado = painel["estado"]
            caixa = "[x]" if estado == "final" else "[ ]"
            plano = (painel.get("plano") or "").strip()
            trecho_plano = (
                " · {0}: {1}".format(rotulos.get("plano", "Plano"), plano)
                if plano
                else ""
            )
            resumo = falas_resumo(painel, rotulos.get("narracao", "Narração"))
            sufixo = " · {0}".format(resumo) if resumo else ""
            linhas.append(
                "- {0} {1} Painel {2} ({3}){4}{5}".format(
                    caixa,
                    EMOJIS.get(estado, EMOJIS["esboco"]),
                    painel["painel"],
                    rotulos.get(estado, estado),
                    trecho_plano,
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


def _segundos_int(valor):
    """Segundos como inteiro >= 0 (tolerante a valor vindo do JSON)."""
    try:
        return max(0, int(valor or 0))
    except (TypeError, ValueError):
        return 0


def caminho_tempos(pasta):
    return os.path.join(pasta, ARQUIVO_TEMPOS)


def carregar_tempos(pasta):
    """Tempos acumulados (total e por página); tolerante a arquivo quebrado."""
    try:
        with open(caminho_tempos(pasta), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {"total": 0, "por_pagina": {}}
    if not isinstance(dados, dict):
        return {"total": 0, "por_pagina": {}}
    por_pagina = {}
    for pagina, segundos in (dados.get("por_pagina") or {}).items():
        por_pagina[str(pagina)] = _segundos_int(segundos)
    return {"total": _segundos_int(dados.get("total")), "por_pagina": por_pagina}


def salvar_tempos(pasta, dados):
    """Grava o tempos.json de forma atômica."""
    dados = dados or {}
    caminho = caminho_tempos(pasta)
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(
            {
                "total": _segundos_int(dados.get("total")),
                "por_pagina": {
                    str(pagina): _segundos_int(segundos)
                    for pagina, segundos in (dados.get("por_pagina") or {}).items()
                },
            },
            arquivo,
            ensure_ascii=False,
            indent=2,
        )
    os.replace(temporario, caminho)


def acumular_tempo(dados, pagina, segundos):
    """Tempos com a sessão somada (total e, quando houver, a página)."""
    dados = dados or {}
    segundos = _segundos_int(segundos)
    por_pagina = dict(dados.get("por_pagina") or {})
    if pagina is not None and segundos:
        chave = str(pagina)
        por_pagina[chave] = _segundos_int(por_pagina.get(chave)) + segundos
    return {
        "total": _segundos_int(dados.get("total")) + segundos,
        "por_pagina": por_pagina,
    }


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
