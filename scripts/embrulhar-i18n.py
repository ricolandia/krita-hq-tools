#!/usr/bin/env python3
"""Codemod: embrulha strings visíveis do plugin em ``i18n.t(...)``.

Para quando entra um módulo novo (ou strings novas) e é preciso passar o texto
visível pela camada de idioma. O script lê o AST, acha os argumentos de texto
das chamadas conhecidas (botões, rótulos, títulos, tooltips, mensagens) e
troca o trecho no fonte preservando formatação e comentários; também insere o
import do i18n quando falta.

**Dry-run por padrão**: sem ``--aplicar`` ele só lista o que faria. Depois de
aplicar, rode a suíte: ``tests/test_i18n.py`` exige tradução para cada string
embrulhada (e acusa chave órfã).

Casos que ficam para a mão (o script não enxerga): texto montado em variável
(``texto = "..."`` seguido de ``texto += "..."``), nomes de dado (config,
chaves) e strings passadas por parâmetro entre funções.

Uso:
    python3 scripts/embrulhar-i18n.py [--aplicar] [--raiz DIR]
"""

import argparse
import ast
import os
import pathlib
import sys

RAIZ_PADRAO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chamada -> índices dos argumentos que são texto visível.
ALVOS = {
    "setWindowTitle": (0,),
    "setToolTip": (0,),
    "setText": (0,),
    "setPlaceholderText": (0,),
    "show_message": (0,),
    "show_info": (0, 1),
    "information": (1, 2),
    "warning": (1, 2),
    "question": (1, 2),
    "getExistingDirectory": (1,),
    "getOpenFileName": (1,),
    "addTab": (1,),
    "addItem": (0,),
    "addRow": (0,),
    "QCheckBox": (0,),
    "QGroupBox": (0,),
    "botao": (0, 1),
    "rotulo": (0, 1),
    "rotulo_info": (0, 1),
}


def literal_do_arg(arg):
    """O nó Constant por trás do argumento, ou None.

    Aceita o literal direto e também o literal de um ``"...".format(...)``,
    que é como a maioria das mensagens é montada.
    """
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg
    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Attribute)
        and arg.func.attr == "format"
        and isinstance(arg.func.value, ast.Constant)
        and isinstance(arg.func.value.value, str)
    ):
        return arg.func.value
    return None


def processar(caminho, aplicar):
    caminho = pathlib.Path(caminho)
    fonte = caminho.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    alvos = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        func = no.func
        if isinstance(func, ast.Attribute):
            nome = func.attr
        elif isinstance(func, ast.Name):
            nome = func.id
        else:
            continue
        if nome not in ALVOS:
            continue
        for indice in ALVOS[nome]:
            if indice >= len(no.args):
                continue
            arg = literal_do_arg(no.args[indice])
            if arg is None or not arg.value.strip():
                continue
            alvos.append(
                (arg.lineno, arg.col_offset, arg.end_lineno, arg.end_col_offset, arg.value)
            )
    if not alvos:
        return []
    if not aplicar:
        return [valor for *_, valor in alvos]
    # O ast devolve col_offset em BYTES UTF-8; por isso o trabalho é feito em
    # bytes e só no fim volta para texto (com acento, o offset em caracteres
    # desloca o span e o código sai corrompido).
    dados = fonte.encode("utf-8")
    linhas = dados.splitlines(keepends=True)
    inicios = [0]
    for linha in linhas:
        inicios.append(inicios[-1] + len(linha))

    def posicao(linha, coluna):
        return inicios[linha - 1] + coluna

    alvos.sort(key=lambda item: posicao(item[0], item[1]), reverse=True)
    for l1, c1, l2, c2, valor in alvos:
        ini = posicao(l1, c1)
        fim = posicao(l2, c2)
        dados = (
            dados[:ini]
            + "i18n.t({0!r})".format(valor).encode("utf-8")
            + dados[fim:]
        )
    fonte = dados.decode("utf-8")
    if "from ...core import i18n" not in fonte and "from .core import i18n" not in fonte:
        linhas = fonte.splitlines(keepends=True)
        ultimo = None
        for indice, linha in enumerate(linhas):
            if linha.startswith("from ...core import"):
                ultimo = indice
        if ultimo is not None:
            linhas.insert(ultimo + 1, "from ...core import i18n\n")
            fonte = "".join(linhas)
    caminho.write_text(fonte, encoding="utf-8")
    return [valor for *_, valor in alvos]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", default=RAIZ_PADRAO)
    parser.add_argument("--aplicar", action="store_true",
                        help="escreve as mudanças (sem isso, só lista)")
    opcoes = parser.parse_args(argv)

    pacote = os.path.join(opcoes.raiz, "hq_tools")
    total = 0
    for base, _, nomes in os.walk(pacote):
        if "__pycache__" in base:
            continue
        for nome in sorted(nomes):
            if not nome.endswith(".py") or nome.startswith("i18n"):
                continue
            caminho = os.path.join(base, nome)
            usados = processar(caminho, opcoes.aplicar)
            if usados:
                relativo = os.path.relpath(caminho, opcoes.raiz)
                acao = "embrulhadas" if opcoes.aplicar else "a embrulhar"
                print("{0}: {1} string(s) {2}".format(relativo, len(usados), acao))
                total += len(usados)
    print(
        "total: {0} string(s) {1}".format(
            total, "embrulhadas" if opcoes.aplicar else "(dry-run; use --aplicar)"
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
