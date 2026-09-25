"""Docker de retículas e hachuras.

Aplica o gerador nativo Screentone do Krita como camada de preenchimento
(retícula sobre a arte) ou como máscara do filtro Halftone (tom pintado vira
pontos ou linhas), sempre de forma não destrutiva e dentro do grupo ativo.
"""

import os

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import DIALOG_NO, DIALOG_YES, QtWidgets
from ...core.config import Config
from ...core.paths import USER_DIR
from . import core

USER_PRESETS_PATH = os.path.join(USER_DIR, "screentone_presets.json")


class ScreentoneDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: retículas")
        self.config = Config()
        self.bundled_presets = core.load_presets(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets.json")
        )
        self.user_presets = core.load_presets(USER_PRESETS_PATH)
        self._fg = "#000000"
        self._bg = "#ffffff"
        self._build_ui()
        self._reload_presets()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        preset_row = widgets.QHBoxLayout()
        preset_row.addWidget(widgets.QLabel("Preset:"))
        self.cmb_preset = widgets.QComboBox()
        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.cmb_preset, 1)
        button_save = widgets.QPushButton("Salvar como...")
        button_save.clicked.connect(self._save_preset)
        preset_row.addWidget(button_save)
        button_delete = widgets.QPushButton("Excluir")
        button_delete.clicked.connect(self._delete_preset)
        preset_row.addWidget(button_delete)
        layout.addLayout(preset_row)

        form = widgets.QFormLayout()

        self.cmb_pattern = widgets.QComboBox()
        for label, value in (("Pontos", core.PATTERN_DOTS), ("Linhas", core.PATTERN_LINES)):
            self.cmb_pattern.addItem(label, value)
        self.cmb_pattern.currentIndexChanged.connect(self._reload_shapes)
        form.addRow("Padrão:", self.cmb_pattern)

        self.cmb_shape = widgets.QComboBox()
        form.addRow("Forma:", self.cmb_shape)

        self.cmb_interpolation = widgets.QComboBox()
        for label, value in core.INTERPOLATIONS:
            self.cmb_interpolation.addItem(label, value)
        form.addRow("Interpolação:", self.cmb_interpolation)

        self.cmb_equalization = widgets.QComboBox()
        for label, value in core.EQUALIZATIONS:
            self.cmb_equalization.addItem(label, value)
        form.addRow("Equalização:", self.cmb_equalization)

        frequency_row = widgets.QHBoxLayout()
        self.spin_lpi = widgets.QDoubleSpinBox()
        self.spin_lpi.setRange(1.0, 200.0)
        self.spin_lpi.setDecimals(1)
        self.spin_lpi.setSingleStep(5.0)
        self.spin_lpi.valueChanged.connect(self._update_info)
        frequency_row.addWidget(self.spin_lpi, 1)
        self.cmb_units = widgets.QComboBox()
        for label, value in core.UNITS:
            self.cmb_units.addItem(label, value)
        frequency_row.addWidget(self.cmb_units, 1)
        form.addRow("Frequência:", frequency_row)

        self.spin_rotation = widgets.QDoubleSpinBox()
        self.spin_rotation.setRange(0.0, 180.0)
        self.spin_rotation.setDecimals(1)
        self.spin_rotation.setSuffix("°")
        form.addRow("Ângulo:", self.spin_rotation)

        self.spin_brightness = widgets.QDoubleSpinBox()
        self.spin_brightness.setRange(0.0, 100.0)
        self.spin_brightness.setSuffix("%")
        form.addRow("Brilho:", self.spin_brightness)

        self.spin_contrast = widgets.QDoubleSpinBox()
        self.spin_contrast.setRange(0.0, 100.0)
        self.spin_contrast.setSuffix("%")
        form.addRow("Contraste:", self.spin_contrast)

        self.spin_hardness = widgets.QDoubleSpinBox()
        self.spin_hardness.setRange(0.0, 100.0)
        self.spin_hardness.setSuffix("%")
        form.addRow("Dureza (meio-tom):", self.spin_hardness)

        self.chk_align = widgets.QCheckBox("Alinhar à grade de pixels")
        form.addRow("", self.chk_align)

        self.chk_invert = widgets.QCheckBox("Inverter (pontos brancos)")
        form.addRow("", self.chk_invert)

        self.chk_selection = widgets.QCheckBox("Usar a seleção ativa como máscara")
        self.chk_selection.setChecked(True)
        form.addRow("", self.chk_selection)

        colors_row = widgets.QHBoxLayout()
        self.btn_fg = widgets.QPushButton()
        self.btn_fg.setFixedHeight(24)
        self.btn_fg.clicked.connect(lambda: self._pick_color("fg"))
        colors_row.addWidget(widgets.QLabel("Frente:"))
        colors_row.addWidget(self.btn_fg, 1)
        self.btn_bg = widgets.QPushButton()
        self.btn_bg.setFixedHeight(24)
        self.btn_bg.clicked.connect(lambda: self._pick_color("bg"))
        colors_row.addWidget(widgets.QLabel("Fundo:"))
        colors_row.addWidget(self.btn_bg, 1)
        form.addRow("Cores:", colors_row)

        self.edit_name = widgets.QLineEdit("Retícula")
        form.addRow("Nome da camada:", self.edit_name)

        layout.addLayout(form)

        self.lbl_info = widgets.QLabel("")
        layout.addWidget(self.lbl_info)

        button_fill = widgets.QPushButton("Aplicar retícula (camada de preenchimento)")
        button_fill.clicked.connect(self.apply_fill)
        layout.addWidget(button_fill)

        button_halftone = widgets.QPushButton("Aplicar meio-tom (máscara de filtro)")
        button_halftone.clicked.connect(self.apply_halftone)
        layout.addWidget(button_halftone)

        hint = widgets.QLabel(
            "A retícula entra dentro do grupo ativo. A máscara de meio-tom usa o "
            "tom pintado na camada ativa."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch(1)

        self.setWidget(main)
        self._sync_colors()
        self._update_info()

    def _reload_shapes(self):
        self.cmb_shape.clear()
        for label, value in core.shapes_for_pattern(self.cmb_pattern.currentData()):
            self.cmb_shape.addItem(label, value)

    def _reload_presets(self):
        self.cmb_preset.blockSignals(True)
        self.cmb_preset.clear()
        for preset in self.bundled_presets + self.user_presets:
            self.cmb_preset.addItem(preset["name"], preset)
        last = self.config.get("screentone.last_preset")
        if last:
            index = self.cmb_preset.findText(last)
            if index >= 0:
                self.cmb_preset.setCurrentIndex(index)
        self.cmb_preset.blockSignals(False)
        self._on_preset_changed()

    def _on_preset_changed(self):
        preset = self.cmb_preset.currentData()
        if not preset:
            return
        preset = core.normalize_preset(preset)
        self.cmb_pattern.setCurrentIndex(
            self.cmb_pattern.findData(preset["pattern"])
        )
        self._reload_shapes()
        index = self.cmb_shape.findData(preset["shape"])
        if index >= 0:
            self.cmb_shape.setCurrentIndex(index)
        index = self.cmb_interpolation.findData(preset["interpolation"])
        if index >= 0:
            self.cmb_interpolation.setCurrentIndex(index)
        index = self.cmb_equalization.findData(preset["equalization"])
        if index >= 0:
            self.cmb_equalization.setCurrentIndex(index)
        self.spin_lpi.setValue(preset["lpi"])
        index = self.cmb_units.findData(preset["units"])
        if index >= 0:
            self.cmb_units.setCurrentIndex(index)
        self.spin_rotation.setValue(preset["rotation"])
        self.spin_brightness.setValue(preset["brightness"])
        self.spin_contrast.setValue(preset["contrast"])
        self.spin_hardness.setValue(preset["hardness"])
        self.chk_align.setChecked(preset["align"])
        self.chk_invert.setChecked(preset["invert"])
        self._fg = preset["fg"]
        self._bg = preset["bg"]
        self._sync_colors()
        self._update_info()
        self.config.set("screentone.last_preset", preset["name"])

    def current_preset(self):
        preset = dict(core.DEFAULT_PRESET)
        preset["name"] = self.edit_name.text().strip() or "Retícula"
        preset["pattern"] = self.cmb_pattern.currentData()
        preset["shape"] = self.cmb_shape.currentData()
        preset["interpolation"] = self.cmb_interpolation.currentData()
        preset["equalization"] = self.cmb_equalization.currentData()
        preset["lpi"] = self.spin_lpi.value()
        preset["units"] = self.cmb_units.currentData()
        preset["rotation"] = self.spin_rotation.value()
        preset["brightness"] = self.spin_brightness.value()
        preset["contrast"] = self.spin_contrast.value()
        preset["hardness"] = self.spin_hardness.value()
        preset["align"] = self.chk_align.isChecked()
        preset["invert"] = self.chk_invert.isChecked()
        preset["fg"] = self._fg
        preset["bg"] = self._bg
        return core.normalize_preset(preset)

    def _update_info(self):
        document = helpers.active_document()
        dpi = helpers.document_dpi(document) if document else 300.0
        cell = core.lpi_to_cell_px(self.spin_lpi.value(), dpi)
        limit = core.max_frequency(dpi)
        text = "Célula: {0:.2f} px a {1:.0f} dpi (máx. {2:.0f} LPI)".format(
            cell, dpi, limit
        )
        if self.spin_lpi.value() > limit:
            text += " — frequência acima do limite, será reduzida ao aplicar"
        self.lbl_info.setText(text)

    def _sync_colors(self):
        self.btn_fg.setStyleSheet(
            "background-color: {0}; border: 1px solid #666;".format(self._fg)
        )
        self.btn_bg.setStyleSheet(
            "background-color: {0}; border: 1px solid #666;".format(self._bg)
        )

    def _pick_color(self, which):
        from ...core.compat import QtGui

        current = self._fg if which == "fg" else self._bg
        color = QtGui.QColor(current)
        chosen = QtWidgets.QColorDialog.getColor(color, self.widget())
        if chosen.isValid():
            value = chosen.name()
            if which == "fg":
                self._fg = value
            else:
                self._bg = value
            self._sync_colors()

    def apply_fill(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para aplicar a retícula.")
            return
        preset = self.current_preset()
        dpi = helpers.document_dpi(document)
        properties = core.screentone_properties(preset, dpi)
        info = helpers.make_info_object(properties)
        selection = helpers.selection_for_apply(
            document, self.chk_selection.isChecked()
        )
        name = helpers.unique_layer_name(document, self.edit_name.text() or "Retícula")
        layer = document.createFillLayer(
            name, core.GENERATOR_ID, info, selection
        )
        if layer is None:
            helpers.show_message(
                "Gerador Screentone indisponível nesta versão do Krita."
            )
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message(
            "Retícula aplicada: {0} a {1} LPI.".format(preset["name"], preset["lpi"])
        )

    def apply_halftone(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para aplicar o meio-tom.")
            return
        node = document.activeNode()
        if node is None:
            helpers.show_message("Selecione a camada com o tom pintado.")
            return
        halftone = helpers.find_filter(*core.HALFTONE_FILTER_NAMES)
        if halftone is None:
            helpers.show_message("Filtro Halftone indisponível nesta versão do Krita.")
            return
        preset = self.current_preset()
        dpi = helpers.document_dpi(document)
        properties = core.halftone_properties(
            preset, document.colorModel(), dpi, "intensity"
        )
        configuration = halftone.configuration()
        if configuration is None:
            from krita import InfoObject

            configuration = InfoObject()
        configuration.setProperties(properties)
        halftone.setConfiguration(configuration)

        selection = document.selection()
        if selection is not None and self.chk_selection.isChecked():
            mask = document.createFilterMask("Meio-tom", halftone, selection)
        else:
            mask = document.createFilterMask("Meio-tom", halftone, node)
        if mask is None:
            helpers.show_message("Não foi possível criar a máscara de meio-tom.")
            return
        node.addChildNode(mask, None)
        document.refreshProjection()
        helpers.show_message("Meio-tom aplicado na camada ativa.")

    def _save_preset(self):
        from ...core.compat import QtWidgets as widgets

        name, ok = widgets.QInputDialog.getText(
            self.widget(), "Salvar preset", "Nome do preset:"
        )
        if not ok or not name.strip():
            return
        preset = self.current_preset()
        preset["name"] = name.strip()
        self.user_presets = [
            item for item in self.user_presets if item["name"] != preset["name"]
        ]
        self.user_presets.append(preset)
        core.save_presets(USER_PRESETS_PATH, self.user_presets)
        self._reload_presets()
        helpers.show_message("Preset salvo: {0}".format(preset["name"]))

    def _delete_preset(self):
        from ...core.compat import QtWidgets as widgets

        preset = self.cmb_preset.currentData()
        if not preset:
            return
        if preset not in self.user_presets:
            helpers.show_message("Presets de fábrica não podem ser excluídos.")
            return
        answer = widgets.QMessageBox.question(
            self.widget(),
            "Excluir preset",
            "Excluir o preset '{0}'?".format(preset["name"]),
            DIALOG_YES | DIALOG_NO,
        )
        if answer != DIALOG_YES:
            return
        self.user_presets = [
            item for item in self.user_presets if item["name"] != preset["name"]
        ]
        core.save_presets(USER_PRESETS_PATH, self.user_presets)
        self._reload_presets()
