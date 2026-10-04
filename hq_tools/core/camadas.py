"""Ordem de camadas (núcleo puro, sem Krita).

No Krita, ``childNodes()`` e ``setChildNodes()`` usam a ordem base -> topo
(confirmado em ``libs/libkis/Node.cpp``). Estas funções manipulam essa lista
para posicionar uma camada nova logo abaixo de outra.
"""


def ordem_com_no_abaixo(lista, alvo, novo, chave=None):
    """Lista (base -> topo) com ``novo`` logo abaixo de ``alvo``.

    ``chave`` identifica os itens (por padrão, o próprio item). Devolve
    ``None`` quando o alvo não está na lista.
    """
    chave = chave or (lambda item: item)
    chaves = [chave(item) for item in lista]
    if chave(alvo) not in chaves:
        return None
    copia = [item for item in lista if chave(item) != chave(novo)]
    indice = next(
        posicao for posicao, item in enumerate(copia) if chave(item) == chave(alvo)
    )
    copia.insert(indice, novo)
    return copia
