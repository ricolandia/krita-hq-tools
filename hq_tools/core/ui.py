"""Camada de widgets compartilhada: um lugar só para o visual dos dockers.

Até a v0.6.2 cada docker criava os widgets por conta própria, e a diferença
ficou visível: 52 botões, 11 com ícone e 22 com tooltip, espalhados por 7
arquivos escritos em momentos diferentes. O docker de páginas tem 10 tooltips e
5 ícones; o de retículas, que é o maior, tem 1 tooltip e nenhum ícone. Nada
impedia a divergência, porque não havia regra: cada botão decidia sozinho.

Estes helpers são a regra. O botão exige a dica (segundo argumento, sem padrão),
o rótulo de estado sempre quebra linha, e o espaçamento sai da escala do
``docs/DESIGN.md``. A identidade visual continua sendo a do Krita: nada aqui
pinta fundo, borda ou fonte, porque estilo próprio briga com o tema que o autor
escolheu, com o alto dpi e com os ícones do programa.
"""

from .compat import FRAME_HLINE, QtWidgets, standard_icon

# Escala de espaçamento do DESIGN.md (seção 4), recortada para o que cabe num
# docker estreito: 4 entre controles, 8 entre linhas, 12 na borda do painel.
GAP = 8
MARGEM = 12

# Chave semântica -> nome do QStyle.StandardPixmap. O botão pede "atualizar" e
# não "SP_BrowserReload", para a escolha de ícone ficar num lugar só. Os nomes
# são os que o próprio plugin já usava e que existem em PyQt5 e PyQt6; um nome
# fora daqui cai no fallback em vez de virar um ícone genérico ou sumir.
ICONES = {
    "abrir": "SP_DialogOpenButton",
    "aplicar": "SP_DialogApplyButton",
    "atualizar": "SP_BrowserReload",
    "novo": "SP_FileDialogNewFolder",
    "pasta": "SP_DirOpenIcon",
    "salvar": "SP_DialogSaveButton",
}
ICONE_FALLBACK = "SP_FileIcon"


def icone(chave):
    """Ícone do tema a partir de uma chave de :data:`ICONES`.

    Chave desconhecida devolve o ícone genérico de arquivo em vez de levantar:
    um botão sem ícone ainda é usável, um botão que não abre é pior.
    """
    return standard_icon(ICONES.get(chave, ICONE_FALLBACK))


def botao(rotulo, dica, slot=None, icone_chave=None, pai=None):
    """Botão com tooltip obrigatório.

    ``dica`` é o segundo argumento e não tem padrão: quem criar botão sem
    tooltip quebra a assinatura, e a checagem estática dos dockerers
    (``tests/test_ui.py``) impede o ``QPushButton`` de voltar a ser chamado
    direto. A dica é a resposta para o que o botão faz, o que muda no documento
    e o que é preciso antes (documento aberto, reiniciar o Krita).
    """
    widget = QtWidgets.QPushButton(rotulo, pai)
    widget.setToolTip(dica)
    if icone_chave is not None:
        widget.setIcon(icone(icone_chave))
    if slot is not None:
        widget.clicked.connect(slot)
    return widget


def rotulo(texto, dica=None, pai=None):
    """QLabel com quebra de linha ligada."""
    widget = QtWidgets.QLabel(texto, pai)
    widget.setWordWrap(True)
    if dica:
        widget.setToolTip(dica)
    return widget


def rotulo_info(texto="", dica=None, pai=None):
    """Rótulo de estado: o texto muda conforme o documento (célula em px,
    projeto, modelo) e é o que alarga o docker.

    O Qt reserva para um QLabel a largura da linha inteira como largura mínima,
    então um aviso de 90 caracteres estufa o painel em vez de quebrar. Daí o
    ``setWordWrap`` e a largura mínima zerada. É a correção do que o rótulo de
    célula da aba Retículas fazia; se o aviso ainda estufar, falta relaxar a
    política horizontal (conferir dentro do Krita).
    """
    widget = rotulo(texto, dica, pai)
    widget.setMinimumWidth(0)
    return widget


def separador(pai=None):
    """Linha divisória fina, na cor do tema (a de um ``QFrame`` de um traço)."""
    linha = QtWidgets.QFrame(pai)
    linha.setFrameShape(FRAME_HLINE)
    return linha


def espacamento(layout, margem=MARGEM, espaco=GAP):
    """Aplica a escala de espaçamento num layout e devolve ele."""
    if margem is not None:
        layout.setContentsMargins(margem, margem, margem, margem)
    if espaco is not None:
        layout.setSpacing(espaco)
    return layout


def painel(pai=None, margem=MARGEM, espaco=GAP):
    """``(widget, layout vertical)`` já com o espaçamento da casa.

    Os 7 dockers abriam com as mesmas duas linhas; agora abrem com uma.
    """
    widget = QtWidgets.QWidget(pai)
    layout = QtWidgets.QVBoxLayout(widget)
    return widget, espacamento(layout, margem, espaco)