"""Camada de widgets compartilhada: um lugar só para o visual dos dockers.

Até a v0.6.2 cada docker criava os widgets por conta própria, e a diferença
ficou visível: 52 botões, 11 com ícone e 22 com tooltip, espalhados pelos
dockers, escritos em momentos diferentes. O docker de páginas tem 10 tooltips
e 5 ícones; o de retículas, que é o maior, tem 1 tooltip e nenhum ícone. Nada
impedia a divergência, porque não havia regra: cada botão decidia sozinho.

Estes helpers são a regra. O botão exige a dica (segundo argumento, sem padrão),
o rótulo de estado sempre quebra linha, e o espaçamento sai da escala do
``docs/DESIGN.md``. A identidade visual continua sendo a do Krita: nada aqui
pinta fundo, borda ou fonte, porque estilo próprio briga com o tema que o autor
escolheu, com o alto dpi e com os ícones do programa.
"""

import collections
import os

from .compat import (
    ELIDE_MIDDLE,
    FRAME_HLINE,
    FRAME_NOFRAME,
    IMAGE_FORMAT_ARGB32,
    PALETTE_NO_ROLE,
    SIZE_IGNORED,
    SIZE_PREFERRED,
    TEXT_BROWSER_INTERACTION,
    TEXT_PLAIN,
    TEXT_SELECTABLE,
    TRANSPARENT,
    QImage,
    QPixmap,
    QSvgRenderer,
    QtGui,
    QtWidgets,
    standard_icon,
)
from .paths import ICONE_PATH
from .version import __version__
from . import i18n

# Endereço do rodapé de cada doca: sempre a última release publicada.
RELEASES_URL = "https://github.com/ricolandia/krita-hq-tools/releases/latest"

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


class _RotuloCaminho(QtWidgets.QLabel):
    """Caminho em uma linha: elide no meio quando falta espaço.

    Caminho longo não tem espaço para quebrar (``/home/.../hq_tools``), então
    o ``wordWrap`` do ``rotulo_info`` deixava o rótulo com três ou quatro
    linhas e empurrava o resto do docker para baixo. Aqui o texto fica em uma
    linha, com o caminho inteiro no tooltip e selecionável para copiar.
    """

    def __init__(self, texto="", dica=None, pai=None):
        super().__init__(pai)
        self._dica = dica
        self._texto = ""
        self.setWordWrap(False)
        self.setMinimumWidth(0)
        self.setTextFormat(TEXT_PLAIN)
        self.setTextInteractionFlags(TEXT_SELECTABLE)
        self.setSizePolicy(SIZE_IGNORED, SIZE_PREFERRED)
        self.setText(texto)

    def setText(self, texto):
        self._texto = str(texto)
        self.setToolTip(self._dica or self._texto)
        self._elidir()

    def _elidir(self):
        largura = max(24, self.width())
        super().setText(
            self.fontMetrics().elidedText(self._texto, ELIDE_MIDDLE, largura)
        )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._elidir()


def rotulo_caminho(texto="", dica=None, pai=None):
    """Rótulo de caminho em uma linha, com o texto inteiro no tooltip."""
    return _RotuloCaminho(texto, dica, pai)


def rolavel(widget, pai=None):
    """Põe um conteúdo longo dentro de uma área rolável.

    O mínimo de altura de um formulário longo (Retículas tem 860 px) vira o
    mínimo do docker inteiro e não cabe em tela de 768 px. Com a área rolável,
    o docker encolhe e o conteúdo continua acessível pela barra. O fundo e a
    moldura seguem o tema do Krita (sem QSS).
    """
    area = QtWidgets.QScrollArea(pai)
    area.setWidgetResizable(True)
    area.setFrameShape(FRAME_NOFRAME)
    area.setBackgroundRole(PALETTE_NO_ROLE)
    area.viewport().setAutoFillBackground(False)
    area.setWidget(widget)
    # Mantém a largura mínima do conteúdo: assim não aparece barra horizontal
    # nem campo cortado na lateral. O que ganha rolagem é só a altura.
    minimo = widget.minimumSizeHint().width()
    if minimo > 0:
        area.setMinimumWidth(minimo)
    return area


