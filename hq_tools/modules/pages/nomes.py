"""Nomes de páginas: próximo número livre sem sobrescrever arquivo.

A duplicação de página no gerenciador escolhia o número com uma expressão
regular que só aceitava ``pagina_005.kra`` em minúsculas. Numa pasta com
``Pagina_005.KRA`` (o Windows não diferencia maiúsculas) o número 5 era
considerado livre e a cópia podia sobrescrever a página existente.
"""

import re


def proximo_indice_livre(nomes, prefixo="pagina"):
    """Menor número de página livre para ``prefixo_NNN.kra``.

    A comparação ignora maiúsculas/minúsculas no prefixo e na extensão: o
    arquivo ``Pagina_005.KRA`` ocupa o número 5 do mesmo jeito que
    ``pagina_005.kra``. Nomes fora do padrão (``pagina_extra.kra``,
    ``modelo-001.kra``) não contam.
    """
    padrao = re.compile(
        r"^{0}_(\d+)\.kra$".format(re.escape(str(prefixo))), re.IGNORECASE
    )
    numeros = set()
    for nome in nomes or ():
        encontrado = padrao.match(str(nome))
        if encontrado:
            numeros.add(int(encontrado.group(1)))
    numero = 1
    while numero in numeros:
        numero += 1
    return numero
