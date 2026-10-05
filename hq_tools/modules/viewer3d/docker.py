"""Docker "HQ Tools: 3D": manequim 3D posável como camada de referência.

O modelo vem do exportador ``scripts/exportar-modelo3d.py`` (FBX -> JSON) e é
lido em Python puro (``core/modelo3d.py``); o Blender não é dependência em
tempo de execução. Arraste no preview para orbitar, use a roda para o zoom e
clique numa parte do corpo: os sliders daquela região aparecem. "Dobrar",
"Abrir" e "Girar" são mapeados para os eixos reais do rig (neste Auto-Rig Pro:
Z, X e Y).

"Flutuar na página" mostra o preview sobre o canvas, arrastável e
redimensionável (alça no canto ou roda), com opacidade e modo fixado
(click-through). "Inserir como camada/referência" rasteriza no lugar do
flutuante, mapeado para pixels do documento, e entra logo abaixo do nó ativo
para o esboço ficar por cima.
"""

import os

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core import mapeamento
from ...core import modelo3d
from ...core import registro, ui
from ...core import i18n
from ...core.compat import (
    ALIGN_CENTER,
    CURSOR_ARROW,
    CURSOR_SIZE_ALL,
    CURSOR_SIZE_FDIAG,
    IMAGE_FORMAT_RGBA8888,
    QImage,
    QSvgRenderer,
    TRANSPARENT,
    WA_NO_SYSTEM_BACKGROUND,
    WA_TRANSLUCENT_BACKGROUND,
    WA_TRANSPARENT_FOR_MOUSE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.paths import (
    VIEWER3D_MODELOS,
    VIEWER3D_POSE_PADRAO,
    VIEWER3D_POSES_DIR,
)

LIMITE_SLIDER = 120

ORIENTACAO_HORIZONTAL = getattr(
    getattr(QtCore.Qt, "Orientation", QtCore.Qt), "Horizontal"
)

PEN_STYLE_DASH = getattr(getattr(QtCore.Qt, "PenStyle", QtCore.Qt), "DashLine")

REGIOES = (
    ("cabeca", "Cabeça", ("neck.x", "head.x")),
    ("tronco", "Tronco", ("spine_01.x", "spine_02.x", "spine_03.x")),
    (
        "braco_esq",
        "Braço esquerdo",
        ("shoulder.l", "arm_stretch.l", "forearm_stretch.l", "hand.l"),
    ),
    (
        "braco_dir",
        "Braço direito",
        ("shoulder.r", "arm_stretch.r", "forearm_stretch.r", "hand.r"),
    ),
    ("perna_esq", "Perna esquerda", ("thigh_stretch.l", "leg_stretch.l", "foot.l")),
    ("perna_dir", "Perna direita", ("thigh_stretch.r", "leg_stretch.r", "foot.r")),
)

NOMES = {
    "neck": "Pescoço",
    "head": "Cabeça",
    "spine_01": "Tronco baixo",
    "spine_02": "Tronco",
    "spine_03": "Tronco alto",
    "shoulder": "Ombro",
    "arm_stretch": "Braço",
    "forearm_stretch": "Cotovelo",
    "hand": "Mão",
    "thigh_stretch": "Coxa",
    "leg_stretch": "Joelho",
    "foot": "Pé",
}

EIXOS_POR_BASE = {
    "neck": ("dobrar", "abrir", "girar"),
    "head": ("dobrar", "abrir", "girar"),
    "spine_01": ("dobrar", "abrir", "girar"),
    "spine_02": ("dobrar", "abrir", "girar"),
    "spine_03": ("dobrar", "abrir", "girar"),
    "shoulder": ("abrir", "dobrar"),
    "arm_stretch": ("dobrar", "abrir", "girar"),
    "forearm_stretch": ("dobrar", "girar"),
    "hand": ("dobrar", "abrir", "girar"),
    "thigh_stretch": ("dobrar", "abrir", "girar"),
    "leg_stretch": ("dobrar",),
    "foot": ("dobrar",),
}

ROTULOS = {"dobrar": "Dobrar", "abrir": "Abrir", "girar": "Girar"}

FAMILIAS_DEDO = ("index", "middle", "ring", "pinky", "thumb")


def _base(nome):
    return nome.rsplit(".", 1)[0]


def _lado(nome):
    if nome.endswith(".l"):
        return "l"
    if nome.endswith(".r"):
        return "r"
    return ""


def nome_amigavel(nome):
    rotulo = NOMES.get(_base(nome), _base(nome))
    lado = _lado(nome)
    if lado == "l":
        return rotulo + " (esq)"
    if lado == "r":
        return rotulo + " (dir)"
    return rotulo


def _posicao(evento):
    if hasattr(evento, "position"):
        return evento.position().toPoint()
    return evento.pos()


def _botao_do_meio(evento):
    meio = getattr(getattr(QtCore.Qt, "MouseButton", QtCore.Qt), "MiddleButton")
    return evento.button() == meio


def _shift_pressionado(evento):
    shift = getattr(
        getattr(QtCore.Qt, "KeyboardModifier", QtCore.Qt), "ShiftModifier"
    )
    return bool(evento.modifiers() & shift)


def _viewport_da_view(view):
    """Viewport do canvas da view ativa (para ancorar o flutuante), ou None."""
    try:
        janela = view.window()
        q_janela = janela.qwindow()
    except (AttributeError, RuntimeError):
        return None
    central = q_janela.centralWidget() if q_janela is not None else None
    area_mdi = central.findChild(QtWidgets.QMdiArea) if central is not None else None
    if area_mdi is None:
        return None
    subjanelas = area_mdi.subWindowList()
    views = list(janela.views())
    for indice, sub in enumerate(subjanelas):
        if indice < len(views) and views[indice] == view:
            area = sub.widget().findChild(QtWidgets.QAbstractScrollArea)
            return area.viewport() if area is not None else None
    if subjanelas:
        area = subjanelas[0].widget().findChild(QtWidgets.QAbstractScrollArea)
        return area.viewport() if area is not None else None
    return None


class _Preview(QtWidgets.QLabel):
    """Área do preview: arrastar orbita, roda dá zoom, clique seleciona."""

    def __init__(self, docker):
        super().__init__()
        self.docker = docker
        self.setMinimumSize(240, 240)
        self.setAlignment(ALIGN_CENTER)
        self._ultimo = None
        self._arrastou = False
        self._deslocando = False

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.docker.agendar_render()

    def mousePressEvent(self, evento):
        self._ultimo = _posicao(evento)
        self._arrastou = False
        self._deslocando = (
            self.docker.modo_mover
            or _shift_pressionado(evento)
            or _botao_do_meio(evento)
        )

    def mouseMoveEvent(self, evento):
        if self._ultimo is None:
            return
        posicao = _posicao(evento)
        delta = posicao - self._ultimo
        if abs(delta.x()) + abs(delta.y()) > 3:
            self._arrastou = True
            if self._deslocando:
                self.docker.deslocar(delta.x(), delta.y())
            else:
                self.docker.orbitar(delta.x(), delta.y())
            self._ultimo = posicao

    def mouseReleaseEvent(self, evento):
        if self._ultimo is not None and not self._arrastou:
            posicao = _posicao(evento)
            self.docker.selecionar_em(posicao.x(), posicao.y())
        self._ultimo = None

    def wheelEvent(self, evento):
        delta = evento.angleDelta().y()
        if delta:
            self.docker.aplicar_zoom(1.1 if delta > 0 else 1 / 1.1)


class _Flutuante(QtWidgets.QWidget):
    """Preview 3D flutuante sobre o canvas: arrasta, redimensiona, opacidade."""

    LADO_ALCA = 16
    TAMANHO_MINIMO = 60

    def __init__(self, docker, pai):
        super().__init__(pai)
        self.docker = docker
        self.setAttribute(WA_TRANSLUCENT_BACKGROUND)
        self.setAttribute(WA_NO_SYSTEM_BACKGROUND)
        self.setAutoFillBackground(False)
        self.setCursor(CURSOR_SIZE_ALL)
        self._pixmap = None
        self._opacidade = 0.8
        self._aspecto = None
        self._arrastando = False
        self._redimensionando = False
        self._ultimo = None

    @property
    def arrastando(self):
        return self._arrastando or self._redimensionando

    def definir_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def definir_opacidade(self, valor):
        self._opacidade = max(0.1, min(1.0, float(valor)))
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

    def _retangulo_alca(self):
        lado = self.LADO_ALCA
        return QtCore.QRect(self.width() - lado, self.height() - lado, lado, lado)

    def paintEvent(self, evento):
        painter = QtGui.QPainter(self)
        if self._pixmap is not None:
            painter.setOpacity(self._opacidade)
            painter.drawPixmap(self.rect(), self._pixmap)
            painter.setOpacity(1.0)
        if not self.docker.modo_fixado:
            caneta = QtGui.QPen(QtGui.QColor(20, 20, 20, 170))
            caneta.setStyle(PEN_STYLE_DASH)
            painter.setPen(caneta)
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
            painter.fillRect(self._retangulo_alca(), QtGui.QColor(20, 20, 20, 170))
        painter.end()

    def mousePressEvent(self, evento):
        posicao = _posicao(evento)
        self._ultimo = posicao
        self._redimensionando = self._retangulo_alca().contains(posicao)
        self._arrastando = not self._redimensionando
        if self._redimensionando:
            self.setCursor(CURSOR_SIZE_FDIAG)

    def mouseMoveEvent(self, evento):
        if self._ultimo is None:
            return
        posicao = _posicao(evento)
        delta = posicao - self._ultimo
        if self._redimensionando:
            variacao = delta.x() if abs(delta.x()) >= abs(delta.y()) else delta.y()
            largura = max(self.TAMANHO_MINIMO, self.width() + variacao)
            altura = max(self.TAMANHO_MINIMO, self._altura_para(largura))
            self.resize(largura, altura)
        elif self._arrastando:
            self.move(self.pos() + delta)
        self._ultimo = posicao

    def mouseReleaseEvent(self, evento):
        if self._redimensionando:
            self.docker.atualizar_flutuante()
        self._ultimo = None
        self._arrastando = False
        self._redimensionando = False
        self.setCursor(CURSOR_SIZE_ALL if not self.docker.modo_fixado else CURSOR_ARROW)

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


class Viewer3DDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: 3D'))
        registro.registrar("viewer3d", self)
        self.modelo = None
        self.corpo = "homem"
        self.regiao = None
        self.semantica = {}
        self.pose_atual = None
        self.modo_mover = False
        self.modo_fixado = False
        self.camera = {
            "yaw": 0.0,
            "pitch": -10.0,
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }
        self._tela = []
        self._canvas = None
        self._flutuante = None
        self._selecao_flutuante = None
        self._offset_preview = (0, 0)
        self._tamanho_render = (0, 0)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self.atualizar_preview)
        self._build_ui()
        try:
            self.widget().destroyed.connect(self._fechar_flutuante)
        except (AttributeError, TypeError):
            pass
        self._carregar_modelo(aplicar_padrao=True)

    def canvasChanged(self, canvas):
        self._canvas = canvas
        if self._flutuante is not None:
            self._criar_flutuante()

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        self.preview = _Preview(self)
        layout.addWidget(self.preview, 1)

        layout.addWidget(ui.rotulo(
            i18n.t('Clique sobre a parte do corpo que deseja rotacionar.')
        ))

        self.lbl_regiao = ui.rotulo_info(i18n.t('Nenhuma região selecionada.'))
        layout.addWidget(self.lbl_regiao)

        corpo_row = widgets.QHBoxLayout()
        corpo_row.addWidget(ui.rotulo(i18n.t('Corpo:')))
        self.cmb_corpo = widgets.QComboBox()
        for chave, rotulo, _ in VIEWER3D_MODELOS:
            self.cmb_corpo.addItem(rotulo, chave)
        self.cmb_corpo.currentIndexChanged.connect(self._mudar_corpo)
        corpo_row.addWidget(self.cmb_corpo, 1)
        layout.addLayout(corpo_row)

        pose_row = widgets.QHBoxLayout()
        pose_row.addWidget(ui.rotulo(i18n.t('Pose:')))
        self.cmb_pose = widgets.QComboBox()
        self.cmb_pose.currentIndexChanged.connect(self._mudar_pose)
        pose_row.addWidget(self.cmb_pose, 1)
        layout.addLayout(pose_row)

        estilo_row = widgets.QHBoxLayout()
        estilo_row.addWidget(ui.rotulo(i18n.t('Estilo:')))
        self.cmb_estilo = widgets.QComboBox()
        self.cmb_estilo.addItem(i18n.t('Sombreado'), "sombreado")
        self.cmb_estilo.addItem(i18n.t('Silhueta'), "silhueta")
        self.cmb_estilo.addItem(i18n.t('Contorno'), "contorno")
        self.cmb_estilo.currentIndexChanged.connect(self.agendar_render)
        estilo_row.addWidget(self.cmb_estilo, 1)
        layout.addLayout(estilo_row)

        self.grupo_juntas = widgets.QGroupBox(i18n.t('Juntas'))
        self.juntas_layout = ui.espacamento(
            widgets.QVBoxLayout(self.grupo_juntas), margem=0, espaco=ui.GAP
        )
        layout.addWidget(self.grupo_juntas)

        cameras = widgets.QHBoxLayout()
        button_front = ui.botao(
            i18n.t('Frente'), i18n.t('Volta à vista frontal (ângulo, zoom e enquadramento).')
        )
        button_front.clicked.connect(self.reset_camera)
        cameras.addWidget(button_front)
        button_fit = ui.botao(
            i18n.t('Enquadrar'), i18n.t('Centraliza o modelo e volta ao zoom 1, sem mudar o ângulo.')
        )
        button_fit.clicked.connect(self.enquadrar)
        cameras.addWidget(button_fit)
        button_zoom_out = ui.botao(i18n.t('−'), i18n.t('Diminui o zoom.'))
        button_zoom_out.clicked.connect(lambda: self.aplicar_zoom(0.8))
        cameras.addWidget(button_zoom_out)
        button_zoom_in = ui.botao(i18n.t('+'), i18n.t('Aumenta o zoom.'))
        button_zoom_in.clicked.connect(lambda: self.aplicar_zoom(1.25))
        cameras.addWidget(button_zoom_in)
        layout.addLayout(cameras)

        posse = widgets.QHBoxLayout()
        button_reset = ui.botao(i18n.t('Limpar pose'), i18n.t('Zera todas as juntas.'))
        button_reset.clicked.connect(self.limpar_pose)
        posse.addWidget(button_reset)
        self.button_move = ui.botao(
            i18n.t('Mover'),
            i18n.t('Ligado, arrastar desloca o enquadramento em vez de girar (ou use Shift/botão do meio).'),
        )
        self.button_move.setCheckable(True)
        self.button_move.toggled.connect(self._alternar_mover)
        posse.addWidget(self.button_move)
        layout.addLayout(posse)

        flutuante = widgets.QHBoxLayout()
        self.button_flutuar = ui.botao(
            i18n.t('Flutuar na página'),
            i18n.t('Mostra o preview sobre a seleção (desenhe uma seleção retangular sobre o painel primeiro); arraste e redimensione à vontade.'),
            icone_chave="novo",
        )
        self.button_flutuar.setCheckable(True)
        self.button_flutuar.toggled.connect(self._alternar_flutuar)
        flutuante.addWidget(self.button_flutuar)
        self.button_fixar = ui.botao(
            i18n.t('Fixar'),
            i18n.t('Com o flutuante fixado, o mouse atravessa e você desenha por baixo.'),
        )
        self.button_fixar.setCheckable(True)
        self.button_fixar.setEnabled(False)
        self.button_fixar.toggled.connect(self._alternar_fixar)
        flutuante.addWidget(self.button_fixar)
        layout.addLayout(flutuante)

        opacidade = widgets.QHBoxLayout()
        opacidade.addWidget(ui.rotulo(i18n.t('Opacidade:')))
        self.sld_opacidade = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        self.sld_opacidade.setRange(20, 100)
        self.sld_opacidade.setValue(80)
        self.lbl_opacidade = ui.rotulo_info(i18n.t('80%'))
        self.sld_opacidade.valueChanged.connect(self._mudar_opacidade)
        opacidade.addWidget(self.sld_opacidade, 1)
        opacidade.addWidget(self.lbl_opacidade)
        layout.addLayout(opacidade)

        acoes = widgets.QHBoxLayout()
        button_layer = ui.botao(
            i18n.t('Inserir como camada'),
            i18n.t('Insere na seleção ativa (desenhe uma seleção retangular sobre o painel); a camada entra abaixo da camada ativa, para o esboço ficar por cima, e a seleção é desfeita.'),
            icone_chave="aplicar",
        )
        button_layer.clicked.connect(lambda: self.inserir(referencia=False))
        acoes.addWidget(button_layer)
        button_ref = ui.botao(
            i18n.t('Inserir como referência'),
            i18n.t('Insere na seleção ativa, travado, com rótulo de cor e opacidade reduzida, abaixo da camada ativa; a seleção é desfeita.'),
        )
        button_ref.clicked.connect(lambda: self.inserir(referencia=True))
        acoes.addWidget(button_ref)
        layout.addLayout(acoes)

        layout.addWidget(ui.rotulo(
            i18n.t("1) Desenhe uma seleção retangular sobre o painel. 2) Ajuste a pose e o zoom (o preview mostra exatamente o recorte que será inserido). 3) 'Inserir' coloca a camada abaixo da ativa e desfaz a seleção. Arraste para orbitar; Shift+arraste desloca; roda ou +/− dão zoom; clique numa região para abrir os sliders.")
        ))

        self.setWidget(main)

    def _caminho_do_corpo(self, chave):
        for chave_modelo, _, caminho in VIEWER3D_MODELOS:
            if chave_modelo == chave:
                return caminho
        return None

    def _carregar_modelo(self, aplicar_padrao=False):
        try:
            self.modelo = modelo3d.Modelo.carregar(self._caminho_do_corpo(self.corpo))
        except (OSError, ValueError) as error:
            self.lbl_regiao.setText(i18n.t('Modelo 3D indisponível: {0}').format(error))
            return
        self._popular_poses()
        if aplicar_padrao:
            self._aplicar_pose(VIEWER3D_POSE_PADRAO)
        if self.regiao is None:
            self._selecionar_regiao("tronco")
        else:
            self._montar_sliders()
        self.atualizar_preview()

    def _popular_poses(self):
        self.cmb_pose.blockSignals(True)
        self.cmb_pose.clear()
        self.cmb_pose.addItem(i18n.t('—'), None)
        try:
            arquivos = sorted(os.listdir(VIEWER3D_POSES_DIR))
        except OSError:
            arquivos = []
        for arquivo in arquivos:
            if not arquivo.endswith(".json"):
                continue
            try:
                dados = modelo3d.carregar_pose(os.path.join(VIEWER3D_POSES_DIR, arquivo))
                rotulo = dados.get("nome") or arquivo[:-5]
            except (OSError, ValueError):
                rotulo = arquivo[:-5]
            self.cmb_pose.addItem(rotulo, arquivo)
        indice = self.cmb_pose.findData(self.pose_atual)
        self.cmb_pose.setCurrentIndex(indice if indice >= 0 else 0)
        self.cmb_pose.blockSignals(False)

    def _sincronizar_combo_pose(self):
        indice = self.cmb_pose.findData(self.pose_atual)
        self.cmb_pose.blockSignals(True)
        self.cmb_pose.setCurrentIndex(indice if indice >= 0 else 0)
        self.cmb_pose.blockSignals(False)

    def _mudar_corpo(self, indice):
        chave = self.cmb_corpo.itemData(indice)
        if chave:
            self.corpo = chave
            self._carregar_modelo()

    def _mudar_pose(self, indice):
        arquivo = self.cmb_pose.itemData(indice)
        if arquivo is None:
            self.limpar_pose()
            return
        self._aplicar_pose(arquivo)

    def _aplicar_pose(self, arquivo):
        try:
            dados = modelo3d.carregar_pose(os.path.join(VIEWER3D_POSES_DIR, arquivo))
        except (OSError, ValueError) as error:
            helpers.show_info(i18n.t('3D'), i18n.t('Não foi possível ler a pose: {0}').format(error))
            return
        self.semantica = {
            osso: dict(valores) for osso, valores in dados.get("ossos", {}).items()
        }
        self.pose_atual = arquivo
        self._sincronizar_combo_pose()
        self._montar_sliders()
        self.agendar_render()

    def _rotacoes(self):
        if self.modelo is None:
            return {}
        return self.modelo.aplicar_semantica(self.semantica)

    def agendar_render(self):
        self._timer.start()

    def _estilo(self):
        dados = self.cmb_estilo.currentData()
        if dados == "silhueta":
            return "chapado", "#141414", "#ffffff"
        if dados == "contorno":
            return "contorno", "#141414", "#ffffff"
        return "sombreado", None, None

    def _pan_em_pixels(self, largura, altura):
        """Converte o pan relativo (fração da menor dimensão) em pixels."""
        minimo = max(1.0, float(min(largura, altura)))
        return self.camera["pan_x"] * minimo, self.camera["pan_y"] * minimo

    def _render_svg(self, largura, altura, com_fundo=True, posados=None):
        estilo, cor, fundo = self._estilo()
        if not com_fundo:
            fundo = None
        if posados is None:
            posados = self.modelo.vertices_em_pose(self._rotacoes())
        pan_x, pan_y = self._pan_em_pixels(largura, altura)
        return self.modelo.renderizar(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            pan_x=pan_x,
            pan_y=pan_y,
            largura=largura,
            altura=altura,
            posados=posados,
            estilo=estilo,
            cor=cor,
            fundo=fundo,
        )

    @staticmethod
    def _rasterizar(svg, largura, altura):
        renderer = QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
        imagem = QImage(largura, altura, IMAGE_FORMAT_RGBA8888)
        imagem.fill(TRANSPARENT)
        painter = QtGui.QPainter(imagem)
        renderer.render(painter)
        painter.end()
        return imagem

    def _tamanho_do_preview(self):
        """Tamanho do render: a proporção da seleção quando ela existe.

        É o que garante o WYSIWYG: o preview mostra o mesmo recorte que a
        seleção vai receber, em qualquer zoom da câmera.
        """
        largura = max(self.preview.width(), 200)
        altura = max(self.preview.height(), 200)
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
        if self.modelo is None:
            return
        largura, altura = self._tamanho_do_preview()
        pan_x, pan_y = self._pan_em_pixels(largura, altura)
        posados = self.modelo.vertices_em_pose(self._rotacoes())
        self._tela = self.modelo.vertices_em_tela(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            pan_x=pan_x,
            pan_y=pan_y,
            largura=largura,
            altura=altura,
            posados=posados,
        )
        if QSvgRenderer is None:
            return
        svg = self._render_svg(largura, altura, posados=posados)
        imagem = self._rasterizar(svg, largura, altura)
        self.preview.setPixmap(QtGui.QPixmap.fromImage(imagem))
        self._tamanho_render = (largura, altura)
        self._offset_preview = (
            max(0, (self.preview.width() - largura) // 2),
            max(0, (self.preview.height() - altura) // 2),
        )
        self._atualizar_flutuante(posados)
        self._sincronizar_flutuante()

    def atualizar_flutuante(self):
        self._atualizar_flutuante()

    def _atualizar_flutuante(self, posados=None):
        if self._flutuante is None or QSvgRenderer is None or self.modelo is None:
            return
        largura = max(self._flutuante.width(), 60)
        altura = max(self._flutuante.height(), 60)
        svg = self._render_svg(largura, altura, com_fundo=False, posados=posados)
        imagem = self._rasterizar(svg, largura, altura)
        self._flutuante.definir_pixmap(QtGui.QPixmap.fromImage(imagem))

    def _alternar_flutuar(self, ligado):
        if ligado:
            self._criar_flutuante()
        else:
            self._fechar_flutuante()

    def _criar_flutuante(self):
        view = helpers.active_view()
        documento = view.document() if view is not None else None
        if documento is None:
            helpers.show_info(i18n.t('3D'), i18n.t('Abra um documento para usar o flutuante.'))
            self.button_flutuar.setChecked(False)
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                i18n.t('3D'),
                i18n.t('Desenhe uma seleção retangular sobre o painel para usar o flutuante.'),
            )
            self.button_flutuar.setChecked(False)
            return
        viewport = _viewport_da_view(view)
        if viewport is None:
            helpers.show_info(i18n.t('3D'), i18n.t('Não foi possível ancorar o flutuante nesta janela.'))
            self.button_flutuar.setChecked(False)
            return
        self._fechar_flutuante()
        self._flutuante = _Flutuante(self, viewport)
        self._flutuante.definir_aspecto(selecao[2] / float(selecao[3]))
        self._flutuante.definir_opacidade(self.sld_opacidade.value() / 100.0)
        self._selecao_flutuante = selecao
        self._posicionar_flutuante(viewport, selecao)
        self._flutuante.show()
        self._flutuante.raise_()
        self.button_fixar.setEnabled(True)
        self.button_fixar.setChecked(False)
        self.modo_fixado = False
        self._atualizar_flutuante()

    def _posicionar_flutuante(self, viewport, selecao):
        """Coloca a janela sobre a seleção, com a proporção dela."""
        if self._flutuante is None:
            return
        documento = helpers.active_document()
        if documento is None:
            return
        parametros = self._parametros_do_canvas(documento, viewport)
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
        altura = max(
            _Flutuante.TAMANHO_MINIMO, int(round(largura / aspecto))
        )
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
            self._atualizar_flutuante()

    def _cancelar_flutuante(self):
        """Fecha o flutuante e desmarca o botão (seleção sumiu ou mudou)."""
        if getattr(self, "button_flutar", None) is not None:
            try:
                self.button_flutar.setChecked(False)
            except RuntimeError:
                pass
        self._fechar_flutuante()

    def _fechar_flutuante(self):
        if self._flutuante is not None:
            self._flutuante.hide()
            self._flutuante.deleteLater()
            self._flutuante = None
        self._selecao_flutuante = None
        if getattr(self, "button_fixar", None) is not None:
            try:
                self.button_fixar.setChecked(False)
                self.button_fixar.setEnabled(False)
            except RuntimeError:
                pass
        self.modo_fixado = False

    def _alternar_fixar(self, ligado):
        self.modo_fixado = bool(ligado)
        if self._flutuante is not None:
            self._flutuante.setAttribute(WA_TRANSPARENT_FOR_MOUSE, self.modo_fixado)
            self._flutuante.setCursor(
                CURSOR_ARROW if self.modo_fixado else CURSOR_SIZE_ALL
            )
            self._flutuante.update()

    def _mudar_opacidade(self, valor):
        self.lbl_opacidade.setText(i18n.t('{0}%').format(valor))
        if self._flutuante is not None:
            self._flutuante.definir_opacidade(valor / 100.0)

    def orbitar(self, dx, dy):
        self.camera["yaw"] = (self.camera["yaw"] + dx * 0.5) % 360.0
        self.camera["pitch"] = max(-89.0, min(89.0, self.camera["pitch"] + dy * 0.5))
        self.agendar_render()

    def aplicar_zoom(self, fator):
        # Até 12x: dá para enquadrar detalhes (uma mão, um rosto) na seleção.
        self.camera["zoom"] = max(0.3, min(12.0, self.camera["zoom"] * fator))
        self.agendar_render()

    def deslocar(self, dx, dy):
        # Pan relativo à menor dimensão: assim o enquadramento chega igual na
        # seleção, independente do tamanho do preview (WYSIWYG).
        minimo = max(1.0, float(min(self.preview.width(), self.preview.height())))
        self.camera["pan_x"] += dx / minimo
        self.camera["pan_y"] += dy / minimo
        self.agendar_render()

    def enquadrar(self):
        self.camera["zoom"] = 1.0
        self.camera["pan_x"] = 0.0
        self.camera["pan_y"] = 0.0
        self.agendar_render()

    def _alternar_mover(self, ligado):
        self.modo_mover = bool(ligado)

    def reset_camera(self):
        self.camera = {
            "yaw": 0.0,
            "pitch": -10.0,
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }
        self.agendar_render()

    def limpar_pose(self):
        self.semantica = {}
        self.pose_atual = None
        self._sincronizar_combo_pose()
        self._montar_sliders()
        self.agendar_render()

    def selecionar_em(self, x, y):
        if self.modelo is None or not self._tela:
            return
        x -= self._offset_preview[0]
        y -= self._offset_preview[1]
        if (
            x < 0
            or y < 0
            or x > self._tamanho_render[0]
            or y > self._tamanho_render[1]
        ):
            return
        melhor = None
        for indice, (tela_x, tela_y, _) in enumerate(self._tela):
            distancia = (tela_x - x) ** 2 + (tela_y - y) ** 2
            if melhor is None or distancia < melhor[0]:
                melhor = (distancia, indice)
        if melhor is None or melhor[0] > 48 ** 2:
            return
        pesos = self.modelo.pesos[melhor[1]]
        if not pesos:
            return
        osso = max(pesos, key=lambda par: par[1])[0]
        nome = self.modelo.ossos[osso]["nome"]
        regiao = self._regiao_do_osso(nome)
        if regiao is not None:
            self._selecionar_regiao(regiao)

    def _regiao_do_osso(self, nome):
        for chave, _, ossos in REGIOES:
            if nome in ossos:
                return chave
        if nome.startswith(FAMILIAS_DEDO):
            if nome.endswith(".l"):
                return "braco_esq"
            if nome.endswith(".r"):
                return "braco_dir"
        return None

    def _selecionar_regiao(self, chave):
        self.regiao = chave
        self._montar_sliders()

    def _limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            filho = item.layout()
            if filho is not None:
                self._limpar_layout(filho)
                filho.deleteLater()
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _linha_slider(self, osso, chave, rotulo):
        widgets = QtWidgets
        linha = widgets.QHBoxLayout()
        linha.addWidget(ui.rotulo(rotulo))
        slider = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        slider.setRange(-LIMITE_SLIDER, LIMITE_SLIDER)
        slider.setValue(int(self.semantica.get(osso, {}).get(chave, 0)))
        valor = ui.rotulo_info(i18n.t('0°'))
        slider.valueChanged.connect(
            lambda novo, o=osso, c=chave, etiqueta=valor: self._mudar_junta(
                o, c, novo, etiqueta
            )
        )
        linha.addWidget(slider, 1)
        linha.addWidget(valor)
        return linha

    def _mudar_junta(self, osso, chave, valor, etiqueta):
        self.semantica.setdefault(osso, {})[chave] = float(valor)
        etiqueta.setText(i18n.t('{0}°').format(valor))
        self.agendar_render()

    def _linha_dedos(self, lado):
        ossos = [
            osso["nome"]
            for osso in self.modelo.ossos
            if osso["nome"].startswith(FAMILIAS_DEDO)
            and osso["nome"].endswith("." + lado)
        ]
        if not ossos:
            return None
        widgets = QtWidgets
        linha = widgets.QHBoxLayout()
        linha.addWidget(ui.rotulo(i18n.t('Dedos · Dobrar')))
        slider = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        slider.setRange(-LIMITE_SLIDER, LIMITE_SLIDER)
        slider.setValue(int(self.semantica.get(ossos[0], {}).get("dobrar", 0)))
        valor = ui.rotulo_info(i18n.t('0°'))
        slider.valueChanged.connect(
            lambda novo, alvos=tuple(ossos), etiqueta=valor: self._mudar_dedos(
                alvos, novo, etiqueta
            )
        )
        linha.addWidget(slider, 1)
        linha.addWidget(valor)
        return linha

    def _mudar_dedos(self, ossos, valor, etiqueta):
        for osso in ossos:
            self.semantica.setdefault(osso, {})["dobrar"] = float(valor)
        etiqueta.setText(i18n.t('{0}°').format(valor))
        self.agendar_render()

    def _montar_sliders(self):
        self._limpar_layout(self.juntas_layout)
        if self.modelo is None or self.regiao is None:
            self.grupo_juntas.setTitle("Juntas")
            return
        for chave, nome, ossos in REGIOES:
            if chave == self.regiao:
                break
        else:
            return
        self.grupo_juntas.setTitle("Juntas: {0}".format(nome))
        self.lbl_regiao.setText(i18n.t('Região: {0}').format(nome))
        for osso in ossos:
            for eixo in EIXOS_POR_BASE.get(_base(osso), ("dobrar",)):
                self.juntas_layout.addLayout(self._linha_slider(
                    osso, eixo, "{0} · {1}".format(nome_amigavel(osso), ROTULOS[eixo])
                ))
        lado = _lado(self.regiao)
        if self.regiao.startswith("braco") and lado:
            linha = self._linha_dedos(lado)
            if linha is not None:
                self.juntas_layout.addLayout(linha)

    def _parametros_do_canvas(self, documento, viewport):
        """(centro_widget, centro_imagem, zoom, rotacao, pan, espelhado) ou None.

        Em modo pixel (o padrão do Krita), a escala de tela é ``zoomLevel``:
        em 100%, um pixel da imagem vira um pixel do widget. O ``72/resolution``
        do exemplo da comunidade valia para o modo de resolução de impressão e
        deixava o mapeamento ~4x maior em 300 dpi (a imagem "gigante").
        """
        view = helpers.active_view()
        canvas = view.canvas() if view is not None else None
        if canvas is None:
            return None
        try:
            zoom = canvas.zoomLevel()
        except (AttributeError, RuntimeError):
            return None
        if zoom <= 0:
            return None
        try:
            rotacao = canvas.rotation()
        except (AttributeError, RuntimeError):
            rotacao = 0.0
        try:
            espelhado = canvas.mirror()
        except (AttributeError, RuntimeError):
            espelhado = False
        centro_imagem = (documento.width() / 2.0, documento.height() / 2.0)
        pan = self._pan_do_viewport(viewport)
        centro_widget = (viewport.width() / 2.0, viewport.height() / 2.0)
        return centro_widget, centro_imagem, zoom, rotacao, pan, espelhado

    @staticmethod
    def _pan_do_viewport(viewport):
        area = viewport.parentWidget()
        if area is None:
            return (0.0, 0.0)
        try:
            horizontal = area.horizontalScrollBar()
            vertical = area.verticalScrollBar()
        except (AttributeError, RuntimeError):
            return (0.0, 0.0)
        return (
            mapeamento.deslocamento_da_barra(
                horizontal.minimum(), horizontal.maximum(), horizontal.value()
            ),
            mapeamento.deslocamento_da_barra(
                vertical.minimum(), vertical.maximum(), vertical.value()
            ),
        )

    def inserir(self, referencia=False):
        if self.modelo is None:
            helpers.show_info(i18n.t('3D'), i18n.t('O modelo não está disponível.'))
            return
        documento = helpers.active_document()
        if documento is None:
            helpers.show_info(i18n.t('3D'), i18n.t('Abra um documento para inserir o desenho.'))
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                i18n.t('3D'),
                i18n.t('Desenhe uma seleção retangular sobre o painel de destino para inserir.'),
            )
            return
        x, y, largura, altura = selecao
        ativo = documento.activeNode()
        nome_ativo = ativo.name() if ativo is not None else None
        svg = self._render_svg(largura, altura, com_fundo=False)
        imagem = self._rasterizar(svg, largura, altura)
        rgba = imagem.convertToFormat(IMAGE_FORMAT_RGBA8888)
        dados = bytes(rgba.constBits().asstring(rgba.sizeInBytes()))
        nome = helpers.unique_layer_name(documento, "3D")
        camada = documento.createNode(nome, "paintlayer")
        if camada is None or not camada.setPixelData(dados, x, y, largura, altura):
            helpers.show_info(i18n.t('3D'), i18n.t('Não foi possível criar a camada.'))
            return
        helpers.attach_below_active(documento, camada)
        if referencia:
            camada.setColorLabel(1)
            camada.setLocked(True)
            camada.setOpacity(150)
        documento.setActiveNode(camada)
        helpers.deselect(documento)
        documento.refreshProjection()
        self._sincronizar_flutuante()
        helpers.show_message(
            i18n.t("Camada '{0}' inserida abaixo de '{1}'{2}; seleção desfeita.").format(
                nome,
                nome_ativo or "camada ativa",
                " como referência" if referencia else "",
            )
        )
