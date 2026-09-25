"""Docker de pincéis (v2): cartões com miniatura e nome, conjuntos e 16 slots.

Os conjuntos (Rascunho, Contornos, Aquarela/Guache, Acrílico/Óleo, Retículas)
são montados com os presets que o próprio Krita já tem instalados, buscados
por nome na inicialização. Cada cartão ativa o pincel num clique e pode ser
atribuído a um dos 16 slots, que ganham atalhos em Configurar Krita > Atalhos.
"""

import os
import shutil

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    ALIGN_CENTER_FULL,
    ICON_MODE,
    LIST_ADJUST,
    LIST_STATIC,
    TOOL_BUTTON_TEXT_BESIDE_ICON,
    QIcon,
    QPixmap,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from . import SLOT_COUNT, register_docker
from .sets import BRUSH_SETS, slot_suggestions, suggest_sets


def preset_icon(resource, fallback="P"):
    """Ícone do preset (a imagem do próprio .kpp) ou um quadrado com a inicial."""
    try:
        image = resource.image()
        if image is not None and not image.isNull():
            pixmap = QPixmap.fromImage(image.scaled(64, 64))
            return QIcon(pixmap)
    except (AttributeError, TypeError, RuntimeError):
        pass
    pixmap = QPixmap(64, 64)
    pixmap.fill(QtGui.QColor("#3a3a3a"))
    painter = QtGui.QPainter(pixmap)
    painter.setPen(QtGui.QColor("#ffffff"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(22)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), ALIGN_CENTER_FULL, fallback[:1].upper())
    painter.end()
    return QIcon(pixmap)


class BrushesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: pincéis")
        self.config = Config()
        self.resources = {}
        self.slot_names = [""] * SLOT_COUNT
        self.slot_buttons = []
        register_docker(self)
        self._build_ui()
        self.reload_presets()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        self.tabs = widgets.QTabWidget()
        self.tab_lists = {}
        self.tab_sets = {}
        for label, _ in BRUSH_SETS:
            self._add_set_tab(label)
        self._add_set_tab("Todos")
        layout.addWidget(self.tabs, 1)

        self.slots_box = widgets.QGroupBox("Slots (atalhos em Configurar Krita > Atalhos > HQ Tools)")
        slots_layout = widgets.QGridLayout(self.slots_box)
        for index in range(SLOT_COUNT):
            button = QtWidgets.QToolButton()
            button.setText("{0}:".format(index + 1))
            button.setToolButtonStyle(TOOL_BUTTON_TEXT_BESIDE_ICON)
            button.setSizePolicy(widgets.QSizePolicy.Expanding, widgets.QSizePolicy.Fixed)
            button.clicked.connect(lambda checked=False, slot=index: self.activate_slot(slot))
            slots_layout.addWidget(button, index // 4, index % 4)
            self.slot_buttons.append(button)
        layout.addWidget(self.slots_box)

        buttons = widgets.QHBoxLayout()
        button_reload = widgets.QPushButton("Atualizar presets")
        button_reload.clicked.connect(self.reload_presets)
        buttons.addWidget(button_reload)
        button_suggest = widgets.QPushButton("Preencher slots com sugestões")
        button_suggest.clicked.connect(self.apply_suggestions)
        buttons.addWidget(button_suggest)
        button_bundle = widgets.QPushButton("Instalar bundle...")
        button_bundle.setToolTip("Copia um .bundle (ex.: Cityscape, Pesi's Watercolors) para o Krita")
        button_bundle.clicked.connect(self.install_bundle)
        buttons.addWidget(button_bundle)
        layout.addLayout(buttons)

        hint = widgets.QLabel(
            "Clique no cartão para ativar o pincel; botão direito atribui ao slot. "
            "Os conjuntos buscam os presets já instalados no seu Krita."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setWidget(main)

    def _add_set_tab(self, label):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)
        list_widget = widgets.QListWidget()
        list_widget.setViewMode(ICON_MODE)
        list_widget.setIconSize(QtCore.QSize(72, 72))
        list_widget.setResizeMode(LIST_ADJUST)
        list_widget.setMovement(LIST_STATIC)
        list_widget.setWordWrap(True)
        list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        list_widget.itemClicked.connect(self.activate_item)
        list_widget.itemDoubleClicked.connect(self.activate_item)
        list_widget.customContextMenuRequested.connect(
            lambda position, widget=list_widget: self._slot_menu(widget, position)
        )
        layout.addWidget(list_widget, 1)
        self.tabs.addTab(tab, label)
        self.tab_lists[label] = list_widget
        self.tab_sets[label] = []

    def reload_presets(self):
        self.resources = dict(Krita.instance().resources("preset") or {})
        names = sorted(self.resources.keys())
        matched_sets = suggest_sets(names)
        for label, matched in matched_sets:
            self.tab_sets[label] = matched
        self.tab_sets["Todos"] = names

        stored = self.config.get("brushes.slots", [""] * SLOT_COUNT)
        if not isinstance(stored, list):
            stored = [""] * SLOT_COUNT
        while len(stored) < SLOT_COUNT:
            stored.append("")
        self.slot_names = [str(name or "") for name in stored[:SLOT_COUNT]]

        for label, list_widget in self.tab_lists.items():
            list_widget.clear()
            for name in self.tab_sets.get(label, []):
                item = QtWidgets.QListWidgetItem(name)
                item.setData(QtCore.Qt.UserRole, name)
                resource = self.resources.get(name)
                if resource is not None:
                    item.setIcon(preset_icon(resource, name))
                list_widget.addItem(item)
        self._refresh_slots()

    def _refresh_slots(self):
        for index, button in enumerate(self.slot_buttons):
            name = self.slot_names[index]
            resource = self.resources.get(name)
            icon = QIcon()
            if resource is not None:
                icon = preset_icon(resource, name)
            button.setIcon(icon)
            label = "{0}:".format(index + 1)
            if name:
                label += " " + name
            button.setText(label)

    def _current_item(self, list_widget, position):
        item = list_widget.itemAt(position)
        if item is None and list_widget.currentItem() is not None:
            item = list_widget.currentItem()
        return item

    def _slot_menu(self, list_widget, position):
        item = self._current_item(list_widget, position)
        if item is None:
            return
        preset = item.data(QtCore.Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        activate = menu.addAction("Ativar pincel")
        menu.addSeparator()
        for index in range(SLOT_COUNT):
            current = self.slot_names[index]
            action = menu.addAction(
                "Slot {0} ({1})".format(index + 1, current or "vazio")
            )
            action.setCheckable(True)
            action.setChecked(current == preset)
        chosen = menu.exec_(list_widget.viewport().mapToGlobal(position))
        if chosen is None:
            return
        if chosen == activate:
            self.activate_preset(preset)
            return
        slot = menu.actions().index(chosen) - 2
        self.slot_names[slot] = preset
        self._save_slots()
        self._refresh_slots()
        helpers.show_message("Slot {0} = {1}".format(slot + 1, preset))

    def activate_item(self, item):
        preset = item.data(QtCore.Qt.UserRole)
        if preset:
            self.activate_preset(preset)

    def activate_preset(self, name):
        view = helpers.active_view()
        resource = self.resources.get(name)
        if view is None:
            helpers.show_message("Abra um documento para trocar de pincel.")
            return
        if resource is None:
            helpers.show_message("Preset não encontrado: {0}".format(name))
            return
        view.activateResource(resource)
        helpers.show_message(name)

    def activate_slot(self, index):
        if index < 0 or index >= SLOT_COUNT:
            return
        name = self.slot_names[index]
        if not name:
            helpers.show_message("Slot {0} vazio. Clique com o botão direito em um pincel.".format(index + 1))
            return
        self.activate_preset(name)

    def _save_slots(self):
        self.config.set("brushes.slots", list(self.slot_names))

    def apply_suggestions(self):
        suggested = slot_suggestions(sorted(self.resources.keys()))
        self.slot_names = suggested[:SLOT_COUNT]
        self._save_slots()
        self._refresh_slots()
        helpers.show_message("Slots preenchidos com as sugestões dos conjuntos.")

    def install_bundle(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.widget(), "Escolher bundle de pincel (.bundle)", os.path.expanduser("~"), "*.bundle"
        )
        if not path:
            return
        target_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "krita")
        try:
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(path, os.path.join(target_dir, os.path.basename(path)))
        except OSError as error:
            helpers.show_message("Falha ao copiar o bundle: {0}".format(error))
            return
        helpers.show_message(
            "Bundle copiado. Reinicie o Krita e confira em Recursos (presets novos)."
        )