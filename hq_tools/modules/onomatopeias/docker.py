"""Docker de onomatopeias: efeitos sonoros em SVG, inseridos como vetor.

A pasta padrão recebe as amostras do plugin na primeira execução; você pode
criar os seus modelos no Inkscape e salvá-los lá (SVG comum, com texto e
formas). Duplo clique insere no grupo ativo.
"""

import os
import shutil

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core.compat import (
    ICON_MODE,
    IMAGE_FORMAT_ARGB32,
    LIST_ADJUST,
    LIST_STATIC,
    QImage,
    QPixmap,
    QSvgRenderer,
    TRANSPARENT,
    USER_ROLE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from ...core import registro, ui
from ...core.paths import ONOMATOPEIAS_DIR

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def ensure_default_folder(config):
    """Pasta de onomatopeias, tolerando pasta configurada inacessível."""
    folder = config.get("onomatopeias.folder") or ONOMATOPEIAS_DIR
    try:
        os.makedirs(folder, exist_ok=True)
        if os.path.abspath(folder) == os.path.abspath(ONOMATOPEIAS_DIR):
            if not any(name.lower().endswith(".svg") for name in os.listdir(folder)):
                for name in sorted(os.listdir(SAMPLES_DIR)):
                    if name.lower().endswith(".svg"):
                        shutil.copy2(
                            os.path.join(SAMPLES_DIR, name), os.path.join(folder, name)
                        )
    except OSError as erro:
        helpers.log("pasta de onomatopeias inacessível ({0}): {1}".format(folder, erro))
        if os.path.abspath(folder) != os.path.abspath(ONOMATOPEIAS_DIR):
            try:
                os.makedirs(ONOMATOPEIAS_DIR, exist_ok=True)
                folder = ONOMATOPEIAS_DIR
            except OSError:
                pass
    return folder


def render_svg_thumbnail(path, size=120):
    if QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return None
    image = QImage(size, int(size * 0.6), IMAGE_FORMAT_ARGB32)
    image.fill(TRANSPARENT)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


class OnomatopoeiasDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: onomatopeias")
        registro.registrar("onomatopeias", self)
        self.config = Config()
        self.folder = ensure_default_folder(self.config)
        self._build_ui()
        self.refresh()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = ui.rotulo_info("")
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = ui.botao(
            "Pasta...",
            "Escolhe a pasta de modelos de onomatopeia; use Atualizar depois de adicionar SVGs.",
            icone_chave="pasta",
        )
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = ui.botao("Abrir", "Abre a pasta de modelos no explorador de arquivos.")
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        layout.addLayout(folder_row)

        self.list_items = widgets.QListWidget()
        self.list_items.setViewMode(ICON_MODE)
        self.list_items.setIconSize(QtCore.QSize(120, 72))
        self.list_items.setResizeMode(LIST_ADJUST)
        self.list_items.setMovement(LIST_STATIC)
        self.list_items.setWordWrap(True)
        self.list_items.itemDoubleClicked.connect(self.insert_effect)
        layout.addWidget(self.list_items, 1)

        buttons = widgets.QHBoxLayout()
        button_insert = ui.botao(
            "Inserir onomatopeia", "Insere o modelo selecionado na camada ativa."
        )
        button_insert.clicked.connect(self.insert_effect)
        buttons.addWidget(button_insert)
        button_refresh = ui.botao(
            "Atualizar", "Relê os modelos da pasta atual.", icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self.refresh)
        buttons.addWidget(button_refresh)
        layout.addLayout(buttons)

        hint = ui.rotulo(
            "Crie os seus modelos no Inkscape (texto + formas) e salve na pasta "
            "acima como SVG. Clique duas vezes para inserir no grupo ativo.")
        layout.addWidget(hint)

        self.setWidget(main)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), "Pasta de onomatopeias", self.folder
        )
        if folder:
            self.folder = folder
            self.config.set("onomatopeias.folder", folder)
            self.refresh()

    def open_folder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.folder))

    def refresh(self):
        self.lbl_folder.setText("Pasta: {0}".format(self.folder))
        self.list_items.clear()
        try:
            names = sorted(os.listdir(self.folder))
        except OSError as erro:
            names = []
            self.lbl_folder.setText(
                "Pasta: {0} (não pôde ser lida: {1})".format(self.folder, erro)
            )
        for name in names:
            if not name.lower().endswith(".svg"):
                continue
            path = os.path.join(self.folder, name)
            item = QtWidgets.QListWidgetItem(os.path.splitext(name)[0])
            item.setData(USER_ROLE, path)
            item.setToolTip(path)
            pixmap = render_svg_thumbnail(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_items.addItem(item)

    def insert_effect(self):
        """Insere a onomatopeia numa macro: um Ctrl+Z desfaz tudo."""
        document = helpers.active_document()
        helpers.run_in_macro(document, self._insert_effect)

    def _insert_effect(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para inserir a onomatopeia.")
            return
        item = self.list_items.currentItem()
        if item is None:
            helpers.show_message("Escolha uma onomatopeia na lista.")
            return
        path = item.data(USER_ROLE)
        try:
            svg = helpers.read_text_file(path)
        except OSError:
            helpers.show_message("Não foi possível ler o arquivo.")
            return
        name = helpers.unique_layer_name(document, item.text())
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message("Não foi possível criar a camada vetorial.")
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            # A camada já foi criada no documento: um SVG ruim deixava uma
            # camada vazia para o autor apagar à mão.
            try:
                document.removeNode(layer)
            except (AttributeError, RuntimeError):
                pass
            helpers.show_message(
                "O SVG não gerou formas. Verifique o arquivo (use texto e formas)."
            )
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message("Onomatopeia inserida: {0}".format(item.text()))