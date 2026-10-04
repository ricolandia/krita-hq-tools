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
from ...core import ui
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
        self._arrastando = False
        self._redimensionando = False
        self._ultimo = None

    def definir_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def definir_opacidade(self, valor):
        self._opacidade = max(0.1, min(1.0, float(valor)))
        self.update()

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
            largura = max(self.TAMANHO_MINIMO, self.width() + delta.x())
            altura = max(self.TAMANHO_MINIMO, self.height() + delta.y())
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
        altura = max(self.TAMANHO_MINIMO, int(round(self.height() * fator)))
        centro = self.rect().center()
        self.resize(largura, altura)
        self.move(self.pos() + centro - self.rect().center())
        self.docker.atualizar_flutuante()


class Viewer3DDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: 3D")
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
            "Clique sobre a parte do corpo que deseja rotacionar."
        ))

        self.lbl_regiao = ui.rotulo_info("Nenhuma região selecionada.")
        layout.addWidget(self.lbl_regiao)

        corpo_row = widgets.QHBoxLayout()
        corpo_row.addWidget(ui.rotulo("Corpo:"))
        self.cmb_corpo = widgets.QComboBox()
        for chave, rotulo, _ in VIEWER3D_MODELOS:
            self.cmb_corpo.addItem(rotulo, chave)
        self.cmb_corpo.currentIndexChanged.connect(self._mudar_corpo)
        corpo_row.addWidget(self.cmb_corpo, 1)
        layout.addLayout(corpo_row)

        pose_row = widgets.QHBoxLayout()
        pose_row.addWidget(ui.rotulo("Pose:"))
        self.cmb_pose = widgets.QComboBox()
        self.cmb_pose.currentIndexChanged.connect(self._mudar_pose)
        pose_row.addWidget(self.cmb_pose, 1)
        layout.addLayout(pose_row)

        estilo_row = widgets.QHBoxLayout()
        estilo_row.addWidget(ui.rotulo("Estilo:"))
        self.cmb_estilo = widgets.QComboBox()
        self.cmb_estilo.addItem("Sombreado", "sombreado")
        self.cmb_estilo.addItem("Silhueta", "silhueta")
        self.cmb_estilo.addItem("Contorno", "contorno")
        self.cmb_estilo.currentIndexChanged.connect(self.agendar_render)
        estilo_row.addWidget(self.cmb_estilo, 1)
        layout.addLayout(estilo_row)

        self.grupo_juntas = widgets.QGroupBox("Juntas")
        self.juntas_layout = ui.espacamento(
            widgets.QVBoxLayout(self.grupo_juntas), margem=0, espaco=ui.GAP
        )
        layout.addWidget(self.grupo_juntas)

        cameras = widgets.QHBoxLayout()
        button_front = ui.botao(
            "Frente", "Volta à vista frontal (ângulo, zoom e enquadramento)."
        )
        button_front.clicked.connect(self.reset_camera)
        cameras.addWidget(button_front)
        button_fit = ui.botao(
            "Enquadrar", "Centraliza o modelo e volta ao zoom 1, sem mudar o ângulo."
        )
        button_fit.clicked.connect(self.enquadrar)
        cameras.addWidget(button_fit)
        button_zoom_out = ui.botao("−", "Diminui o zoom.")
        button_zoom_out.clicked.connect(lambda: self.aplicar_zoom(0.8))
        cameras.addWidget(button_zoom_out)
        button_zoom_in = ui.botao("+", "Aumenta o zoom.")
        button_zoom_in.clicked.connect(lambda: self.aplicar_zoom(1.25))
        cameras.addWidget(button_zoom_in)
        layout.addLayout(cameras)

        posse = widgets.QHBoxLayout()
        button_reset = ui.botao("Limpar pose", "Zera todas as juntas.")
        button_reset.clicked.connect(self.limpar_pose)
        posse.addWidget(button_reset)
        self.button_move = ui.botao(
            "Mover",
            "Ligado, arrastar desloca o enquadramento em vez de girar "
            "(ou use Shift/botão do meio).",
        )
        self.button_move.setCheckable(True)
        self.button_move.toggled.connect(self._alternar_mover)
        posse.addWidget(self.button_move)
        layout.addLayout(posse)

        flutuante = widgets.QHBoxLayout()
        self.button_flutuar = ui.botao(
            "Flutuar na página",
            "Mostra o preview flutuante sobre o canvas para posicionar a "
            "referência; arraste e redimensione antes de inserir.",
            icone_chave="novo",
        )
        self.button_flutuar.setCheckable(True)
        self.button_flutuar.toggled.connect(self._alternar_flutuar)
        flutuante.addWidget(self.button_flutuar)
        self.button_fixar = ui.botao(
            "Fixar",
            "Com o flutuante fixado, o mouse atravessa e você desenha por baixo.",
        )
        self.button_fixar.setCheckable(True)
        self.button_fixar.setEnabled(False)
        self.button_fixar.toggled.connect(self._alternar_fixar)
        flutuante.addWidget(self.button_fixar)
        layout.addLayout(flutuante)

        opacidade = widgets.QHBoxLayout()
        opacidade.addWidget(ui.rotulo("Opacidade:"))
        self.sld_opacidade = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        self.sld_opacidade.setRange(20, 100)
        self.sld_opacidade.setValue(80)
        self.lbl_opacidade = ui.rotulo_info("80%")
        self.sld_opacidade.valueChanged.connect(self._mudar_opacidade)
        opacidade.addWidget(self.sld_opacidade, 1)
        opacidade.addWidget(self.lbl_opacidade)
        layout.addLayout(opacidade)

        acoes = widgets.QHBoxLayout()
        button_layer = ui.botao(
            "Inserir como camada",
            "Rasteriza o preview no lugar e no tamanho do flutuante (ou no "
            "documento inteiro, sem ele); a camada entra abaixo da camada "
            "ativa, para o esboço ficar por cima.",
            icone_chave="aplicar",
        )
        button_layer.clicked.connect(lambda: self.inserir(referencia=False))
        acoes.addWidget(button_layer)
        button_ref = ui.botao(
            "Inserir como referência",
            "Insere o preview travado, com rótulo de cor e opacidade reduzida, "
            "no lugar do flutuante.",
        )
        button_ref.clicked.connect(lambda: self.inserir(referencia=True))
        acoes.addWidget(button_ref)
        layout.addLayout(acoes)

        layout.addWidget(ui.rotulo(
            "Arraste para orbitar; Shift+arraste (ou botão do meio) desloca; "
            "roda do mouse ou +/− dão zoom; clique numa região para abrir os "
            "sliders. 'Flutuar na página' mostra o preview sobre o canvas "
            "para posicionar a referência antes de inserir; a inserção entra "
            "abaixo da camada ativa, para o esboço ficar por cima."
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
            self.lbl_regiao.setText("Modelo 3D indisponível: {0}".format(error))
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
        self.cmb_pose.addItem("—", None)
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
            helpers.show_info("3D", "Não foi possível ler a pose: {0}".format(error))
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

    def _render_svg(self, largura, altura, com_fundo=True, posados=None):
        estilo, cor, fundo = self._estilo()
        if not com_fundo:
            fundo = None
        if posados is None:
            posados = self.modelo.vertices_em_pose(self._rotacoes())
        return self.modelo.renderizar(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            pan_x=self.camera["pan_x"],
            pan_y=self.camera["pan_y"],
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

    def atualizar_preview(self):
        if self.modelo is None:
            return
        largura = max(self.preview.width(), 200)
        altura = max(self.preview.height(), 200)
        posados = self.modelo.vertices_em_pose(self._rotacoes())
        self._tela = self.modelo.vertices_em_tela(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            pan_x=self.camera["pan_x"],
            pan_y=self.camera["pan_y"],
            largura=largura,
            altura=altura,
            posados=posados,
        )
        if QSvgRenderer is None:
            return
        svg = self._render_svg(largura, altura, posados=posados)
        imagem = self._rasterizar(svg, largura, altura)
        self.preview.setPixmap(QtGui.QPixmap.fromImage(imagem))
        self._atualizar_flutuante(posados)

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
        if view is None or view.document() is None:
            helpers.show_info("3D", "Abra um documento para usar o flutuante.")
            self.button_flutuar.setChecked(False)
            return
        viewport = _viewport_da_view(view)
        if viewport is None:
            helpers.show_info("3D", "Não foi possível ancorar o flutuante nesta janela.")
            self.button_flutuar.setChecked(False)
            return
        self._fechar_flutuante()
        self._flutuante = _Flutuante(self, viewport)
        largura = min(320, max(160, viewport.width() // 3))
        altura = int(largura * 1.25)
        self._flutuante.setGeometry(
            max(0, (viewport.width() - largura) // 2),
            max(0, (viewport.height() - altura) // 2),
            largura,
            altura,
        )
        self._flutuante.definir_opacidade(self.sld_opacidade.value() / 100.0)
        self._flutuante.show()
        self._flutuante.raise_()
        self.button_fixar.setEnabled(True)
        self.button_fixar.setChecked(False)
        self.modo_fixado = False
        self._atualizar_flutuante()

    def _fechar_flutuante(self):
        if self._flutuante is not None:
            self._flutuante.hide()
            self._flutuante.deleteLater()
            self._flutuante = None
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
        self.lbl_opacidade.setText("{0}%".format(valor))
        if self._flutuante is not None:
            self._flutuante.definir_opacidade(valor / 100.0)

    def orbitar(self, dx, dy):
        self.camera["yaw"] = (self.camera["yaw"] + dx * 0.5) % 360.0
        self.camera["pitch"] = max(-89.0, min(89.0, self.camera["pitch"] + dy * 0.5))
        self.agendar_render()

    def aplicar_zoom(self, fator):
        self.camera["zoom"] = max(0.3, min(4.0, self.camera["zoom"] * fator))
        self.agendar_render()

    def deslocar(self, dx, dy):
        self.camera["pan_x"] += dx
        self.camera["pan_y"] += dy
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
        valor = ui.rotulo_info("0°")
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
        etiqueta.setText("{0}°".format(valor))
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
        linha.addWidget(ui.rotulo("Dedos · Dobrar"))
        slider = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        slider.setRange(-LIMITE_SLIDER, LIMITE_SLIDER)
        slider.setValue(int(self.semantica.get(ossos[0], {}).get("dobrar", 0)))
        valor = ui.rotulo_info("0°")
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
        etiqueta.setText("{0}°".format(valor))
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
        self.lbl_regiao.setText("Região: {0}".format(nome))
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

    def _mapear_flutuante(self, documento):
        """Retângulo do flutuante em pixels do documento, ou None."""
        if self._flutuante is None:
            return None
        view = helpers.active_view()
        if view is None:
            return None
        viewport = self._flutuante.parentWidget()
        if viewport is None:
            return None
        canvas = view.canvas()
        try:
            zoom = canvas.zoomLevel() * 72.0 / documento.resolution()
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
        # Âncora pelo centro do documento + barras de rolagem, e não pelo
        # Canvas.preferredCenter(): ele é o ponto de apoio das transformações
        # (still point), não o centro atual do widget depois de rolar.
        centro_imagem = (documento.width() / 2.0, documento.height() / 2.0)
        pan = self._pan_do_viewport(viewport)
        centro_widget = (viewport.width() / 2.0, viewport.height() / 2.0)
        retangulo = (
            self._flutuante.x(),
            self._flutuante.y(),
            self._flutuante.width(),
            self._flutuante.height(),
        )
        resultado = mapeamento.retangulo_para_imagem(
            retangulo, centro_widget, centro_imagem, zoom, rotacao, pan, espelhado
        )
        helpers.log(
            "[3D] flutuante {0} -> imagem {1} (zoom {2:.4f}, rotacao {3:.1f}, "
            "espelhado {4}, pan {5})".format(
                retangulo, resultado, zoom, rotacao, espelhado, pan
            )
        )
        return resultado

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
            helpers.show_info("3D", "O modelo não está disponível.")
            return
        documento = helpers.active_document()
        if documento is None:
            helpers.show_info("3D", "Abra um documento para inserir o desenho.")
            return
        ativo = documento.activeNode()
        nome_ativo = ativo.name() if ativo is not None else None
        retangulo = self._mapear_flutuante(documento)
        if retangulo is not None:
            x, y, largura, altura = retangulo
        else:
            x, y = 0, 0
            largura = documento.width()
            altura = documento.height()
        vx, vy, vw, vh = mapeamento.intersecao_com_documento(
            (x, y, largura, altura), documento.width(), documento.height()
        )
        if vw <= 0 or vh <= 0:
            helpers.show_info("3D", "O flutuante está fora do documento.")
            return
        svg = self._render_svg(largura, altura, com_fundo=False)
        imagem = self._rasterizar(svg, largura, altura)
        if (vx, vy, vw, vh) != (x, y, largura, altura):
            imagem = imagem.copy(vx - x, vy - y, vw, vh)
        rgba = imagem.convertToFormat(IMAGE_FORMAT_RGBA8888)
        dados = bytes(rgba.constBits().asstring(rgba.sizeInBytes()))
        nome = helpers.unique_layer_name(documento, "3D")
        camada = documento.createNode(nome, "paintlayer")
        if camada is None or not camada.setPixelData(dados, vx, vy, vw, vh):
            helpers.show_info("3D", "Não foi possível criar a camada.")
            return
        helpers.attach_below_active(documento, camada)
        if referencia:
            camada.setColorLabel(1)
            camada.setLocked(True)
            camada.setOpacity(150)
        documento.setActiveNode(camada)
        documento.refreshProjection()
        helpers.show_message(
            "Camada '{0}' inserida abaixo de '{1}'{2} (para traçar por cima).".format(
                nome,
                nome_ativo or "camada ativa",
                " como referência" if referencia else "",
            )
        )
