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

import json
import os

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core import mapeamento
from ...core import modelo3d
from ...core import registro, ui
from ...core.config import Config
from ...core import i18n
from ...core.compat import (
    ALIGN_CENTER,
    CURSOR_ARROW,
    CURSOR_SIZE_ALL,
    CURSOR_SIZE_FDIAG,
    IMAGE_FORMAT_ARGB32,
    IMAGE_FORMAT_RGBA8888,
    QImage,
    QSvgRenderer,
    SIZE_IGNORED,
    TRANSPARENT,
    WA_NO_SYSTEM_BACKGROUND,
    WA_TRANSLUCENT_BACKGROUND,
    WA_TRANSPARENT_FOR_MOUSE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.paths import (
    RESOURCES_DIR,
    VIEWER3D_MODELOS,
    VIEWER3D_POSE_CORPO_PADRAO,
    VIEWER3D_POSE_MAOS_PADRAO,
    VIEWER3D_POSES_CORPO_DIR,
    VIEWER3D_POSES_MAOS_DIR,
    VIEWER3D_POSES_USUARIO_CORPO_DIR,
    VIEWER3D_POSES_USUARIO_MAOS_DIR,
)

LIMITE_SLIDER = 120
# Slider "Dobrar" dos dedos: 0° = mão aberta (repouso) e 90° = punho. Os
# valores saem da interpolação da pose de referência "fechada" (medida em QA:
# o fechar do dedo mora no eixo "abrir" negativo; "dobrar"/"girar" deformam).
LIMITE_FECHAR_DEDO = 90

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
    shift = getattr(getattr(QtCore.Qt, "KeyboardModifier", QtCore.Qt), "ShiftModifier")
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
        self.setWindowTitle(i18n.t("HQ Tools: 3D"))
        registro.registrar("viewer3d", self)
        self.config = Config()
        self.modelo = None
        self.corpo = "homem"
        self.regiao = None
        self.semantica = {}
        # A pose só muda em _aplicar_poses e nos sliders; a revisão evita
        # recalcular vertices_em_pose a cada tick de câmera (arrasto/zoom).
        self._pose_revisao = 0
        self._posados_cache = None
        self.pose_corpo = VIEWER3D_POSE_CORPO_PADRAO
        # Padrão: as duas mãos fechadas, como antes da separação; cada mão
        # tem a própria caixa de pose.
        self.pose_mao_direita = VIEWER3D_POSE_MAOS_PADRAO
        self.pose_mao_esquerda = VIEWER3D_POSE_MAOS_PADRAO
        self.modo_mover = False
        self.modo_fixado = False
        self.camera = {
            "yaw": 0.0,
            "pitch": -10.0,
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }
        # Ortográfica por padrão (fluxo validado); a perspectiva mantém o
        # enquadramento e muda só a convergência (ver modelo3d.LENTES).
        self.perspectiva = False
        self.lente = modelo3d.LENTES[-1]
        # None = cor padrão do modelo; qualquer outra vale no render, no
        # flutuante e na inserção (a camada inserida é raster).
        self.cor = None
        # Luz do render (azimute e altura em graus, no espaço da câmera): os
        # padrões reproduzem a LUZ_PADRAO do núcleo.
        self.luz_azimute = 26.6
        self.luz_altura = 26.7
        # Mão em ajuste na aba "Mãos" (a pose salva sai na convenção da
        # direita; a esquerda é espelhada ao gravar).
        self.mao_ajuste = modelo3d.LADO_DIREITA
        self._ref_fechada = None
        # Estado salvo: o estilo vem por atributo porque o combo só existe
        # depois de _build_ui.
        self._estilo_salvo = None
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
        # Autosave do estado (config.json): grava com um respiro depois da
        # última mudança; o agendar_render agenda as duas coisas.
        self._salvar_timer = QtCore.QTimer(self)
        self._salvar_timer.setSingleShot(True)
        self._salvar_timer.setInterval(800)
        self._salvar_timer.timeout.connect(self._salvar_estado)
        self._restaurar_estado()
        self._build_ui()
        self._aplicar_estado_nos_combos()
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
        self.preview.setSizePolicy(SIZE_IGNORED, SIZE_IGNORED)
        layout.addWidget(self.preview, 1)

        layout.addWidget(
            ui.rotulo(i18n.t("Clique sobre a parte do corpo que deseja rotacionar."))
        )

        self.lbl_regiao = ui.rotulo_info(i18n.t("Nenhuma região selecionada."))
        layout.addWidget(self.lbl_regiao)

        self.tabs = widgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(ui.rolavel(self._build_pose_tab()), i18n.t("Pose"))
        self.tabs.addTab(ui.rolavel(self._build_maos_tab()), i18n.t("Mãos"))
        self.tabs.addTab(ui.rolavel(self._build_camera_tab()), i18n.t("Câmera"))
        self.tabs.addTab(ui.rolavel(self._build_insert_tab()), i18n.t("Inserir"))

        self.setWidget(main)

    def _build_pose_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))

        modelo_row = widgets.QHBoxLayout()
        modelo_row.addWidget(ui.rotulo(i18n.t("Modelo:")))
        self.cmb_corpo = widgets.QComboBox()
        for chave, rotulo, _ in VIEWER3D_MODELOS:
            self.cmb_corpo.addItem(i18n.t(rotulo), chave)
        self.cmb_corpo.currentIndexChanged.connect(self._mudar_corpo)
        modelo_row.addWidget(self.cmb_corpo, 1)
        layout.addLayout(modelo_row)

        corpo_row = widgets.QHBoxLayout()
        corpo_row.addWidget(ui.rotulo(i18n.t("Corpo:")))
        self.cmb_pose_corpo = widgets.QComboBox()
        self.cmb_pose_corpo.currentIndexChanged.connect(self._mudar_pose_corpo)
        corpo_row.addWidget(self.cmb_pose_corpo, 1)
        corpo_row.addWidget(
            ui.botao(
                i18n.t("Salvar pose..."),
                i18n.t(
                    "Salva a pose do corpo atual na sua biblioteca. As mãos não entram."
                ),
                self._salvar_pose_corpo,
                icone_chave="salvar",
            )
        )
        layout.addLayout(corpo_row)

        mao_direita_row = widgets.QHBoxLayout()
        mao_direita_row.addWidget(ui.rotulo(i18n.t("Mão direita:")))
        self.cmb_mao_direita = widgets.QComboBox()
        self.cmb_mao_direita.currentIndexChanged.connect(self._mudar_mao_direita)
        mao_direita_row.addWidget(self.cmb_mao_direita, 1)
        layout.addLayout(mao_direita_row)

        mao_esquerda_row = widgets.QHBoxLayout()
        mao_esquerda_row.addWidget(ui.rotulo(i18n.t("Mão esquerda:")))
        self.cmb_mao_esquerda = widgets.QComboBox()
        self.cmb_mao_esquerda.currentIndexChanged.connect(self._mudar_mao_esquerda)
        mao_esquerda_row.addWidget(self.cmb_mao_esquerda, 1)
        layout.addLayout(mao_esquerda_row)

        self.grupo_juntas = widgets.QGroupBox(i18n.t("Juntas"))
        self.juntas_layout = ui.espacamento(
            widgets.QVBoxLayout(self.grupo_juntas), margem=0, espaco=ui.GAP
        )
        layout.addWidget(self.grupo_juntas)

        posse = widgets.QHBoxLayout()
        button_reset = ui.botao(i18n.t("Limpar pose"), i18n.t("Zera todas as juntas."))
        button_reset.clicked.connect(self.limpar_pose)
        posse.addWidget(button_reset)
        layout.addLayout(posse)
        layout.addStretch(1)
        return tab

    def _build_maos_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))
        layout.addWidget(
            ui.rotulo(
                i18n.t(
                    "Escolha a mão, ajuste os dedos (0° = mão aberta, 90° = punho) e salve na sua biblioteca: a esquerda é espelhada ao salvar, como as poses do kit."
                )
            )
        )
        lado_row = widgets.QHBoxLayout()
        lado_row.addWidget(ui.rotulo(i18n.t("Mão:")))
        self.cmb_mao_ajuste = widgets.QComboBox()
        self.cmb_mao_ajuste.addItem(i18n.t("Direita"), modelo3d.LADO_DIREITA)
        self.cmb_mao_ajuste.addItem(i18n.t("Esquerda"), modelo3d.LADO_ESQUERDA)
        self.cmb_mao_ajuste.currentIndexChanged.connect(self._mudar_mao_ajuste)
        lado_row.addWidget(self.cmb_mao_ajuste, 1)
        layout.addLayout(lado_row)

        self.grupo_dedos = widgets.QGroupBox(i18n.t("Dedos"))
        self.dedos_layout = ui.espacamento(
            widgets.QVBoxLayout(self.grupo_dedos), margem=0, espaco=ui.GAP
        )
        layout.addWidget(self.grupo_dedos)

        self.button_salvar_mao = ui.botao(
            i18n.t("Salvar pose da mão direita..."),
            i18n.t("Salva a pose atual da mão direita na sua biblioteca."),
            self._salvar_pose_de_mao,
            icone_chave="salvar",
        )
        layout.addWidget(self.button_salvar_mao)
        layout.addStretch(1)
        return tab

    def _build_camera_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))

        camera_row = widgets.QHBoxLayout()
        camera_row.addWidget(ui.rotulo(i18n.t("Câmera:")))
        self.cmb_camera = widgets.QComboBox()
        self.cmb_camera.addItem(i18n.t("Ortográfica"), "ortografica")
        self.cmb_camera.addItem(i18n.t("Perspectiva"), "perspectiva")
        self.cmb_camera.currentIndexChanged.connect(self._mudar_camera)
        camera_row.addWidget(self.cmb_camera, 1)
        layout.addLayout(camera_row)

        lente_row = widgets.QHBoxLayout()
        lente_row.addWidget(ui.rotulo(i18n.t("Lente:")))
        self.cmb_lente = widgets.QComboBox()
        for lente in modelo3d.LENTES:
            self.cmb_lente.addItem(i18n.t("{0:.0f} mm").format(lente), lente)
        self.cmb_lente.currentIndexChanged.connect(self._mudar_lente)
        lente_row.addWidget(self.cmb_lente, 1)
        layout.addLayout(lente_row)
        self._atualizar_lente()

        estilo_row = widgets.QHBoxLayout()
        estilo_row.addWidget(ui.rotulo(i18n.t("Estilo:")))
        self.cmb_estilo = widgets.QComboBox()
        self.cmb_estilo.addItem(i18n.t("Sombreado"), "sombreado")
        self.cmb_estilo.addItem(i18n.t("Silhueta"), "silhueta")
        self.cmb_estilo.addItem(i18n.t("Toon"), "toon")
        self.cmb_estilo.currentIndexChanged.connect(self.agendar_render)
        estilo_row.addWidget(self.cmb_estilo, 1)
        layout.addLayout(estilo_row)

        cor_row = widgets.QHBoxLayout()
        cor_row.addWidget(ui.rotulo(i18n.t("Cor:")))
        self.cmb_cor = widgets.QComboBox()
        self.cmb_cor.addItem(i18n.t("Bege"), None)
        self.cmb_cor.addItem(i18n.t("Azul"), "#7da7d9")
        self.cmb_cor.addItem(i18n.t("Gelo"), "#eef4fb")
        self.cmb_cor.addItem(i18n.t("Grafite"), "#5c5c5c")
        self.cmb_cor.currentIndexChanged.connect(self._mudar_cor)
        cor_row.addWidget(self.cmb_cor, 1)
        layout.addLayout(cor_row)

        luz_azimute_row = widgets.QHBoxLayout()
        luz_azimute_row.addWidget(ui.rotulo(i18n.t("Luz · Azimute")))
        self.sld_luz_azimute = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        self.sld_luz_azimute.setRange(-180, 180)
        self.sld_luz_azimute.setValue(int(self.luz_azimute))
        etiqueta_azimute = ui.rotulo_info(i18n.t("{0}°").format(int(self.luz_azimute)))
        self.sld_luz_azimute.valueChanged.connect(
            lambda novo, etiqueta=etiqueta_azimute: self._mudar_luz(
                "azimute", novo, etiqueta
            )
        )
        luz_azimute_row.addWidget(self.sld_luz_azimute, 1)
        luz_azimute_row.addWidget(etiqueta_azimute)
        layout.addLayout(luz_azimute_row)

        luz_altura_row = widgets.QHBoxLayout()
        luz_altura_row.addWidget(ui.rotulo(i18n.t("Luz · Altura")))
        self.sld_luz_altura = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        self.sld_luz_altura.setRange(-80, 80)
        self.sld_luz_altura.setValue(int(self.luz_altura))
        etiqueta_altura = ui.rotulo_info(i18n.t("{0}°").format(int(self.luz_altura)))
        self.sld_luz_altura.valueChanged.connect(
            lambda novo, etiqueta=etiqueta_altura: self._mudar_luz(
                "altura", novo, etiqueta
            )
        )
        luz_altura_row.addWidget(self.sld_luz_altura, 1)
        luz_altura_row.addWidget(etiqueta_altura)
        layout.addLayout(luz_altura_row)

        cameras = widgets.QHBoxLayout()
        button_front = ui.botao(
            i18n.t("Frente"),
            i18n.t("Volta à vista frontal (ângulo, zoom e enquadramento)."),
        )
        button_front.clicked.connect(self.reset_camera)
        cameras.addWidget(button_front)
        button_fit = ui.botao(
            i18n.t("Enquadrar"),
            i18n.t("Centraliza o modelo e volta ao zoom 1, sem mudar o ângulo."),
        )
        button_fit.clicked.connect(self.enquadrar)
        cameras.addWidget(button_fit)
        button_zoom_out = ui.botao(i18n.t("−"), i18n.t("Diminui o zoom."))
        button_zoom_out.clicked.connect(lambda: self.aplicar_zoom(0.8))
        cameras.addWidget(button_zoom_out)
        button_zoom_in = ui.botao(i18n.t("+"), i18n.t("Aumenta o zoom."))
        button_zoom_in.clicked.connect(lambda: self.aplicar_zoom(1.25))
        cameras.addWidget(button_zoom_in)
        layout.addLayout(cameras)

        self.button_move = ui.botao(
            i18n.t("Mover"),
            i18n.t(
                "Ligado, arrastar desloca o enquadramento em vez de girar (ou use Shift/botão do meio)."
            ),
        )
        self.button_move.setCheckable(True)
        self.button_move.toggled.connect(self._alternar_mover)
        layout.addWidget(self.button_move)

        layout.addWidget(
            ui.rotulo(
                i18n.t(
                    "Arraste no preview para orbitar; Shift+arraste desloca; roda ou +/− dão zoom."
                )
            )
        )
        layout.addStretch(1)
        return tab

    def _build_insert_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))

        flutuante = widgets.QHBoxLayout()
        self.button_flutuar = ui.botao(
            i18n.t("Flutuar na página"),
            i18n.t(
                "Mostra o preview sobre a seleção (desenhe uma seleção retangular sobre o painel primeiro); arraste e redimensione à vontade."
            ),
            icone_chave="novo",
        )
        self.button_flutuar.setCheckable(True)
        self.button_flutuar.toggled.connect(self._alternar_flutuar)
        flutuante.addWidget(self.button_flutuar)
        self.button_fixar = ui.botao(
            i18n.t("Fixar"),
            i18n.t(
                "Com o flutuante fixado, o mouse atravessa e você desenha por baixo."
            ),
        )
        self.button_fixar.setCheckable(True)
        self.button_fixar.setEnabled(False)
        self.button_fixar.toggled.connect(self._alternar_fixar)
        flutuante.addWidget(self.button_fixar)
        layout.addLayout(flutuante)

        opacidade = widgets.QHBoxLayout()
        opacidade.addWidget(ui.rotulo(i18n.t("Opacidade:")))
        self.sld_opacidade = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        self.sld_opacidade.setRange(20, 100)
        self.sld_opacidade.setValue(80)
        self.lbl_opacidade = ui.rotulo_info(i18n.t("80%"))
        self.sld_opacidade.valueChanged.connect(self._mudar_opacidade)
        opacidade.addWidget(self.sld_opacidade, 1)
        opacidade.addWidget(self.lbl_opacidade)
        layout.addLayout(opacidade)

        acoes = widgets.QHBoxLayout()
        button_layer = ui.botao(
            i18n.t("Inserir como camada"),
            i18n.t(
                "Insere na seleção ativa (desenhe uma seleção retangular sobre o painel); a camada entra abaixo da camada ativa, para o esboço ficar por cima, e a seleção é desfeita."
            ),
            icone_chave="aplicar",
        )
        button_layer.clicked.connect(lambda: self.inserir(referencia=False))
        acoes.addWidget(button_layer)
        button_ref = ui.botao(
            i18n.t("Inserir como referência"),
            i18n.t(
                "Insere na seleção ativa, travado, com rótulo de cor e opacidade reduzida, abaixo da camada ativa; a seleção é desfeita."
            ),
        )
        button_ref.clicked.connect(lambda: self.inserir(referencia=True))
        acoes.addWidget(button_ref)
        layout.addLayout(acoes)

        layout.addWidget(
            ui.rotulo(
                i18n.t(
                    "1) Desenhe uma seleção retangular sobre o painel. 2) Ajuste a pose e o zoom (o preview mostra exatamente o recorte). 3) 'Inserir' coloca a camada abaixo da ativa e desfaz a seleção."
                )
            )
        )
        layout.addStretch(1)
        return tab

    def _caminho_do_corpo(self, chave):
        for chave_modelo, _, caminho in VIEWER3D_MODELOS:
            if chave_modelo == chave:
                return caminho
        return None

    def _carregar_modelo(self, aplicar_padrao=False):
        try:
            self.modelo = modelo3d.Modelo.carregar(self._caminho_do_corpo(self.corpo))
        except (OSError, ValueError) as error:
            self.lbl_regiao.setText(i18n.t("Modelo 3D indisponível: {0}").format(error))
            return
        self._posados_cache = None
        self._popular_poses()
        if aplicar_padrao:
            self._aplicar_poses()
        if self.regiao is None:
            self._selecionar_regiao("tronco")
        else:
            self._montar_sliders()
        self.atualizar_preview()

    def _popular_poses(self):
        self.pose_corpo = self._popular_combo(
            self.cmb_pose_corpo,
            (VIEWER3D_POSES_CORPO_DIR, VIEWER3D_POSES_USUARIO_CORPO_DIR),
            "corpo",
            self.pose_corpo,
        )
        self.pose_mao_direita = self._popular_combo(
            self.cmb_mao_direita,
            (VIEWER3D_POSES_MAOS_DIR, VIEWER3D_POSES_USUARIO_MAOS_DIR),
            "maos",
            self.pose_mao_direita,
        )
        self.pose_mao_esquerda = self._popular_combo(
            self.cmb_mao_esquerda,
            (VIEWER3D_POSES_MAOS_DIR, VIEWER3D_POSES_USUARIO_MAOS_DIR),
            "maos",
            self.pose_mao_esquerda,
        )

    def _popular_combo(self, combo, pastas, parte, atual):
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(i18n.t("—"), None)
        combo.setIconSize(QtCore.QSize(34, 46))
        for pasta in pastas:
            try:
                arquivos = sorted(os.listdir(pasta))
            except OSError:
                continue
            for arquivo in arquivos:
                if not arquivo.endswith(".json"):
                    continue
                caminho = os.path.join(pasta, arquivo)
                try:
                    dados = modelo3d.carregar_pose(caminho)
                    rotulo = i18n.t(dados.get("nome") or arquivo[:-5])
                except (OSError, ValueError):
                    rotulo = arquivo[:-5]
                combo.addItem(rotulo, caminho)
                # Miniatura: a do lado do arquivo (pose do usuário gera a sua)
                # ou a galeria do repositório, por nome de arquivo.
                previa = os.path.splitext(caminho)[0] + ".png"
                if not os.path.isfile(previa):
                    previa = os.path.join(
                        RESOURCES_DIR, "poses-preview", parte, arquivo[:-5] + ".png"
                    )
                if os.path.isfile(previa):
                    combo.setItemIcon(combo.count() - 1, QtGui.QIcon(previa))
        indice = self._indice_da_pose(combo, atual)
        combo.setCurrentIndex(indice if indice >= 0 else 0)
        combo.blockSignals(False)
        return combo.itemData(combo.currentIndex())

    @staticmethod
    def _indice_da_pose(combo, atual):
        """Índice do item para ``atual`` (caminho completo ou nome de arquivo).

        O nome puro cobre o valor inicial e o do "limpar pose" em versões
        anteriores, quando os itens guardavam só o nome do arquivo.
        """
        indice = combo.findData(atual)
        if indice >= 0 or not atual:
            return indice
        alvo = os.path.basename(atual)
        for indice in range(combo.count()):
            dado = combo.itemData(indice)
            if dado and os.path.basename(dado) == alvo:
                return indice
        return -1

    def _sincronizar_combos(self):
        for combo, atual in (
            (self.cmb_pose_corpo, self.pose_corpo),
            (self.cmb_mao_direita, self.pose_mao_direita),
            (self.cmb_mao_esquerda, self.pose_mao_esquerda),
        ):
            indice = self._indice_da_pose(combo, atual)
            combo.blockSignals(True)
            combo.setCurrentIndex(indice if indice >= 0 else 0)
            combo.blockSignals(False)

    def _ler_pose(self, caminho):
        if not caminho:
            return {}
        try:
            dados = modelo3d.carregar_pose(caminho)
        except (OSError, ValueError) as error:
            helpers.show_info(
                i18n.t("3D"), i18n.t("Não foi possível ler a pose: {0}").format(error)
            )
            return {}
        return dados.get("ossos", {})

    def _mudar_corpo(self, indice):
        chave = self.cmb_corpo.itemData(indice)
        if chave:
            self.corpo = chave
            self._carregar_modelo()
            self._agendar_salvar_estado()

    def _mudar_pose_corpo(self, indice):
        self.pose_corpo = self.cmb_pose_corpo.itemData(indice)
        self._aplicar_corpo()

    def _mudar_mao_direita(self, indice):
        self.pose_mao_direita = self.cmb_mao_direita.itemData(indice)
        self._aplicar_mao(modelo3d.LADO_DIREITA)

    def _mudar_mao_esquerda(self, indice):
        self.pose_mao_esquerda = self.cmb_mao_esquerda.itemData(indice)
        self._aplicar_mao(modelo3d.LADO_ESQUERDA)

    def _mudar_camera(self, indice):
        self.perspectiva = self.cmb_camera.itemData(indice) == "perspectiva"
        self._atualizar_lente()
        self.agendar_render()

    def _mudar_lente(self, indice):
        lente = self.cmb_lente.itemData(indice)
        if lente:
            self.lente = float(lente)
        self.agendar_render()

    def _mudar_cor(self, indice):
        self.cor = self.cmb_cor.itemData(indice)
        self.agendar_render()

    def _mudar_luz(self, eixo, valor, etiqueta):
        if eixo == "azimute":
            self.luz_azimute = float(valor)
        else:
            self.luz_altura = float(valor)
        etiqueta.setText(i18n.t("{0}°").format(valor))
        self.agendar_render()

    def _atualizar_lente(self):
        self.cmb_lente.setEnabled(self.perspectiva)

    def _aplicar_poses(self):
        """Combina corpo e mãos (cada mão por cima) e redesenha.

        Reconstrução completa: usada na carga do modelo e no "limpar pose".
        As trocas de seletor usam :meth:`_aplicar_corpo` e :meth:`_aplicar_mao`
        para não descartar os ajustes feitos nos sliders.
        """
        corpo = self._ler_pose(self.pose_corpo)
        direita = self._ler_pose(self.pose_mao_direita)
        esquerda = self._ler_pose(self.pose_mao_esquerda)
        self.semantica = modelo3d.combinar_poses(corpo, direita, esquerda)
        self._pose_mudou()
        self._montar_sliders()
        self.agendar_render()

    def _aplicar_corpo(self):
        """Troca só a pose do corpo, preservando as mãos (e seus ajustes)."""
        corpo = self._ler_pose(self.pose_corpo)
        self.semantica = modelo3d.substituir_corpo(self.semantica, corpo)
        self._pose_mudou()
        self._montar_sliders()
        self.agendar_render()

    def _aplicar_mao(self, lado):
        """Troca só a mão pedida, preservando corpo e a outra mão."""
        if lado == modelo3d.LADO_DIREITA:
            arquivo = self.pose_mao_direita
        else:
            arquivo = self.pose_mao_esquerda
        valores = self._ler_pose(arquivo)
        self.semantica = modelo3d.substituir_mao(self.semantica, valores, lado)
        self._pose_mudou()
        self._montar_sliders()
        self.agendar_render()

    def _pose_mudou(self):
        """Invalida o cache dos vértices posados (a pose mudou)."""
        self._pose_revisao += 1

    def _posados(self):
        """Vértices na pose atual, recalculados só quando a pose muda."""
        if self._posados_cache is None or self._posados_cache[0] != self._pose_revisao:
            self._posados_cache = (
                self._pose_revisao,
                self.modelo.vertices_em_pose(self._rotacoes()),
            )
        return self._posados_cache[1]

    def _rotacoes(self):
        if self.modelo is None:
            return {}
        return self.modelo.aplicar_semantica(self.semantica)

    def agendar_render(self):
        self._timer.start()
        self._salvar_timer.start()

    def _restaurar_estado(self):
        """Lê o estado da sessão anterior do config.json (tolerante a lixo)."""

        def ler(chave, padrao, tipos):
            valor = self.config.get(chave)
            if valor is None or not isinstance(valor, tipos):
                return padrao
            return valor

        self.corpo = ler("viewer3d.modelo", self.corpo, str) or self.corpo
        self.pose_corpo = ler("viewer3d.pose_corpo", self.pose_corpo, str)
        self.pose_mao_direita = ler(
            "viewer3d.pose_mao_direita", self.pose_mao_direita, str
        )
        self.pose_mao_esquerda = ler(
            "viewer3d.pose_mao_esquerda", self.pose_mao_esquerda, str
        )
        camera = ler("viewer3d.camera", {}, dict)
        for chave in ("yaw", "pitch", "zoom", "pan_x", "pan_y"):
            valor = camera.get(chave)
            if isinstance(valor, (int, float)):
                self.camera[chave] = float(valor)
        self.cor = ler("viewer3d.cor", self.cor, str)
        self.luz_azimute = float(
            ler("viewer3d.luz_azimute", self.luz_azimute, (int, float))
        )
        self.luz_altura = float(
            ler("viewer3d.luz_altura", self.luz_altura, (int, float))
        )
        self.perspectiva = bool(ler("viewer3d.perspectiva", self.perspectiva, bool))
        self.lente = float(ler("viewer3d.lente", self.lente, (int, float)))
        self._estilo_salvo = ler("viewer3d.estilo", None, str)

    @staticmethod
    def _indice_por_dado(combo, dado):
        """Índice do item com este dado (o ``findData`` não lida bem com None)."""
        for indice in range(combo.count()):
            if combo.itemData(indice) == dado:
                return indice
        return -1

    def _aplicar_estado_nos_combos(self):
        """Mostra nos combos o estado restaurado, sem disparar os handlers.

        O estado já está nos atributos; os sinais ficam bloqueados para o
        modelo não carregar duas vezes (a carga acontece uma vez no __init__).
        """
        alvos = []
        if self._estilo_salvo:
            indice = self._indice_por_dado(self.cmb_estilo, self._estilo_salvo)
            if indice >= 0:
                alvos.append((self.cmb_estilo, indice))
        for combo, dado in (
            (self.cmb_cor, self.cor),
            (
                self.cmb_camera,
                "perspectiva" if self.perspectiva else "ortografica",
            ),
            (self.cmb_lente, self.lente),
            (self.cmb_corpo, self.corpo),
        ):
            indice = self._indice_por_dado(combo, dado)
            if indice >= 0:
                alvos.append((combo, indice))
        for combo, indice in alvos:
            combo.blockSignals(True)
            combo.setCurrentIndex(indice)
            combo.blockSignals(False)

    def _agendar_salvar_estado(self):
        self._salvar_timer.start()

    def _salvar_estado(self):
        """Grava o estado da sessão no config.json (agendado com respiro)."""
        try:
            self.config.set("viewer3d.modelo", self.corpo)
            self.config.set("viewer3d.pose_corpo", self.pose_corpo)
            self.config.set("viewer3d.pose_mao_direita", self.pose_mao_direita)
            self.config.set("viewer3d.pose_mao_esquerda", self.pose_mao_esquerda)
            self.config.set("viewer3d.estilo", self.cmb_estilo.currentData())
            self.config.set("viewer3d.cor", self.cor)
            self.config.set("viewer3d.luz_azimute", self.luz_azimute)
            self.config.set("viewer3d.luz_altura", self.luz_altura)
            self.config.set("viewer3d.perspectiva", self.perspectiva)
            self.config.set("viewer3d.lente", self.lente)
            self.config.set("viewer3d.camera", dict(self.camera))
        except OSError as erro:
            helpers.log("estado do 3D não salvo: {0}".format(erro))

    def _estilo(self):
        dados = self.cmb_estilo.currentData()
        cor = self.cor
        if dados == "silhueta":
            return "chapado", cor or "#141414", "#ffffff"
        if dados == "toon":
            return "toon", cor, None
        return "sombreado", cor, None

    def _pan_em_pixels(self, largura, altura):
        """Converte o pan relativo (fração da menor dimensão) em pixels."""
        minimo = max(1.0, float(min(largura, altura)))
        return self.camera["pan_x"] * minimo, self.camera["pan_y"] * minimo

    def _render_svg(self, largura, altura, com_fundo=True, posados=None):
        estilo, cor, fundo = self._estilo()
        if not com_fundo:
            fundo = None
        if posados is None:
            posados = self._posados()
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
            luz=modelo3d.luz_de_angulos(self.luz_azimute, self.luz_altura),
            lente=self.lente if self.perspectiva else None,
            cull=True,
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
        posados = self._posados()
        self._tela = self.modelo.vertices_em_tela(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            pan_x=pan_x,
            pan_y=pan_y,
            largura=largura,
            altura=altura,
            posados=posados,
            lente=self.lente if self.perspectiva else None,
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
            helpers.show_info(
                i18n.t("3D"), i18n.t("Abra um documento para usar o flutuante.")
            )
            self.button_flutuar.setChecked(False)
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t(
                    "Desenhe uma seleção retangular sobre o painel para usar o flutuante."
                ),
            )
            self.button_flutuar.setChecked(False)
            return
        viewport = _viewport_da_view(view)
        if viewport is None:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Não foi possível ancorar o flutuante nesta janela."),
            )
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
        self.lbl_opacidade.setText(i18n.t("{0}%").format(valor))
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
        """Volta ao padrão: Idle + Fechadas, nas duas mãos."""
        self.pose_corpo = os.path.join(
            VIEWER3D_POSES_CORPO_DIR, VIEWER3D_POSE_CORPO_PADRAO
        )
        self.pose_mao_direita = os.path.join(
            VIEWER3D_POSES_MAOS_DIR, VIEWER3D_POSE_MAOS_PADRAO
        )
        self.pose_mao_esquerda = os.path.join(
            VIEWER3D_POSES_MAOS_DIR, VIEWER3D_POSE_MAOS_PADRAO
        )
        self._sincronizar_combos()
        self._aplicar_poses()

    def _salvar_pose_corpo(self):
        """Salva a pose atual do corpo na biblioteca do usuário (só o corpo)."""
        if self.modelo is None:
            helpers.show_info(i18n.t("3D"), i18n.t("O modelo não está disponível."))
            return
        nome, ok = QtWidgets.QInputDialog.getText(
            self.widget(),
            i18n.t("Salvar pose do corpo"),
            i18n.t("Nome da pose do corpo (somente o corpo será salvo):"),
        )
        if not ok or not nome.strip():
            return
        nome = nome.strip()
        destino = os.path.join(
            VIEWER3D_POSES_USUARIO_CORPO_DIR, modelo3d.slug_de_pose(nome) + ".json"
        )
        if os.path.exists(destino):
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Já existe uma pose com esse nome na sua biblioteca."),
            )
            return
        try:
            os.makedirs(VIEWER3D_POSES_USUARIO_CORPO_DIR, exist_ok=True)
            valores = modelo3d.semantica_do_corpo(self.semantica)
            modelo3d.salvar_pose(destino, nome, valores)
            self._salvar_previa_da_pose(destino, valores)
        except OSError as error:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Não foi possível salvar a pose: {0}").format(error),
            )
            return
        self.pose_corpo = destino
        self._popular_poses()
        self._agendar_salvar_estado()
        helpers.show_info(
            i18n.t("3D"), i18n.t("Pose do corpo salva na sua biblioteca.")
        )

    def _salvar_previa_da_pose(self, caminho_json, valores, parte="corpo"):
        """Miniatura ao lado da pose do usuário, na câmera da galeria.

        Corpo: a pose com as mãos fechadas padrão. Mãos: o corpo em Idle com a
        mão salva (que sai na convenção da direita). Falha de miniatura não
        derruba o salvamento: a pose já está gravada e a lista mostra o item
        sem ícone.
        """
        if QSvgRenderer is None:
            return
        try:
            if parte == "maos":
                corpo = self._ler_pose(
                    os.path.join(VIEWER3D_POSES_CORPO_DIR, VIEWER3D_POSE_CORPO_PADRAO)
                )
                semantica = modelo3d.combinar_poses(corpo, valores, {})
            else:
                fechada = self._ler_pose(
                    os.path.join(VIEWER3D_POSES_MAOS_DIR, VIEWER3D_POSE_MAOS_PADRAO)
                )
                semantica = modelo3d.combinar_poses(valores, fechada, fechada)
            svg = modelo3d.render_previa(self.modelo, semantica, parte)
            imagem = self._rasterizar(
                svg, modelo3d.PREVIA_LARGURA, modelo3d.PREVIA_ALTURA
            )
            imagem.save(os.path.splitext(caminho_json)[0] + ".png", "PNG")
        except (OSError, ValueError) as erro:
            helpers.log("prévia da pose não gerada: {0}".format(erro))

    def _salvar_pose_de_mao(self):
        """Salva a mão em ajuste na biblioteca do usuário (direita por padrão).

        A pose sai sempre na convenção autoral (mão direita): a esquerda é
        espelhada ao gravar, como as poses do kit.
        """
        if self.modelo is None:
            helpers.show_info(i18n.t("3D"), i18n.t("O modelo não está disponível."))
            return
        lado = self.mao_ajuste
        nome, ok = QtWidgets.QInputDialog.getText(
            self.widget(),
            i18n.t("Salvar pose de mão"),
            i18n.t("Nome da pose de mão:"),
        )
        if not ok or not nome.strip():
            return
        nome = nome.strip()
        valores = modelo3d.semantica_da_mao(self.semantica, lado)
        if not valores:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Ajuste os dedos antes de salvar a pose da mão."),
            )
            return
        if lado == modelo3d.LADO_ESQUERDA:
            valores = modelo3d.espelhar(valores)
        destino = os.path.join(
            VIEWER3D_POSES_USUARIO_MAOS_DIR, modelo3d.slug_de_pose(nome) + ".json"
        )
        if os.path.exists(destino):
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Já existe uma pose com esse nome na sua biblioteca."),
            )
            return
        try:
            os.makedirs(VIEWER3D_POSES_USUARIO_MAOS_DIR, exist_ok=True)
            modelo3d.salvar_pose(destino, nome, valores)
            self._salvar_previa_da_pose(destino, valores, parte="maos")
        except OSError as error:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t("Não foi possível salvar a pose: {0}").format(error),
            )
            return
        if lado == modelo3d.LADO_DIREITA:
            self.pose_mao_direita = destino
        else:
            self.pose_mao_esquerda = destino
        self._popular_poses()
        self._agendar_salvar_estado()
        helpers.show_info(i18n.t("3D"), i18n.t("Pose de mão salva na sua biblioteca."))

    def selecionar_em(self, x, y):
        if self.modelo is None or not self._tela:
            return
        x -= self._offset_preview[0]
        y -= self._offset_preview[1]
        if x < 0 or y < 0 or x > self._tamanho_render[0] or y > self._tamanho_render[1]:
            return
        melhor = None
        for indice, (tela_x, tela_y, _) in enumerate(self._tela):
            distancia = (tela_x - x) ** 2 + (tela_y - y) ** 2
            if melhor is None or distancia < melhor[0]:
                melhor = (distancia, indice)
        if melhor is None or melhor[0] > 48**2:
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
        slider.setToolTip(
            i18n.t(
                "Ajusta a junta em graus; Dobrar/Abrir/Girar seguem os eixos do rig."
            )
        )
        slider.setValue(int(self.semantica.get(osso, {}).get(chave, 0)))
        valor = ui.rotulo_info(i18n.t("0°"))
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
        self._pose_mudou()
        etiqueta.setText(i18n.t("{0}°").format(valor))
        self.agendar_render()

    def _referencia_fechada(self):
        """Valores de referência da pose "fechada" (só os dedos, sem o pulso).

        O fechar do dedo neste rig mora no eixo "abrir" negativo (medido em
        QA contra as poses abertas/fechada); "dobrar" e "girar" deformam.
        """
        if self._ref_fechada is None:
            caminho = os.path.join(VIEWER3D_POSES_MAOS_DIR, "fechada.json")
            try:
                with open(caminho, encoding="utf-8") as arquivo:
                    dados = json.load(arquivo)
                self._ref_fechada = {
                    osso: valores
                    for osso, valores in dados.get("ossos", {}).items()
                    if osso.startswith(FAMILIAS_DEDO)
                }
            except (OSError, ValueError):
                self._ref_fechada = {}
        return self._ref_fechada

    def _valor_do_dedo(self, ossos):
        """Valor do slider (0 = aberta, 90 = fechada) a partir da semântica."""
        return max(
            0,
            min(
                LIMITE_FECHAR_DEDO,
                modelo3d.graus_dos_dedos(
                    self._referencia_fechada(), ossos, self.semantica
                ),
            ),
        )

    def _mudar_dedos(self, ossos, valor, etiqueta):
        """Interpola os valores da pose "fechada" na proporção do slider."""
        lado = (
            modelo3d.LADO_ESQUERDA
            if ossos and ossos[0].endswith(".l")
            else modelo3d.LADO_DIREITA
        )
        valores = modelo3d.dedos_por_graus(self._referencia_fechada(), lado, valor)
        for osso in ossos:
            if osso in valores:
                self.semantica[osso] = valores[osso]
        self._pose_mudou()
        etiqueta.setText(i18n.t("{0}°").format(valor))
        self.agendar_render()

    def _linha_dedo(self, rotulo, ossos):
        """Linha de slider "Dobrar" (0 = aberta, 90 = fechada) para um grupo."""
        if not ossos:
            return None
        widgets = QtWidgets
        linha = widgets.QHBoxLayout()
        linha.addWidget(ui.rotulo(rotulo))
        slider = widgets.QSlider(ORIENTACAO_HORIZONTAL)
        slider.setRange(0, LIMITE_FECHAR_DEDO)
        slider.setToolTip(i18n.t("0° = mão aberta; 90° = punho."))
        slider.setValue(self._valor_do_dedo(ossos))
        valor = ui.rotulo_info(i18n.t("{0}°").format(slider.value()))
        slider.valueChanged.connect(
            lambda novo, alvos=tuple(ossos), etiqueta=valor: self._mudar_dedos(
                alvos, novo, etiqueta
            )
        )
        linha.addWidget(slider, 1)
        linha.addWidget(valor)
        return linha

    def _linha_dedos(self, lado):
        """Slider de todos os dedos de um lado (usado na região do braço)."""
        ossos = [
            osso["nome"]
            for osso in self.modelo.ossos
            if osso["nome"].startswith(FAMILIAS_DEDO)
            and osso["nome"].endswith("." + lado)
        ]
        return self._linha_dedo(i18n.t("Dedos · Dobrar"), ossos)

    def _montar_dedos(self):
        """Rebuild dos sliders da aba "Mãos" para o lado em ajuste."""
        self._limpar_layout(self.dedos_layout)
        if self.modelo is None:
            return
        lado = "l" if self.mao_ajuste == modelo3d.LADO_ESQUERDA else "r"
        self.grupo_dedos.setTitle(
            i18n.t("Dedos · {0}").format(
                i18n.t("Esquerda" if lado == "l" else "Direita")
            )
        )
        for familia, rotulo in (
            ("thumb", i18n.t("Polegar")),
            ("index", i18n.t("Indicador")),
            ("middle", i18n.t("Médio")),
            ("ring", i18n.t("Anelar")),
            ("pinky", i18n.t("Mindinho")),
        ):
            ossos = [
                osso["nome"]
                for osso in self.modelo.ossos
                if osso["nome"].startswith(familia)
                and osso["nome"].endswith("." + lado)
            ]
            linha = self._linha_dedo(
                "{0} · {1}".format(rotulo, i18n.t("Dobrar")), ossos
            )
            if linha is not None:
                self.dedos_layout.addLayout(linha)
        linha = self._linha_dedos(lado)
        if linha is not None:
            self.dedos_layout.addLayout(linha)

    def _mudar_mao_ajuste(self, indice):
        self.mao_ajuste = self.cmb_mao_ajuste.itemData(indice) or modelo3d.LADO_DIREITA
        if self.mao_ajuste == modelo3d.LADO_ESQUERDA:
            self.button_salvar_mao.setText(i18n.t("Salvar pose da mão esquerda..."))
            self.button_salvar_mao.setToolTip(
                i18n.t(
                    "Salva a pose atual da mão esquerda na sua biblioteca (espelhada para a convenção da direita, como as poses do kit)."
                )
            )
        else:
            self.button_salvar_mao.setText(i18n.t("Salvar pose da mão direita..."))
            self.button_salvar_mao.setToolTip(
                i18n.t("Salva a pose atual da mão direita na sua biblioteca.")
            )
        self._montar_dedos()

    def _montar_sliders(self):
        self._limpar_layout(self.juntas_layout)
        self._montar_dedos()
        if self.modelo is None or self.regiao is None:
            self.grupo_juntas.setTitle(i18n.t("Juntas"))
            return
        for chave, nome, ossos in REGIOES:
            if chave == self.regiao:
                break
        else:
            return
        self.grupo_juntas.setTitle(i18n.t("Juntas: {0}").format(i18n.t(nome)))
        self.lbl_regiao.setText(i18n.t("Região: {0}").format(i18n.t(nome)))
        for osso in ossos:
            for eixo in EIXOS_POR_BASE.get(_base(osso), ("dobrar",)):
                self.juntas_layout.addLayout(
                    self._linha_slider(
                        osso,
                        eixo,
                        "{0} · {1}".format(
                            i18n.t(nome_amigavel(osso)), i18n.t(ROTULOS[eixo])
                        ),
                    )
                )
        # As regiões do braço mostram também o slider de todos os dedos
        # (as chaves são "braco_esq"/"braco_dir", daí o sufixo do osso).
        lado = ""
        if self.regiao.endswith("_esq"):
            lado = "l"
        elif self.regiao.endswith("_dir"):
            lado = "r"
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
            helpers.show_info(i18n.t("3D"), i18n.t("O modelo não está disponível."))
            return
        documento = helpers.active_document()
        if documento is None:
            helpers.show_info(
                i18n.t("3D"), i18n.t("Abra um documento para inserir o desenho.")
            )
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_info(
                i18n.t("3D"),
                i18n.t(
                    "Desenhe uma seleção retangular sobre o painel de destino para inserir."
                ),
            )
            return
        x, y, largura, altura = selecao
        ativo = documento.activeNode()
        nome_ativo = ativo.name() if ativo is not None else None

        def _inserir_agora():
            svg = self._render_svg(largura, altura, com_fundo=False)
            imagem = self._rasterizar(svg, largura, altura)
            # O device RGBA 8 bits do Krita guarda os canais em BGRA (documentação
            # do libkis: "Integer RGBA: Blue, Green, Red, Alpha"); o Format_ARGB32
            # do Qt é BGRA em memória, então os bytes batem com o setPixelData.
            # Com RGBA8888 o vermelho e o azul saíam trocados (azul virava bege).
            rgba = imagem.convertToFormat(IMAGE_FORMAT_ARGB32)
            dados = bytes(rgba.constBits().asstring(rgba.sizeInBytes()))
            nome = helpers.unique_layer_name(documento, "3D")
            camada = documento.createNode(nome, "paintlayer")
            if camada is None or not camada.setPixelData(dados, x, y, largura, altura):
                helpers.show_info(
                    i18n.t("3D"), i18n.t("Não foi possível criar a camada.")
                )
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
                i18n.t(
                    "Camada '{0}' inserida abaixo de '{1}'{2}; seleção desfeita."
                ).format(
                    nome,
                    nome_ativo or "camada ativa",
                    " como referência" if referencia else "",
                )
            )

        helpers.run_in_macro(documento, _inserir_agora)
