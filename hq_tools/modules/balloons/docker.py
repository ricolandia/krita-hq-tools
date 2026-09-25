"""Docker de balões vetoriais.

Mostra os modelos SVG de uma pasta (própria do usuário por padrão e amostras
do plugin) e insere o balão escolhido como camada vetorial no grupo ativo.
Como são vetores, o traço continua editável no Krita.
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
from ...core.paths import BALLOONS_DIR

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def ensure_default_folder(config):
    """Define a pasta padrão de balões e copia as amostras na primeira execução."""
    folder = config.get("balloons.folder") or BALLOONS_DIR
    os.makedirs(folder, exist_ok=True)
    if os.path.abspath(folder) == os.path.abspath(BALLOONS_DIR):
        if not any(name.lower().endswith(".svg") for name in os.listdir(folder)):
            for name in sorted(os.listdir(SAMPLES_DIR)):
                if name.lower().endswith(".svg"):
                    shutil.copy2(
                        os.path.join(SAMPLES_DIR, name), os.path.join(folder, name)
                    )
    return folder


def render_svg_thumbnail(path, size=120):
    """Renderiza um SVG em QPixmap para a lista; devolve None se indisponível."""
    if QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return None
    image = QImage(size, int(size * 0.75), IMAGE_FORMAT_ARGB32)
    image.fill(TRANSPARENT)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


class BalloonsDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: balões")
        self.config = Config()
        self.folder = ensure_default_folder(self.config)
        self._build_ui()
        self.refresh()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = widgets.QLabel("")
        self.lbl_folder.setWordWrap(True)
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = widgets.QPushButton("Pasta...")
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = widgets.QPushButton("Abrir")
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        layout.addLayout(folder_row)

        self.list_balloons = widgets.QListWidget()
        self.list_balloons.setViewMode(ICON_MODE)
        self.list_balloons.setIconSize(QtCore.QSize(120, 90))
        self.list_balloons.setResizeMode(LIST_ADJUST)
        self.list_balloons.setMovement(LIST_STATIC)
        self.list_balloons.setWordWrap(True)
        self.list_balloons.itemDoubleClicked.connect(self.insert_balloon)
        layout.addWidget(self.list_balloons, 1)

        self.chk_text_layer = widgets.QCheckBox(
            "Nomear a camada como 'text' (para o CPMT)"
        )
        self.chk_text_layer.setChecked(
            bool(self.config.get("balloons.insert_as_text_layer", False))
        )
        layout.addWidget(self.chk_text_layer)

        buttons = widgets.QHBoxLayout()
        button_insert = widgets.QPushButton("Inserir balão")
        button_insert.clicked.connect(self.insert_balloon)
        buttons.addWidget(button_insert)
        button_refresh = widgets.QPushButton("Atualizar")
        button_refresh.clicked.connect(self.refresh)
        buttons.addWidget(button_refresh)
        layout.addLayout(buttons)

        hint = widgets.QLabel(
            "Os modelos são SVGs comuns: você pode desenhar os seus e salvá-los "
            "na pasta acima. Clique duas vezes para inserir no grupo ativo."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setWidget(main)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), "Pasta de balões", self.folder
        )
        if folder:
            self.folder = folder
            self.config.set("balloons.folder", folder)
            self.refresh()

    def open_folder(self):
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(self.folder)
        )

    def refresh(self):
        self.lbl_folder.setText("Pasta: {0}".format(self.folder))
        self.list_balloons.clear()
        try:
            names = sorted(os.listdir(self.folder))
        except OSError:
            names = []
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
            self.list_balloons.addItem(item)

    def insert_balloon(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para inserir o balão.")
            return
        item = self.list_balloons.currentItem()
        if item is None:
            helpers.show_message("Escolha um balão na lista.")
            return
        path = item.data(USER_ROLE)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                svg = handle.read()
        except OSError:
            helpers.show_message("Não foi possível ler o arquivo do balão.")
            return
        base = "text" if self.chk_text_layer.isChecked() else item.text()
        name = helpers.unique_layer_name(document, base)
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message("Não foi possível criar a camada vetorial.")
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            helpers.show_message(
                "O SVG não gerou formas. Verifique o arquivo (use formas e texto)."
            )
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        self.config.set(
            "balloons.insert_as_text_layer", self.chk_text_layer.isChecked()
        )
        helpers.show_message("Balão inserido: {0}".format(item.text()))
