"""Escrita de diagnóstico tolerante ao Krita sem console.

No Krita do Windows (aplicativo gráfico sem console) ``sys.stderr`` é
``None``. Escrever nele na importação derrubava o plugin inteiro
("Could not import hq_tools"). Todo o código de runtime usa
``escrever_erro`` em vez de ``sys.stderr.write`` direto.
"""

import sys


def escrever_erro(texto, flush=False):
    """Escreve em ``sys.stderr`` quando ele existe; silencioso quando não."""
    if sys.stderr is None:
        return
    try:
        sys.stderr.write(texto)
        if flush:
            sys.stderr.flush()
    except (ValueError, OSError):
        pass
