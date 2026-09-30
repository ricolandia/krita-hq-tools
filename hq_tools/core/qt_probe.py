"""Escolha da versão do Qt, sem importar PyQt.

Fica separado de :mod:`hq_tools.core.compat` porque a decisão precisa ser
testável: os testes rodam em máquina onde nenhum dos dois PyQt está
instalado, e importar ``compat`` ali estoura.
"""

import sys

# Ordem de preferência quando o processo não diz nada (fora do Krita).
_PREFERENCIA = (6, 5)

# Differente de None: "não me informaram" é outra coisa que "não há Krita".
_NAO_INFORMADO = object()


def versao_do_krita():
    """Versão do Qt que o processo do Krita está usando, ou ``None``.

    O Krita exporta ``krita.QT_VERSION``. Descobrir a versão tentando importar
    PyQt6 primeiro erra quando a máquina tem PyQt6 instalado por fora (pip,
    outra distro) e o Krita em uso é o 5.x: o plugin passava a construir
    widgets de um Qt que não é o do processo, e o Krita caía na hora de abrir
    qualquer docker.
    """
    try:
        from krita import QT_VERSION
    except ImportError:
        return None
    try:
        return int(str(QT_VERSION).strip()[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def versao_no_processo():
    """Qt já importado pelo interpretador, se houver.

    Fora do Krita (testes, scripts) nenhum ``krita`` existe, e aí vale o que o
    processo já tem em uso. Sem isto o import fixava PyQt6 e quebrava em toda
    máquina que só tem PyQt5.
    """
    for versao in _PREFERENCIA:
        if "PyQt{0}".format(versao) in sys.modules:
            return versao
    return None


def versao_disponivel():
    """Primeira versão de Qt realmente instalada, ou ``None``."""
    for versao in _PREFERENCIA:
        nome = "PyQt{0}".format(versao)
        if nome in sys.modules:
            return versao
        try:
            __import__(nome)
            return versao
        except ImportError:
            continue
    return None


def escolher(versao_krita=_NAO_INFORMADO, no_processo=_NAO_INFORMADO, disponivel=_NAO_INFORMADO):
    """Devolve 5 ou 6: qual binding de Qt o plugin deve usar.

    A ordem importa: o que o Krita disser ganha sempre, porque o processo já
    está com um Qt carregado e trocar cria dois QObjects em Qt diferentes, que
    o Python não deixa passar entre si.

    Os três argumentos existem para teste e para o chamador que já sabe a
    resposta. ``None`` significa "não há", que é diferente de omitir (aí a
    função descobre sozinha).
    """
    if versao_krita is _NAO_INFORMADO:
        versao_krita = versao_do_krita()
    if versao_krita is not None:
        return 6 if versao_krita >= 6 else 5
    if no_processo is _NAO_INFORMADO:
        no_processo = versao_no_processo()
    if no_processo is not None:
        return 6 if no_processo >= 6 else 5
    if disponivel is _NAO_INFORMADO:
        disponivel = versao_disponivel()
    if disponivel is None:
        # Sem nenhum dos dois, deixa o erro de import do PyQt falar. A
        # mensagem padrão ("No module named 'PyQt6'") é mais honesta que uma
        # mensagem inventada aqui.
        return 6
    return 6 if disponivel >= 6 else 5
