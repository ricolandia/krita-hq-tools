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
    CONTEXT_MENU,
    ICON_MODE,
    LIST_ADJUST,
    LIST_STATIC,
    NO_ITEM_FLAGS,
    SIZE_EXPANDING,
    SIZE_FIXED,
    SINGLE_SELECTION,
    TOOL_BUTTON_TEXT_BESIDE_ICON,
    USER_ROLE,
    QIcon,
    QPixmap,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core import registro, ui
from ...core.config import Config
from ...core.paths import BRUSHES_KIT_DIR, KRITA_HOME
from . import SLOT_COUNT, register_docker
from . import packs as packs_lib
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
        registro.registrar("brushes", self)
        self.config = Config()
        self.resources = {}
        self.slot_names = [""] * SLOT_COUNT
        self.slot_buttons = []
        register_docker(self)
        self._build_ui()
        self.reload_presets()
        self._refresh_packs()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        self.tabs = widgets.QTabWidget()
        self.tab_lists = {}
        self.tab_sets = {}
        for label, _ in BRUSH_SETS:
            self._add_set_tab(label)
        self._add_set_tab("Todos")
        self.tabs.addTab(self._build_packs_tab(), "Packs")
        self.tabs.addTab(self._build_community_tab(), "Comunidade")
        layout.addWidget(self.tabs, 1)

        self.slots_box = widgets.QGroupBox("Slots (atalhos em Configurar Krita > Atalhos > HQ Tools)")
        slots_layout = widgets.QGridLayout(self.slots_box)
        for index in range(SLOT_COUNT):
            button = QtWidgets.QToolButton()
            button.setText("{0}:".format(index + 1))
            button.setToolButtonStyle(TOOL_BUTTON_TEXT_BESIDE_ICON)
            button.setSizePolicy(SIZE_EXPANDING, SIZE_FIXED)
            button.clicked.connect(lambda checked=False, slot=index: self.activate_slot(slot))
            slots_layout.addWidget(button, index // 4, index % 4)
            self.slot_buttons.append(button)
        layout.addWidget(self.slots_box)

        buttons = widgets.QHBoxLayout()
        button_reload = ui.botao(
            "Atualizar presets",
            "Relê os arquivos .kpp dos packs instalados (não reinicia o Krita).",
            icone_chave="atualizar",
        )
        button_reload.clicked.connect(self.reload_presets)
        buttons.addWidget(button_reload)
        button_suggest = ui.botao(
            "Preencher slots com sugestões",
            "Sugere um pincel parecido com o que está selecionado para cada slot livre.",
        )
        button_suggest.clicked.connect(self.apply_suggestions)
        buttons.addWidget(button_suggest)
        layout.addLayout(buttons)

        hint = ui.rotulo(
            "Clique no cartão para ativar o pincel; botão direito atribui ao slot. "
            "Os conjuntos buscam os presets já instalados no seu Krita.")
        layout.addWidget(hint)

        self.setWidget(main)

    def _add_set_tab(self, label):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))
        list_widget = widgets.QListWidget()
        list_widget.setViewMode(ICON_MODE)
        list_widget.setIconSize(QtCore.QSize(72, 72))
        list_widget.setResizeMode(LIST_ADJUST)
        list_widget.setMovement(LIST_STATIC)
        list_widget.setWordWrap(True)
        list_widget.setContextMenuPolicy(CONTEXT_MENU)
        list_widget.itemClicked.connect(self.activate_item)
        list_widget.itemDoubleClicked.connect(self.activate_item)
        list_widget.customContextMenuRequested.connect(
            lambda position, widget=list_widget: self._slot_menu(widget, position)
        )
        layout.addWidget(list_widget, 1)
        self.tabs.addTab(tab, label)
        self.tab_lists[label] = list_widget
        self.tab_sets[label] = []

    def _build_packs_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))

        self.list_packs = widgets.QListWidget()
        self.list_packs.setSelectionMode(SINGLE_SELECTION)
        layout.addWidget(self.list_packs, 1)

        buttons = widgets.QHBoxLayout()
        button_install = ui.botao(
            "Instalar pack selecionado",
            "Copia os .kpp do pack selecionado para a pasta de pincel do Krita.",
            icone_chave="aplicar",
        )
        button_install.clicked.connect(self.install_pack)
        buttons.addWidget(button_install)
        button_bundle = ui.botao(
            "Instalar bundle...",
            "Copia um .bundle (ex.: Cityscape, Pesi's Watercolors) para o Krita",
            icone_chave="salvar",
        )
        button_bundle.clicked.connect(self.install_bundle)
        buttons.addWidget(button_bundle)
        layout.addLayout(buttons)

        buttons_extra = widgets.QHBoxLayout()
        button_license = ui.botao(
            "Ver licença", "Mostra a licença (e a autoria) do pack selecionado."
        )
        button_license.clicked.connect(self.view_pack_license)
        buttons_extra.addWidget(button_license)
        button_refresh = ui.botao(
            "Atualizar", "Relê os packs instalados e os do usuário.", icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self._refresh_packs)
        buttons_extra.addWidget(button_refresh)
        layout.addLayout(buttons_extra)

        hint = ui.rotulo(
            "Packs da comunidade incluídos com licença verificada (créditos em "
            "CREDITS.md). Instalar copia os arquivos para os recursos do Krita "
            "e exige reiniciar o programa.")
        layout.addWidget(hint)
        return tab

    def _build_community_tab(self):
        """Presets dos packs da comunidade já instalados no Krita."""
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = ui.espacamento(widgets.QVBoxLayout(tab))
        self.list_community = widgets.QListWidget()
        self.list_community.setViewMode(ICON_MODE)
        self.list_community.setIconSize(QtCore.QSize(72, 72))
        self.list_community.setResizeMode(LIST_ADJUST)
        self.list_community.setMovement(LIST_STATIC)
        self.list_community.setWordWrap(True)
        self.list_community.itemClicked.connect(self.activate_item)
        self.list_community.itemDoubleClicked.connect(self.activate_item)
        layout.addWidget(self.list_community, 1)
        hint = ui.rotulo(
            "Presets dos packs da comunidade já instalados no Krita, agrupados "
            "por pack. Clique para ativar; os créditos estão no CREDITS.md.")
        layout.addWidget(hint)
        return tab

    def _refresh_community(self):
        if not hasattr(self, "list_community"):
            return
        self.list_community.clear()
        for nome, caminho in packs_lib.listar_packs(BRUSHES_KIT_DIR).items():
            info = packs_lib.pack_info(caminho)
            aliases = packs_lib.preset_aliases(caminho)
            presentes = []
            for nome_arquivo, nome_interno in aliases:
                recurso_nome = (
                    nome_interno
                    if nome_interno in self.resources
                    else (nome_arquivo if nome_arquivo in self.resources else None)
                )
                if recurso_nome is not None:
                    presentes.append(recurso_nome)
            if not presentes:
                continue
            cabecalho = QtWidgets.QListWidgetItem(
                "{0} — {1} ({2})".format(
                    nome, info.get("autor", "autor?"), info.get("licenca", "licença?")
                )
            )
            cabecalho.setFlags(NO_ITEM_FLAGS)
            cabecalho.setToolTip(info.get("origem", ""))
            self.list_community.addItem(cabecalho)
            for recurso_nome in presentes:
                item = QtWidgets.QListWidgetItem("  {0}".format(recurso_nome))
                item.setData(USER_ROLE, recurso_nome)
                resource = self.resources.get(recurso_nome)
                if resource is not None:
                    item.setIcon(preset_icon(resource, recurso_nome))
                item.setToolTip("Clique para ativar (preset instalado)")
                self.list_community.addItem(item)

    def _refresh_packs(self):
        self.list_packs.clear()
        destinos = self._pack_destinos()
        for nome, caminho in packs_lib.listar_packs(BRUSHES_KIT_DIR).items():
            info = packs_lib.pack_info(caminho)
            autor = info.get("autor", "autor desconhecido")
            licenca = info.get("licenca", "licença desconhecida")
            marcador = " [instalado]" if packs_lib.pack_instalado(caminho, destinos) else ""
            item = QtWidgets.QListWidgetItem(
                "{0} — {1} ({2}){3}".format(nome, autor, licenca, marcador)
            )
            item.setData(USER_ROLE, caminho)
            item.setToolTip(info.get("origem", ""))
            self.list_packs.addItem(item)

    def _pack_destinos(self):
        return {tipo: os.path.join(KRITA_HOME, tipo) for tipo in packs_lib.TIPOS}

    def install_pack(self):
        item = self.list_packs.currentItem()
        if item is None:
            helpers.show_info("Packs", "Escolha um pack na lista.")
            return
        pack_dir = item.data(USER_ROLE)
        relatorio = []
        total = packs_lib.instalar_pack(pack_dir, self._pack_destinos(), relatorio)
        self._refresh_packs()
        texto = "Pack instalado: {0} arquivos copiados para os recursos do Krita.".format(total)
        if relatorio:
            texto += "\n\n" + "\n".join(sorted(set(relatorio)))
        texto += "\n\nReinicie o Krita para carregar os pincéis novos."
        helpers.show_info("Packs", texto)

    def view_pack_license(self):
        item = self.list_packs.currentItem()
        if item is None:
            helpers.show_info("Packs", "Escolha um pack na lista.")
            return
        pack_dir = item.data(USER_ROLE)
        info = packs_lib.pack_info(pack_dir)
        texto = packs_lib.pack_license(pack_dir)
        QtWidgets.QMessageBox.information(
            helpers.modal_parent(),
            "Licença de {0}".format(info.get("nome", pack_dir)),
            texto,
        )

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
                item.setData(USER_ROLE, name)
                resource = self.resources.get(name)
                if resource is not None:
                    item.setIcon(preset_icon(resource, name))
                list_widget.addItem(item)
        self._refresh_slots()
        self._refresh_community()

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
        preset = item.data(USER_ROLE)
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
        chosen = menu.exec(list_widget.viewport().mapToGlobal(position))
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
        preset = item.data(USER_ROLE)
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
        target_dir = KRITA_HOME
        try:
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(path, os.path.join(target_dir, os.path.basename(path)))
        except OSError as error:
            helpers.show_message("Falha ao copiar o bundle: {0}".format(error))
            return
        helpers.show_message(
            "Bundle copiado. Reinicie o Krita e confira em Recursos (presets novos)."
        )