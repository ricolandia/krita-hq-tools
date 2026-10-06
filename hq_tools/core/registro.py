"""Registro das instâncias dos dockers do plugin.

O hub precisa das instâncias para abrir e fechar as dockas, e casar por título
de janela é frágil (o título muda com tradução e com o tema). Cada docker se
registra no ``__init__``; o hub escuta as chegadas porque a ordem de criação é
do Krita, e pode ser que ele mesmo seja criado antes dos outros.
"""

_INSTANCIAS = {}
_OBSERVADORES = []

# Agrupamento dos botões no hub: cada tupla é um grupo, separado por um divisor
# na grade; a ordem das chaves dentro do grupo é a que aparece. Módulo fora da
# lista cai num grupo extra no fim (nada some).
GRUPOS = (
    ("pages", "producao"),
    ("moodboard", "biblioteca"),
    ("perspectiva", "viewer3d"),
    ("palettes", "brushes"),
    ("screentone", "balloons"),
    ("onomatopeias",),
)


def agrupar(modulos):
    """Grupos de módulos para o hub, na ordem de ``GRUPOS``.

    ``modulos`` é uma sequência de ``(chave, rótulo)`` (a ordem dela é mantida
    nas sobras); devolve uma lista de grupos (listas de pares).
    """
    disponiveis = dict(modulos)
    grupos = []
    usados = set()
    for grupo in GRUPOS:
        itens = [
            (chave, disponiveis[chave]) for chave in grupo if chave in disponiveis
        ]
        if itens:
            usados.update(chave for chave, _ in itens)
            grupos.append(itens)
    sobras = [
        (chave, rotulo)
        for chave, rotulo in disponiveis.items()
        if chave not in usados
    ]
    if sobras:
        grupos.append(sobras)
    return grupos


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
