"""Registro das instâncias dos dockers do plugin.

O hub precisa das instâncias para abrir e fechar as dockas, e casar por título
de janela é frágil (o título muda com tradução e com o tema). Cada docker se
registra no ``__init__``; o hub escuta as chegadas porque a ordem de criação é
do Krita, e pode ser que ele mesmo seja criado antes dos outros.
"""

_INSTANCIAS = {}
_OBSERVADORES = []


def registrar(chave, docker):
    """Guarda a instância do docker e avisa quem estiver escutando."""
    _INSTANCIAS[chave] = docker
    for observador in list(_OBSERVADORES):
        try:
            observador(chave, docker)
        except (AttributeError, RuntimeError, TypeError):
            pass


def obter(chave):
    return _INSTANCIAS.get(chave)


def instancias():
    return dict(_INSTANCIAS)


def ao_registrar(callback):
    """Chama ``callback(chave, docker)`` a cada docker registrado."""
    _OBSERVADORES.append(callback)


def limpar():
    """Esvazia o registro (usado nos testes)."""
    _INSTANCIAS.clear()
    del _OBSERVADORES[:]
