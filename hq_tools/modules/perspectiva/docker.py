"""Docker da biblioteca de linhas de perspectiva.

Mesmo fluxo do visualizador 3D: escolha o conjunto, desenhe uma seleção
retangular sobre o painel, o preview adota a proporção dela (WYSIWYG), o
flutuante mostra a malha sobre a seleção (arrastar move, roda redimensiona) e
a inserção sai no tamanho exato da seleção, abaixo do esboço, como camada ou
referência travada, com a seleção desfeita. A inserção roda em macro de
desfazer: um Ctrl+Z desfaz tudo.
"""

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core import mapeamento, registro, ui
from ...core.compat import (
    ALIGN_CENTER,
    CURSOR_SIZE_ALL,
    ICON_MODE,
    IMAGE_FORMAT_RGBA8888,
    LIST_ADJUST,
    LIST_STATIC,
    QImage,
    QSvgRenderer,
    TRANSPARENT,
    USER_ROLE,
    WA_NO_SYSTEM_BACKGROUND,
    WA_TRANSLUCENT_BACKGROUND,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from . import linhas

PEN_STYLE_DASH = getattr(getattr(QtCore.Qt, "PenStyle", QtCore.Qt), "DashLine")

TAMANHO_PREVIEW = (320, 427)


class _Flutuante(QtWidgets.QWidget):
    """Malha flutuante sobre o canvas: arrastar move, roda dá zoom no tamanho."""

    TAMANHO_MINIMO = 60

    def __init__(self, docker, pai):
        super().__init__(pai)
        self.docker = docker
        self.setAttribute(WA_TRANSLUCENT_BACKGROUND)
        self.setAttribute(WA_NO_SYSTEM_BACKGROUND)
        self.setAutoFillBackground(False)
        self.setCursor(CURSOR_SIZE_ALL)
        self._pixmap = None
        self._aspecto = None
        self._arrastando = False
        self._ultimo = None

    @property
    def arrastando(self):
        return self._arrastando

    def definir_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def definir_aspecto(self, aspecto):
        """Trava a proporção da janela na da seleção (WYSIWYG)."""
        try:
            self._aspecto = max(0.05, float(aspecto)) if aspecto else None
        except (TypeError, ValueError):
            self._aspecto = None

    def _altura_para(self, largura):
        if self._aspecto is None:
            return self.height()
        return max(self.TAMANHO_MINIMO, int(round(largura / self._aspecto)))

    def paintEvent(self, evento):
        painter = QtGui.QPainter(self)
        if self._pixmap is not None:
            painter.drawPixmap(self.rect(), self._pixmap)
        caneta = QtGui.QPen(QtGui.QColor(20, 20, 20, 170))
        caneta.setStyle(PEN_STYLE_DASH)
        painter.setPen(caneta)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def mousePressEvent(self, evento):
        self._ultimo = evento.pos()
        self._arrastando = True

    def mouseMoveEvent(self, evento):
        if self._ultimo is None:
            return
        self.move(self.pos() + evento.pos() - self._ultimo)

    def mouseReleaseEvent(self, evento):
        self._ultimo = None
        self._arrastando = False

    def wheelEvent(self, evento):
        delta = evento.angleDelta().y()
        if not delta:
            return
        fator = 1.1 if delta > 0 else 1 / 1.1
        largura = max(self.TAMANHO_MINIMO, int(round(self.width() * fator)))
        altura = max(self.TAMANHO_MINIMO, self._altura_para(largura))
        centro = self.rect().center()
        self.resize(largura, altura)
        self.move(self.pos() + centro - self.rect().center())
        self.docker.atualizar_flutuante()


class PerspectivaDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: perspectiva")
        self.config = Config()
        self._flutuante = None
        self._selecao_flutuante = None
        self._build_ui()
        self.refresh()
        registro.registrar("perspectiva", self)

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)
        layout.addWidget(ui.rotulo(
            "Escolha um conjunto de linhas, desenhe uma seleção retangular "
            "sobre o painel e insira: a malha sai no tamanho da seleção, "
            "abaixo do esboço."
        ))
        self.list_presets = widgets.QListWidget()
        self.list_presets.setViewMode(ICON_MODE)
        self.list_presets.setIconSize(QtCore.QSize(120, 160))
        self.list_presets.setResizeMode(LIST_ADJUST)
        self.list_presets.setMovement(LIST_STATIC)
        self.list_presets.setWordWrap(True)
        self.list_presets.currentItemChanged.connect(
            lambda atual, anterior: self.atualizar_preview()
        )
        layout.addWidget(self.list_presets, 1)

        self.preview = widgets.QLabel()
        self.preview.setMinimumSize(240, 240)
        self.preview.setAlignment(ALIGN_CENTER)
        self.preview.setToolTip(
            "Prévia do conjunto selecionado; com uma seleção ativa no Krita, "
            "adota a proporção dela."
        )
        layout.addWidget(self.preview, 1)

        botoes = widgets.QHBoxLayout()
        self.button_flutuar = ui.botao(
            "Flutuar na página",
            "Mostra a malha sobre a seleção ativa; arraste para mover e use a "
            "roda para redimensionar.",
        )
        self.button_flutuar.setCheckable(True)
        self.button_flutuar.toggled.connect(self._alternar_flutuar)
        botoes.addWidget(self.button_flutuar)
        button_atualizar = ui.botao(
            "Atualizar prévia", "Relê a seleção ativa e redesenha a prévia.",
            icone_chave="atualizar",
        )
        button_atualizar.clicked.connect(self.atualizar_preview)
        botoes.addWidget(button_atualizar)
        layout.addLayout(botoes)

        botoes2 = widgets.QHBoxLayout()
        button_inserir = ui.botao(
            "Inserir no painel",
            "Insere a malha no tamanho da seleção, abaixo da camada ativa.",
        )
        button_inserir.clicked.connect(lambda: self.inserir(False))
        botoes2.addWidget(button_inserir)
        button_referencia = ui.botao(
            "Inserir como referência",
            "Como o inserir, mas a camada fica travada e com rótulo de cor, "
            "no papel de referência.",
        )
        button_referencia.clicked.connect(lambda: self.inserir(True))
        botoes2.addWidget(button_referencia)
        layout.addLayout(botoes2)

        layout.addWidget(ui.rotulo(
            "Cores das famílias: azul = verticais/3º ponto de fuga; laranja = "
            "profundidade e eixos; cinza = horizontais e horizonte."
        ))
        self.setWidget(main)

    def refresh(self):
        self.list_presets.clear()
        ultimo = self.config.get("perspectiva.last_preset")
        selecionar = 0
        for indice, (arquivo, titulo, _, legenda) in enumerate(linhas.PRESETS):
            item = QtWidgets.QListWidgetItem(titulo)
            item.setData(USER_ROLE, arquivo)
            item.setToolTip(legenda)
            pixmap = self._miniatura(arquivo)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_presets.addItem(item)
            if arquivo == ultimo:
                selecionar = indice
        self.list_presets.setCurrentRow(selecionar)
        self.atualizar_preview()

    def _miniatura(self, arquivo):
        return self._rasterizar(linhas.gerar(arquivo, 120, 160), 120, 160)

    @staticmethod
    def _rasterizar(svg, largura, altura):
        if QSvgRenderer is None:
            return None
        renderer = QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
        imagem = QImage(largura, altura, IMAGE_FORMAT_RGBA8888)
        imagem.fill(TRANSPARENT)
        painter = QtGui.QPainter(imagem)
        renderer.render(painter)
        painter.end()
        return QtGui.QPixmap.fromImage(imagem)

    def _preset_atual(self):
        item = self.list_presets.currentItem()
        if item is None:
            return None
        return item.data(USER_ROLE)

    def _tamanho_do_preview(self):
        """Tamanho da prévia: a proporção da seleção quando ela existe."""
        largura = max(self.preview.width(), TAMANHO_PREVIEW[0])
        altura = max(self.preview.height(), TAMANHO_PREVIEW[1])
        documento = helpers.active_document()
        if documento is None:
            return largura, altura
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            return largura, altura
        aspecto = selecao[2] / float(selecao[3])
        if largura / float(altura) > aspecto:
            largura = max(80, int(round(altura * aspecto)))
        else:
            altura = max(80, int(round(largura / aspecto)))
        return largura, altura

    def atualizar_preview(self):
        arquivo = self._preset_atual()
        if not arquivo:
            return
        self.config.set("perspectiva.last_preset", arquivo)
        largura, altura = self._tamanho_do_preview()
        pixmap = self._rasterizar(linhas.gerar(arquivo, largura, altura), largura, altura)
        if pixmap is not None:
            self.preview.setPixmap(pixmap)
        self.atualizar_flutuante()
        self._sincronizar_flutuante()

    def atualizar_flutuante(self):
        if self._flutuante is None or self._preset_atual() is None:
            return
        largura = max(self._flutuante.width(), 60)
        altura = max(self._flutuante.height(), 60)
        pixmap = self._rasterizar(
            linhas.gerar(self._preset_atual(), largura, altura), largura, altura
        )
        if pixmap is not None:
            self._flutuante.definir_pixmap(pixmap)

    def _alternar_flutuar(self, ligado):
        if ligado:
            self._criar_flutuante()
        else:
            self._fechar_flutuante()

    def _criar_flutuante(self):
        view = helpers.active_view()
        documento = view.document() if view is not None else None
        if documento is None:
            helpers.show_info("Perspectiva", "Abra um documento para usar o flutuante.")
            self.button_flutuar.setChecked(False)
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                "Perspectiva",
                "Desenhe uma seleção retangular sobre o painel para usar o "
                "flutuante.",
            )
            self.button_flutuar.setChecked(False)
            return
        viewport = helpers.viewport_da_view(view)
        if viewport is None:
            helpers.show_info(
                "Perspectiva", "Não foi possível ancorar o flutuante nesta janela."
            )
            self.button_flutuar.setChecked(False)
            return
        self._fechar_flutuante()
        self._flutuante = _Flutuante(self, viewport)
        self._flutuante.definir_aspecto(selecao[2] / float(selecao[3]))
        self._selecao_flutuante = selecao
        self._posicionar_flutuante(viewport, selecao)
        self._flutuante.show()
        self._flutuante.raise_()
        self.atualizar_flutuante()

    def _posicionar_flutuante(self, viewport, selecao):
        """Coloca a janela sobre a seleção, com a proporção dela."""
        if self._flutuante is None:
            return
        documento = helpers.active_document()
        if documento is None:
            return
        parametros = helpers.parametros_do_canvas(documento, viewport)
        if parametros is None:
            return
        centro_widget, centro_imagem, zoom, rotacao, pan, espelhado = parametros
        tela = mapeamento.retangulo_para_widget(
            (selecao[0], selecao[1], selecao[2], selecao[3]),
            centro_widget,
            centro_imagem,
            zoom,
            rotacao,
            pan,
            espelhado,
        )
        aspecto = selecao[2] / float(selecao[3])
        fator = min(
            1.0,
            viewport.width() / max(1.0, float(tela[2])),
            viewport.height() / max(1.0, float(tela[3])),
        )
        largura = max(_Flutuante.TAMANHO_MINIMO, int(round(tela[2] * fator)))
        altura = max(_Flutuante.TAMANHO_MINIMO, int(round(largura / aspecto)))
        x = int(round(tela[0] + (tela[2] - largura) / 2.0))
        y = int(round(tela[1] + (tela[3] - altura) / 2.0))
        x = max(0, min(x, viewport.width() - largura))
        y = max(0, min(y, viewport.height() - altura))
        self._flutuante.setGeometry(x, y, largura, altura)

    def _sincronizar_flutuante(self):
        """Segue a seleção: reposiciona quando ela muda e fecha se sumir."""
        if self._flutuante is None:
            return
        documento = helpers.active_document()
        if documento is None:
            self._cancelar_flutuante()
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            self._cancelar_flutuante()
            return
        if selecao == self._selecao_flutuante or self._flutuante.arrastando:
            return
        self._selecao_flutuante = selecao
        self._flutuante.definir_aspecto(selecao[2] / float(selecao[3]))
        viewport = self._flutuante.parentWidget()
        if viewport is not None:
            self._posicionar_flutuante(viewport, selecao)
            self.atualizar_flutuante()

    def _cancelar_flutuante(self):
        """Fecha o flutuante e desmarca o botão (seleção sumiu ou mudou)."""
        self._fechar_flutuante()
        try:
            self.button_flutuar.setChecked(False)
        except (AttributeError, RuntimeError):
            pass

    def _fechar_flutuante(self):
        if self._flutuante is None:
            return
        try:
            self._flutuante.hide()
            self._flutuante.deleteLater()
        except (AttributeError, RuntimeError):
            pass
        self._flutuante = None
        self._selecao_flutuante = None

    def inserir(self, referencia=False):
        """Insere a malha na seleção, abaixo do esboço, dentro de uma macro."""
        documento = helpers.active_document()
        if documento is None:
            helpers.show_info("Perspectiva", "Abra um documento para inserir a malha.")
            return
        arquivo = self._preset_atual()
        if not arquivo:
            helpers.show_info("Perspectiva", "Escolha um conjunto na lista.")
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                "Perspectiva",
                "Desenhe uma seleção retangular sobre o painel de destino para "
                "inserir.",
            )
            return
        x, y, largura, altura = selecao
        ativo = documento.activeNode()
        nome_ativo = ativo.name() if ativo is not None else None
        svg = linhas.gerar(arquivo, largura, altura)
        imagem = self._rasterizar(svg, largura, altura)
        if imagem is None:
            helpers.show_info("Perspectiva", "Não foi possível desenhar a malha.")
            return
        rgba = imagem.convertToFormat(IMAGE_FORMAT_RGBA8888)
        dados = bytes(rgba.constBits().asstring(rgba.sizeInBytes()))
        nome = helpers.unique_layer_name(documento, "Perspectiva")

        def _inserir_agora():
            camada = documento.createNode(nome, "paintlayer")
            if camada is None or not camada.setPixelData(dados, x, y, largura, altura):
                helpers.show_info("Perspectiva", "Não foi possível criar a camada.")
                return False
            helpers.attach_below_active(documento, camada)
            if referencia:
                camada.setColorLabel(1)
                camada.setLocked(True)
                camada.setOpacity(150)
            documento.setActiveNode(camada)
            helpers.deselect(documento)
            documento.refreshProjection()
            return True

        if not helpers.run_in_macro(documento, _inserir_agora):
            return
        self.atualizar_flutuante()
        helpers.show_message(
            "Perspectiva '{0}' inserida abaixo de '{1}'{2}; seleção desfeita.".format(
                nome,
                nome_ativo or "camada ativa",
                " como referência" if referencia else "",
            )
        )
