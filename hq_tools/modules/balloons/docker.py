"""Docker de balões (com aba de símbolos do Krita).

Mostra os modelos SVG de uma pasta (própria do usuário por padrão e amostras
do plugin) e insere o balão escolhido como camada vetorial no grupo ativo.
A aba "Símbolos do Krita" lista as bibliotecas de símbolos instaladas nos
recursos do Krita (``symbols/*.svg``), com inserção em um clique dentro do
grupo do painel.
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
from . import symbols as symbols_lib

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

SYMBOL_LICENSES = {
    "BalloonSymbols.svg": "Domínio público (Martin Owens, Tavmjong Bah, 2013)",
    "pepper_carrot_speech_bubbles.svg": "CC-BY-SA 4.0 (David Revoy)",
}


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
        self.libraries = {}
        self._symbols_cache = {}
        self._build_ui()
        self.refresh()
        self._load_symbol_libraries()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)
        self.tabs = widgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_balloons_tab(), "Balões")
        self.tabs.addTab(self._build_symbols_tab(), "Símbolos do Krita")
        self.setWidget(main)

    def _build_balloons_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

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
        return tab

    def _build_symbols_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        row = widgets.QHBoxLayout()
        row.addWidget(widgets.QLabel("Biblioteca:"))
        self.cmb_library = widgets.QComboBox()
        self.cmb_library.currentIndexChanged.connect(self._load_symbols_list)
        row.addWidget(self.cmb_library, 1)
        button_reload = widgets.QPushButton("Atualizar")
        button_reload.clicked.connect(self._load_symbol_libraries)
        row.addWidget(button_reload)
        layout.addLayout(row)

        self.lbl_license = widgets.QLabel("")
        self.lbl_license.setWordWrap(True)
        layout.addWidget(self.lbl_license)

        self.list_symbols = widgets.QListWidget()
        self.list_symbols.setViewMode(ICON_MODE)
        self.list_symbols.setIconSize(QtCore.QSize(96, 96))
        self.list_symbols.setResizeMode(LIST_ADJUST)
        self.list_symbols.setMovement(LIST_STATIC)
        self.list_symbols.setWordWrap(True)
        self.list_symbols.itemDoubleClicked.connect(self.insert_symbol)
        layout.addWidget(self.list_symbols, 1)

        button_insert = widgets.QPushButton("Inserir símbolo no grupo ativo")
        button_insert.clicked.connect(self.insert_symbol)
        layout.addWidget(button_insert)

        hint = widgets.QLabel(
            "Símbolos das bibliotecas instaladas em "
            "~/.local/share/krita/symbols (o Krita também tem um docker nativo; "
            "aqui a inserção é em um clique, dentro do grupo do painel)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return tab

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

    # ------------------------------------------------------------------ símbolos

    def _load_symbol_libraries(self):
        self.libraries = symbols_lib.list_libraries()
        self.cmb_library.blockSignals(True)
        self.cmb_library.clear()
        for name in sorted(self.libraries.keys()):
            self.cmb_library.addItem(name, name)
        self.cmb_library.blockSignals(False)
        self._load_symbols_list()

    def _load_symbols_list(self):
        self.list_symbols.clear()
        name = self.cmb_library.currentData()
        library = self.libraries.get(name)
        if not library:
            self.lbl_license.setText("Nenhuma biblioteca de símbolos encontrada.")
            return
        self.lbl_license.setText(
            "Licença: {0}".format(
                SYMBOL_LICENSES.get(name, "confira os metadados do arquivo")
            )
        )
        self._symbols_cache = {}
        renderer = None
        if QSvgRenderer is not None:
            renderer = QSvgRenderer(library["path"])
        for symbol in library["symbols"]:
            item = QtWidgets.QListWidgetItem(symbol["title"])
            item.setToolTip("{0} ({1})".format(symbol["id"], symbol["kind"]))
            item.setData(USER_ROLE, symbol["id"])
            self._symbols_cache[symbol["id"]] = symbol
            pixmap = self._render_symbol(renderer, symbol["id"])
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_symbols.addItem(item)

    def _render_symbol(self, renderer, element_id, size=96):
        if renderer is None or not renderer.isValid():
            return None
        try:
            bounds = renderer.boundsOnElement(element_id)
        except (TypeError, RuntimeError):
            return None
        if bounds is None or bounds.isEmpty():
            return None
        image = QImage(size, size, IMAGE_FORMAT_ARGB32)
        image.fill(TRANSPARENT)
        painter = QtGui.QPainter(image)
        try:
            renderer.render(painter, element_id)
        except (TypeError, RuntimeError):
            painter.end()
            return None
        painter.end()
        return QPixmap.fromImage(image)

    def insert_symbol(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para inserir o símbolo.")
            return
        item = self.list_symbols.currentItem()
        if item is None:
            helpers.show_message("Escolha um símbolo na lista.")
            return
        element_id = item.data(USER_ROLE)
        library_name = self.cmb_library.currentData()
        library = self.libraries.get(library_name)
        if not library:
            return
        try:
            with open(library["path"], "r", encoding="utf-8", errors="replace") as handle:
                source = handle.read()
            svg = symbols_lib.extract_symbol_svg(source, element_id)
        except (OSError, ValueError) as error:
            helpers.show_message("Não foi possível extrair o símbolo: {0}".format(error))
            return

        renderer = None
        if QSvgRenderer is not None:
            renderer = QSvgRenderer(library["path"])
            bounds = None
            if renderer.isValid():
                try:
                    bounds = renderer.boundsOnElement(element_id)
                except (TypeError, RuntimeError):
                    bounds = None
            if bounds is not None and not bounds.isEmpty():
                svg = svg.replace("</svg>", 'viewBox="{0} {1} {2} {3}"></svg>'.format(
                    bounds.x(), bounds.y(), bounds.width(), bounds.height()
                ))

        base = "text" if self.chk_text_layer.isChecked() else item.text()
        name = helpers.unique_layer_name(document, base)
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message("Não foi possível criar a camada vetorial.")
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            helpers.show_message(
                "O símbolo não gerou formas nesta versão do Krita; tente pelo "
                "docker nativo 'Bibliotecas de símbolos'."
            )
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message("Símbolo inserido: {0}".format(item.text()))