# Cache das miniaturas de SVG: as listas redesenham a cada refresh e o mesmo
# arquivo era rasterizado de novo. A chave inclui mtime e tamanho, então
# editar o SVG invalida sozinho (mesmo padrão do cache de .kra do thumbs.py).
_LIMITE_MINIATURAS = 256
_miniaturas = collections.OrderedDict()


def limpar_cache_miniaturas():
    """Esvazia o cache das miniaturas de SVG (testes e quem quiser)."""
    _miniaturas.clear()


def _chave_miniatura(path, size, proporcao):
    try:
        info = os.stat(path)
    except OSError:
        return None
    return (os.path.abspath(path), info.st_mtime_ns, info.st_size, size, proporcao)


def render_svg_thumbnail(path, size=120, proporcao=0.75):
    """Miniatura rasterizada de um SVG, para as listas dos dockers.

    Estava copiada em três (balões, onomatopeias e biblioteca) com alturas
    diferentes; aqui a proporção vira parâmetro para cada lista manter o que
    já usava. Com cache por arquivo (mtime/tamanho na chave). Devolve ``None``
    quando o Qt do SVG não está disponível ou o arquivo não é um SVG legível:
    a lista cai no item sem ícone, sem quebrar.
    """
    if QSvgRenderer is None:
        return None
    chave = _chave_miniatura(path, size, proporcao)
    if chave is not None:
        pixmap = _miniaturas.get(chave)
        if pixmap is not None:
            _miniaturas.move_to_end(chave)
            return pixmap
    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return None
    image = QImage(size, int(size * proporcao), IMAGE_FORMAT_ARGB32)
    image.fill(TRANSPARENT)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    pixmap = QPixmap.fromImage(image)
    if chave is not None:
        _miniaturas[chave] = pixmap
        _miniaturas.move_to_end(chave)
        while len(_miniaturas) > _LIMITE_MINIATURAS:
            _miniaturas.popitem(last=False)
    return pixmap


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


def _rodape():
    """Versão instalada e link manual para a última release, no pé da doca."""
    linha = QtWidgets.QHBoxLayout()
    linha.setContentsMargins(0, 0, 0, 0)
    linha.setSpacing(GAP)
    versao = QtWidgets.QLabel("HQ Tools v{0}".format(__version__))
    versao.setToolTip(i18n.t("Versão instalada do HQ Tools."))
    link = QtWidgets.QLabel(
        '<a href="{0}">{1}</a>'.format(RELEASES_URL, i18n.t("Verificar atualização"))
    )
    link.setOpenExternalLinks(True)
    link.setTextInteractionFlags(TEXT_BROWSER_INTERACTION)
    link.setToolTip(i18n.t("Abre a última release no GitHub. A atualização é manual."))
    linha.addWidget(versao)
    linha.addStretch(1)
    linha.addWidget(link)
    return linha


def painel(pai=None, margem=MARGEM, espaco=GAP):
    """``(widget, layout vertical)`` já com o espaçamento da casa.

    Os dockers abriam com as mesmas duas linhas; agora abrem com uma. O
    conteúdo fica num layout interno com esticamento e o rodapé (versão e
    link da release) fica sempre no pé, fora do conteúdo.
    """
    widget = QtWidgets.QWidget(pai)
    if os.path.isfile(ICONE_PATH):
        icone = QtGui.QIcon(ICONE_PATH)
        widget.setWindowIcon(icone)
        if pai is not None:
            pai.setWindowIcon(icone)
    externo = espacamento(QtWidgets.QVBoxLayout(widget), margem, espaco)
    conteudo = espacamento(QtWidgets.QVBoxLayout(), 0, espaco)
    externo.addLayout(conteudo, 1)
    externo.addLayout(_rodape())
    return widget, conteudo
