"""Docker de paletas: templates de HQ e paletas instaladas no Krita."""

import os
import shutil

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    ICON_MODE,
    LIST_ADJUST,
    LIST_STATIC,
    USER_ROLE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from ...core.gpl import load_gpl
from ...core.paths import KRITA_PALETTES_DIR
from ...core import ui

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

try:
    from krita import Palette, PaletteView
except ImportError:  # pragma: no cover
    Palette = None
    PaletteView = None


def swatch_pixmap(red, green, blue, size=24):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtGui.QColor(red, green, blue))
    return pixmap


class PalettesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: paletas")
        self.config = Config()
        self._palettes = {}
        self._build_ui()
        self._load_templates()
        self._load_krita_palettes()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)
        self.tabs = widgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_templates_tab(), "Templates de HQ")
        self.tabs.addTab(self._build_krita_tab(), "Paletas do Krita")
        self.setWidget(main)

    def _build_templates_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        row = widgets.QHBoxLayout()
        row.addWidget(ui.rotulo("Template:"))
        self.cmb_template = widgets.QComboBox()
        self.cmb_template.currentIndexChanged.connect(self._load_swatches)
        row.addWidget(self.cmb_template, 1)
        layout.addLayout(row)

        self.list_swatches = widgets.QListWidget()
        self.list_swatches.setViewMode(ICON_MODE)
        self.list_swatches.setIconSize(QtCore.QSize(26, 26))
        self.list_swatches.setGridSize(QtCore.QSize(28, 28))
        self.list_swatches.setSpacing(1)
        self.list_swatches.setUniformItemSizes(True)
        self.list_swatches.setResizeMode(LIST_ADJUST)
        self.list_swatches.setMovement(LIST_STATIC)
        layout.addWidget(self.list_swatches, 1)

        layout.addWidget(ui.separador())
        buttons = widgets.QHBoxLayout()
        button_fg = ui.botao("Aplicar na frente", "Define a cor de frente com o swatch selecionado.", icone_chave="aplicar")
        button_fg.clicked.connect(lambda: self.apply_swatch(True))
        buttons.addWidget(button_fg)
        button_bg = ui.botao("Aplicar no fundo", "Define a cor de fundo com o swatch selecionado.", icone_chave="aplicar")
        button_bg.clicked.connect(lambda: self.apply_swatch(False))
        buttons.addWidget(button_bg)
        layout.addLayout(buttons)

        buttons2 = widgets.QHBoxLayout()
        button_install = ui.botao("Instalar no Krita", "Copia os templates de paleta para a pasta de paletas do Krita.", icone_chave="salvar")
        button_install.clicked.connect(self.install_templates)
        buttons2.addWidget(button_install)
        button_folder = ui.botao("Abrir pasta do Krita", "Abre a pasta de paletas do Krita no explorador.", icone_chave="pasta")
        button_folder.clicked.connect(self.open_krita_folder)
        buttons2.addWidget(button_folder)
        layout.addLayout(buttons2)

        return tab

    def _build_krita_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        row = widgets.QHBoxLayout()
        row.addWidget(ui.rotulo("Paleta:"))
        self.cmb_krita = widgets.QComboBox()
        self.cmb_krita.currentIndexChanged.connect(self._on_krita_palette_changed)
        row.addWidget(self.cmb_krita, 1)
        button_refresh = ui.botao("Atualizar", "Recarrega a lista de paletas do Krita.", icone_chave="atualizar")
        button_refresh.clicked.connect(self._load_krita_palettes)
        row.addWidget(button_refresh)
        layout.addLayout(row)

        if PaletteView is not None:
            self.palette_view = PaletteView()
            layout.addWidget(self.palette_view, 1)
        else:  # pragma: no cover
            layout.addWidget(ui.rotulo("PaletteView indisponível nesta versão do Krita."))
            self.palette_view = None

        return tab

    def _template_files(self):
        try:
            names = sorted(os.listdir(TEMPLATES_DIR))
        except OSError:
            return []
        return [name for name in names if name.lower().endswith(".gpl")]

    def _load_templates(self):
        self.cmb_template.blockSignals(True)
        self.cmb_template.clear()
        for name in self._template_files():
            self.cmb_template.addItem(name)
        last = self.config.get("palettes.last_template")
        if last:
            index = self.cmb_template.findText(last)
            if index >= 0:
                self.cmb_template.setCurrentIndex(index)
        self.cmb_template.blockSignals(False)
        self._load_swatches()

    def _load_swatches(self):
        self.list_swatches.clear()
        name = self.cmb_template.currentText()
        if not name:
            return
        self.config.set("palettes.last_template", name)
        path = os.path.join(TEMPLATES_DIR, name)
        try:
            palette = load_gpl(path)
        except (OSError, ValueError):
            return
        for color in palette["colors"]:
            red, green, blue = color["rgb"]
            name = color.get("name") or ""
            hex_value = "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)
            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(swatch_pixmap(red, green, blue)))
            item.setData(USER_ROLE, (red, green, blue))
            item.setToolTip(
                "{0} ({1})".format(name, hex_value) if name else hex_value
            )
            self.list_swatches.addItem(item)

    def apply_swatch(self, foreground=True):
        view = helpers.active_view()
        if view is None:
            helpers.show_message("Abra um documento para aplicar a cor.")
            return
        item = self.list_swatches.currentItem()
        if item is None:
            helpers.show_message("Escolha uma cor na lista.")
            return
        red, green, blue = item.data(USER_ROLE)
        color = QtGui.QColor(red, green, blue)
        try:
            from krita import ManagedColor

            managed = ManagedColor.fromQColor(color)
        except (ImportError, TypeError):
            helpers.show_message("Não foi possível converter a cor.")
            return
        if foreground:
            view.setForeGroundColor(managed)
        else:
            view.setBackGroundColor(managed)

    def install_templates(self):
        os.makedirs(KRITA_PALETTES_DIR, exist_ok=True)
        installed = 0
        for name in self._template_files():
            source = os.path.join(TEMPLATES_DIR, name)
            target = os.path.join(KRITA_PALETTES_DIR, name)
            try:
                shutil.copy2(source, target)
                installed += 1
            except OSError:
                continue
        helpers.show_message(
            "{0} paletas instaladas. Reinicie o Krita para vê-las no docker "
            "de paletas.".format(installed)
        )

    def open_krita_folder(self):
        os.makedirs(KRITA_PALETTES_DIR, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(KRITA_PALETTES_DIR))

    def _load_krita_palettes(self):
        palettes = Krita.instance().resources("palette") or {}
        self._palettes = dict(palettes)
        self.cmb_krita.blockSignals(True)
        self.cmb_krita.clear()
        for name in sorted(self._palettes.keys()):
            self.cmb_krita.addItem(name)
        self.cmb_krita.blockSignals(False)
        self._on_krita_palette_changed()

    def _on_krita_palette_changed(self):
        if self.palette_view is None or Palette is None:
            return
        name = self.cmb_krita.currentText()
        resource = self._palettes.get(name)
        if resource is None:
            return
        try:
            self.palette_view.setPalette(Palette(resource))
        except (TypeError, RuntimeError):
            pass
