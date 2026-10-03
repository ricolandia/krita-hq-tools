"""Docker "HQ Tools: 3D": manequim 3D posável como camada de referência.

O modelo vem do exportador ``scripts/exportar-modelo3d.py`` (FBX -> JSON) e é
lido em Python puro (``core/modelo3d.py``); o Blender não é dependência em
tempo de execução. Arraste no preview para orbitar, use a roda para o zoom e
clique numa parte do corpo: os sliders daquela região aparecem. "Dobrar",
"Abrir" e "Girar" são mapeados para os eixos reais do rig (neste Auto-Rig Pro:
Z, X e Y). A inserção no documento é raster: o preview vira uma camada de
pintura, opcionalmente marcada como referência (travada, opacidade 150).
"""

import os

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core import modelo3d
from ...core import ui
from ...core.compat import (
    ALIGN_CENTER,
    IMAGE_FORMAT_RGBA8888,
    QImage,
    QSvgRenderer,
    TRANSPARENT,
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


class _Preview(QtWidgets.QLabel):
    """Área do preview: arrastar orbita, roda dá zoom, clique seleciona."""

    def __init__(self, docker):
        super().__init__()
        self.docker = docker
        self.setMinimumSize(240, 240)
        self.setAlignment(ALIGN_CENTER)
        self._ultimo = None
        self._arrastou = False

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.docker.agendar_render()

    def mousePressEvent(self, evento):
        self._ultimo = _posicao(evento)
        self._arrastou = False

    def mouseMoveEvent(self, evento):
        if self._ultimo is None:
            return
        posicao = _posicao(evento)
        delta = posicao - self._ultimo
        if abs(delta.x()) + abs(delta.y()) > 3:
            self._arrastou = True
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


class Viewer3DDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: 3D")
        self.modelo = None
        self.corpo = "homem"
        self.regiao = None
        self.semantica = {}
        self.pose_atual = None
        self.camera = {"yaw": 0.0, "pitch": -10.0, "zoom": 1.0}
        self._tela = []
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self.atualizar_preview)
        self._build_ui()
        self._carregar_modelo(aplicar_padrao=True)

    def canvasChanged(self, canvas):
        pass

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
        button_front = ui.botao("Frente", "Volta a câmera para a vista frontal.")
        button_front.clicked.connect(self.reset_camera)
        cameras.addWidget(button_front)
        button_reset = ui.botao("Limpar pose", "Zera todas as juntas.")
        button_reset.clicked.connect(self.limpar_pose)
        cameras.addWidget(button_reset)
        layout.addLayout(cameras)

        acoes = widgets.QHBoxLayout()
        button_layer = ui.botao(
            "Inserir como camada",
            "Rasteriza o preview na resolução do documento e insere no grupo ativo.",
            icone_chave="aplicar",
        )
        button_layer.clicked.connect(lambda: self.inserir(referencia=False))
        acoes.addWidget(button_layer)
        button_ref = ui.botao(
            "Inserir como referência",
            "Insere o preview travado, com rótulo de cor e opacidade reduzida.",
        )
        button_ref.clicked.connect(lambda: self.inserir(referencia=True))
        acoes.addWidget(button_ref)
        layout.addLayout(acoes)

        layout.addWidget(ui.rotulo(
            "Arraste para orbitar, roda do mouse dá zoom; clique numa região "
            "para abrir os sliders. Dobrar/Abrir/Girar seguem os eixos do rig."
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

    def atualizar_preview(self):
        if self.modelo is None:
            return
        largura = max(self.preview.width(), 200)
        altura = max(self.preview.height(), 200)
        rotacoes = self._rotacoes()
        posados = self.modelo.vertices_em_pose(rotacoes)
        estilo, cor, fundo = self._estilo()
        svg = self.modelo.renderizar(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            largura=largura,
            altura=altura,
            posados=posados,
            estilo=estilo,
            cor=cor,
            fundo=fundo,
        )
        self._tela = self.modelo.vertices_em_tela(
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            largura=largura,
            altura=altura,
            posados=posados,
        )
        if QSvgRenderer is None:
            return
        renderer = QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
        imagem = QImage(largura, altura, IMAGE_FORMAT_RGBA8888)
        imagem.fill(TRANSPARENT)
        painter = QtGui.QPainter(imagem)
        renderer.render(painter)
        painter.end()
        self.preview.setPixmap(QtGui.QPixmap.fromImage(imagem))

    def orbitar(self, dx, dy):
        self.camera["yaw"] = (self.camera["yaw"] + dx * 0.5) % 360.0
        self.camera["pitch"] = max(-89.0, min(89.0, self.camera["pitch"] + dy * 0.5))
        self.agendar_render()

    def aplicar_zoom(self, fator):
        self.camera["zoom"] = max(0.3, min(4.0, self.camera["zoom"] * fator))
        self.agendar_render()

    def reset_camera(self):
        self.camera = {"yaw": 0.0, "pitch": -10.0, "zoom": 1.0}
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

    def inserir(self, referencia=False):
        if self.modelo is None:
            helpers.show_info("3D", "O modelo não está disponível.")
            return
        documento = helpers.active_document()
        if documento is None:
            helpers.show_info("3D", "Abra um documento para inserir o desenho.")
            return
        largura = documento.width()
        altura = documento.height()
        estilo, cor, _ = self._estilo()
        svg = self.modelo.renderizar(
            self._rotacoes(),
            yaw=self.camera["yaw"],
            pitch=self.camera["pitch"],
            zoom=self.camera["zoom"],
            largura=largura,
            altura=altura,
            estilo=estilo,
            cor=cor,
        )
        renderer = QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
        imagem = QImage(largura, altura, IMAGE_FORMAT_RGBA8888)
        imagem.fill(TRANSPARENT)
        painter = QtGui.QPainter(imagem)
        renderer.render(painter)
        painter.end()
        rgba = imagem.convertToFormat(IMAGE_FORMAT_RGBA8888)
        dados = bytes(rgba.constBits().asstring(rgba.sizeInBytes()))
        nome = helpers.unique_layer_name(documento, "3D")
        camada = documento.createNode(nome, "paintlayer")
        if camada is None or not camada.setPixelData(dados, 0, 0, largura, altura):
            helpers.show_info("3D", "Não foi possível criar a camada.")
            return
        helpers.attach(documento, camada)
        if referencia:
            camada.setColorLabel(1)
            camada.setLocked(True)
            camada.setOpacity(150)
        documento.setActiveNode(camada)
        documento.refreshProjection()
        helpers.show_message(
            "Camada '{0}' inserida{1}.".format(
                nome, " como referência" if referencia else ""
            )
        )
