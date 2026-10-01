"""Docker de retículas e hachuras (v2).

Recursos: presets com LPI, edição da retícula selecionada, máscara vazia
(revelar pintando), mostrar área como seleção, reutilização de tons idênticos,
posição do padrão, tons com padrões instalados do Krita, meio-tom por canal
(CMYK) e linhas de efeito/velocidade.
"""

import os

from krita import DockWidget, Krita, Selection

from ...core import krita_helpers as helpers
from ...core.compat import DIALOG_NO, DIALOG_YES, QtWidgets
from ...core.config import Config
from ...core.paths import USER_DIR
from ...core import ui
from . import core
from . import effects

USER_PRESETS_PATH = os.path.join(USER_DIR, "screentone_presets.json")

MASK_MODES = (("Seleção ou documento inteiro", "selection"), ("Máscara vazia (revelar pintando)", "empty"))
HALFTONE_MODES = (("Intensidade (preto e branco)", "intensity"), ("Alfa (transparência)", "alpha"), ("Cores por canal (CMYK)", "cmyk"))
EFFECT_MODES = (("Foco (linhas de velocidade)", "focus"), ("Paralelas (linhas de efeito)", "parallel"))


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
        self._edit_fill_id = None
        self._edit_mask_id = None
        # Unidade que o valor da caixa de frequência representa agora; None
        # enquanto nenhum preset foi carregado (evita converter o valor inicial).
        self._unidades_ativas = None
        self._build_ui()
        self._reload_presets()
        self._reload_patterns()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)
        self.tabs = widgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_tones_tab(), "Retículas")
        self.tabs.addTab(self._build_effects_tab(), "Linhas de efeito")
        self.setWidget(main)
        self._sync_colors()
        self._update_info()
        self._update_pattern_enabled()
        self._update_effect_enabled()

    def _build_tones_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        preset_row = widgets.QHBoxLayout()
        preset_row.addWidget(ui.rotulo("Preset:"))
        self.cmb_preset = widgets.QComboBox()
        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.cmb_preset, 1)
        button_save = ui.botao("Salvar como...", "Salva o preset atual na pasta de presets do usuário.", icone_chave="salvar")
        button_save.clicked.connect(self._save_preset)
        preset_row.addWidget(button_save)
        button_delete = ui.botao("Excluir", "Exclui o preset selecionado do usuário.", icone_chave=None)
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
        self.cmb_units.currentIndexChanged.connect(self._on_units_changed)
        frequency_row.addWidget(self.cmb_units, 1)
        form.addRow("Frequência:", frequency_row)

        self.spin_rotation = widgets.QDoubleSpinBox()
        self.spin_rotation.setRange(0.0, 180.0)
        self.spin_rotation.setDecimals(1)
        self.spin_rotation.setSuffix("°")
        form.addRow("Ângulo:", self.spin_rotation)

        position_row = widgets.QHBoxLayout()
        self.spin_pos_x = widgets.QDoubleSpinBox()
        self.spin_pos_x.setRange(-10000.0, 10000.0)
        self.spin_pos_x.setDecimals(0)
        position_row.addWidget(self.spin_pos_x, 1)
        self.spin_pos_y = widgets.QDoubleSpinBox()
        self.spin_pos_y.setRange(-10000.0, 10000.0)
        self.spin_pos_y.setDecimals(0)
        position_row.addWidget(self.spin_pos_y, 1)
        form.addRow("Posição X/Y (px):", position_row)

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

        pattern_row = widgets.QHBoxLayout()
        self.chk_pattern = widgets.QCheckBox("Usar padrão do Krita")
        self.chk_pattern.toggled.connect(self._update_pattern_enabled)
        pattern_row.addWidget(self.chk_pattern)
        self.cmb_krita_pattern = widgets.QComboBox()
        pattern_row.addWidget(self.cmb_krita_pattern, 1)
        form.addRow("Tom por padrão:", pattern_row)

        self.chk_selection = widgets.QCheckBox("Usar a seleção ativa como máscara")
        self.chk_selection.setChecked(True)
        form.addRow("", self.chk_selection)

        self.cmb_mask = widgets.QComboBox()
        for label, value in MASK_MODES:
            self.cmb_mask.addItem(label, value)
        form.addRow("Aplicação:", self.cmb_mask)

        self.chk_reuse = widgets.QCheckBox("Reutilizar retícula idêntica já existente")
        self.chk_reuse.setChecked(True)
        form.addRow("", self.chk_reuse)

        self.cmb_halftone = widgets.QComboBox()
        for label, value in HALFTONE_MODES:
            self.cmb_halftone.addItem(label, value)
        form.addRow("Meio-tom:", self.cmb_halftone)

        # Botões só com a cor (o papel é pintado por _sync_colors), sem altura
        # fixa: quem manda no tamanho é o tema do Krita.
        colors_row = widgets.QHBoxLayout()
        colors_row.addWidget(ui.rotulo("Frente:"))
        self.btn_fg = ui.botao(
            "", "Escolhe a cor da frente (o que sai do pincel)."
        )
        self.btn_fg.clicked.connect(lambda: self._pick_color("fg"))
        colors_row.addWidget(self.btn_fg, 1)
        colors_row.addWidget(ui.rotulo("Fundo:"))
        self.btn_bg = ui.botao("", "Escolhe a cor do fundo (o que fica embaixo).")
        self.btn_bg.clicked.connect(lambda: self._pick_color("bg"))
        colors_row.addWidget(self.btn_bg, 1)
        form.addRow("Cores:", colors_row)

        self.edit_name = widgets.QLineEdit("Retícula")
        form.addRow("Nome da camada:", self.edit_name)

        layout.addLayout(form)

        self.lbl_info = ui.rotulo_info()
        layout.addWidget(self.lbl_info)

        button_fill = ui.botao(
            "Aplicar retícula (camada de preenchimento)",
            "Cria uma camada com o padrão repetido na tela, dentro do grupo ativo.",
            icone_chave="aplicar",
        )
        button_fill.clicked.connect(self.apply_fill)
        layout.addWidget(button_fill)

        button_halftone = ui.botao(
            "Aplicar meio-tom (máscara de filtro)",
            "Cria a retícula como máscara de filtro: pintar aplica a textura.",
            icone_chave="aplicar",
        )
        button_halftone.clicked.connect(self.apply_halftone)
        layout.addWidget(button_halftone)
        layout.addWidget(ui.separador())

        edit_row = widgets.QHBoxLayout()
        button_edit = ui.botao(
            "Editar selecionada",
            "Carrega as opções da camada ou máscara de retícula ativa.",
        )
        button_edit.clicked.connect(self.edit_selected)
        edit_row.addWidget(button_edit)
        button_area = ui.botao(
            "Mostrar área",
            "Transforma a máscara de retícula ativa em seleção, para pintar só nela.",
        )
        button_area.clicked.connect(self.show_area)
        edit_row.addWidget(button_area)
        layout.addLayout(edit_row)

        hint = ui.rotulo(
            "A retícula entra dentro do grupo ativo. 'Editar selecionada' carrega "
            "as opções da camada/máscara ativa; 'Mostrar área' transforma a "
            "máscara em seleção.")
        layout.addWidget(hint)

        button_patterns = ui.botao(
            "Instalar padrões e texturas (kit)",
            "Copia os padrões próprios do kit (papéis, retículas, hachuras) "
            "para os padrões do Krita",
            icone_chave="salvar",
        )
        button_patterns.clicked.connect(self.install_kit_patterns)
        layout.addWidget(button_patterns)
        layout.addStretch(1)
        return tab

    def _build_effects_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        form = widgets.QFormLayout()
        self.cmb_effect = widgets.QComboBox()
        for label, value in EFFECT_MODES:
            self.cmb_effect.addItem(label, value)
        self.cmb_effect.currentIndexChanged.connect(self._update_effect_enabled)
        form.addRow("Tipo:", self.cmb_effect)

        self.spin_focus_x = widgets.QDoubleSpinBox()
        self.spin_focus_x.setRange(0.0, 100.0)
        self.spin_focus_x.setSuffix("%")
        self.spin_focus_x.setValue(50.0)
        form.addRow("Foco X:", self.spin_focus_x)

        self.spin_focus_y = widgets.QDoubleSpinBox()
        self.spin_focus_y.setRange(0.0, 100.0)
        self.spin_focus_y.setSuffix("%")
        self.spin_focus_y.setValue(50.0)
        form.addRow("Foco Y:", self.spin_focus_y)

        self.spin_lines = widgets.QSpinBox()
        self.spin_lines.setRange(2, 120)
        self.spin_lines.setValue(24)
        form.addRow("Linhas:", self.spin_lines)

        self.spin_effect_thickness = widgets.QDoubleSpinBox()
        self.spin_effect_thickness.setRange(0.2, 20.0)
        self.spin_effect_thickness.setDecimals(1)
        self.spin_effect_thickness.setValue(2.0)
        form.addRow("Espessura (px):", self.spin_effect_thickness)

        self.spin_inset = widgets.QDoubleSpinBox()
        self.spin_inset.setRange(0.0, 90.0)
        self.spin_inset.setSuffix("%")
        self.spin_inset.setValue(12.0)
        form.addRow("Começo longe do foco:", self.spin_inset)

        self.spin_spacing = widgets.QDoubleSpinBox()
        self.spin_spacing.setRange(1.0, 200.0)
        self.spin_spacing.setDecimals(1)
        self.spin_spacing.setValue(12.0)
        form.addRow("Espaçamento (px):", self.spin_spacing)

        self.spin_angle = widgets.QDoubleSpinBox()
        self.spin_angle.setRange(-180.0, 180.0)
        self.spin_angle.setDecimals(1)
        self.spin_angle.setSuffix("°")
        form.addRow("Ângulo (paralelas):", self.spin_angle)

        self.spin_region_x = widgets.QDoubleSpinBox()
        self.spin_region_x.setRange(0.0, 100.0)
        self.spin_region_x.setSuffix("%")
        form.addRow("Região X:", self.spin_region_x)

        self.spin_region_y = widgets.QDoubleSpinBox()
        self.spin_region_y.setRange(0.0, 100.0)
        self.spin_region_y.setSuffix("%")
        form.addRow("Região Y:", self.spin_region_y)

        self.spin_region_w = widgets.QDoubleSpinBox()
        self.spin_region_w.setRange(5.0, 100.0)
        self.spin_region_w.setSuffix("%")
        self.spin_region_w.setValue(80.0)
        form.addRow("Região Larg.:", self.spin_region_w)

        self.spin_region_h = widgets.QDoubleSpinBox()
        self.spin_region_h.setRange(5.0, 100.0)
        self.spin_region_h.setSuffix("%")
        self.spin_region_h.setValue(60.0)
        form.addRow("Região Alt.:", self.spin_region_h)

        layout.addLayout(form)

        button_effects = ui.botao(
            "Inserir linhas de efeito",
            "Cria a camada vetorial de linhas de velocidade ou de efeito.",
            icone_chave="aplicar",
        )
        button_effects.clicked.connect(self.insert_effect_lines)
        layout.addWidget(button_effects)

        hint = ui.rotulo(
            "Foco: linhas radiais saindo de um ponto (linhas de velocidade). "
            "Paralelas: linhas preenchendo a região indicada. A camada é vetorial.")
        layout.addWidget(hint)
        layout.addStretch(1)
        return tab

    def _update_effect_enabled(self):
        focus = self.cmb_effect.currentData() == "focus"
        for spin in (self.spin_focus_x, self.spin_focus_y, self.spin_inset):
            spin.setEnabled(focus)
        for spin in (self.spin_spacing, self.spin_angle, self.spin_region_x,
                     self.spin_region_y, self.spin_region_w, self.spin_region_h):
            spin.setEnabled(not focus)

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

    def _reload_patterns(self):
        patterns = dict(Krita.instance().resources("pattern") or {})
        self.cmb_krita_pattern.blockSignals(True)
        self.cmb_krita_pattern.clear()
        for name in sorted(patterns.keys()):
            self.cmb_krita_pattern.addItem(name, name)
        self.cmb_krita_pattern.blockSignals(False)

    def _update_pattern_enabled(self):
        self.cmb_krita_pattern.setEnabled(self.chk_pattern.isChecked())

    def _on_preset_changed(self):
        preset = self.cmb_preset.currentData()
        if not preset:
            return
        preset = core.normalize_preset(preset)
        self.cmb_pattern.setCurrentIndex(self.cmb_pattern.findData(preset["pattern"]))
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
        self._unidades_ativas = int(preset["units"])
        self.spin_lpi.setValue(preset["lpi"])
        index = self.cmb_units.findData(preset["units"])
        if index >= 0:
            self.cmb_units.setCurrentIndex(index)
        self.spin_rotation.setValue(preset["rotation"])
        self.spin_pos_x.setValue(preset.get("position_x", 0.0))
        self.spin_pos_y.setValue(preset.get("position_y", 0.0))
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
        preset["position_x"] = self.spin_pos_x.value()
        preset["position_y"] = self.spin_pos_y.value()
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
        units = self.cmb_units.currentData() or core.UNITS_LPI
        lpi = core.to_lpi(self.spin_lpi.value(), units)
        cell = core.lpi_to_cell_px(lpi, dpi)
        limit = core.from_lpi(core.max_frequency(dpi), units)
        unidade = core.rotulo_unidade(units)
        text = "Célula: {0:.2f} px a {1:.0f} dpi (máx. {2:.0f} {3})".format(
            cell, dpi, limit, unidade
        )
        if self.spin_lpi.value() > limit:
            text += " — frequência acima do limite, será reduzida ao aplicar"
        self.lbl_info.setText(text)

    def _on_units_changed(self, _index):
        """Trocar LPI por LPC converte o valor, para a densidade não mudar 2,5x."""
        novo = self.cmb_units.currentData()
        if novo is None:
            return
        origem = self._unidades_ativas
        self._unidades_ativas = novo
        if origem is not None and origem != novo:
            self.spin_lpi.blockSignals(True)
            self.spin_lpi.setValue(
                min(
                    self.spin_lpi.maximum(),
                    max(
                        self.spin_lpi.minimum(),
                        core.from_lpi(core.to_lpi(self.spin_lpi.value(), origem), novo),
                    ),
                )
            )
            self.spin_lpi.blockSignals(False)
        self._update_info()

    def _sync_colors(self):
        self.btn_fg.setStyleSheet("background-color: {0}; border: 1px solid #666;".format(self._fg))
        self.btn_bg.setStyleSheet("background-color: {0}; border: 1px solid #666;".format(self._bg))

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

    # ------------------------------------------------------------------ ações

    def _current_generator(self):
        if self.chk_pattern.isChecked() and self.cmb_krita_pattern.currentData():
            return core.PATTERN_GENERATOR_ID, self.cmb_krita_pattern.currentData()
        return core.GENERATOR_ID, None

    def _apply_selection(self, document):
        mode = self.cmb_mask.currentData()
        if mode == "empty":
            return helpers.full_selection(document)
        if self.chk_selection.isChecked():
            # Só a seleção com pixels vale: uma seleção vazia geraria máscara
            # de 0 px e o filtro não faria nada, sem aviso.
            selecao = helpers.active_selection(document)
            if selecao is not None:
                return selecao
        return helpers.full_selection(document)

    def _find_same_tone(self, document, generator, fingerprint):
        root = document.rootNode()
        for node in root.findChildNodes(recursive=True):
            if node.type() != "filllayer":
                continue
            if node.generatorName() != generator:
                continue
            props = node.filterConfig().properties()
            if generator == core.PATTERN_GENERATOR_ID:
                if fingerprint and props.get("pattern") == fingerprint:
                    return node
            else:
                if fingerprint is not None and core.tone_fingerprint(props) == fingerprint:
                    return node
        return None

    def _set_selection_mask(self, document, layer, selection):
        for child in layer.childNodes():
            if child.type() == "selectionmask":
                child.setSelection(selection)
                return child
        mask = document.createSelectionMask("Seleção")
        if mask is None:
            return None
        layer.addChildNode(mask, None)
        mask.setSelection(selection)
        return mask

    def _node_id(self, node):
        """Identificador estável do nó (para reencontrá-lo depois)."""
        try:
            return str(node.uniqueId())
        except (AttributeError, RuntimeError):
            return None

    def _find_node_by_id(self, document, node_id):
        """Nó do documento com o id dado, ou None (camada apagada/movida)."""
        if not node_id:
            return None
        for node in document.rootNode().findChildNodes(recursive=True):
            if self._node_id(node) == node_id:
                return node
        return None

    def _update_selection(self, document):
        """Seleção para atualizar um tom em edição.

        Sem seleção ativa (e sem o modo "máscara vazia"), devolve None para
        manter a máscara existente em vez de cobrir a página inteira.
        """
        if self.cmb_mask.currentData() == "empty":
            return Selection()
        if self.chk_selection.isChecked():
            return helpers.active_selection(document)
        return None

    def _update_fill_layer(self, document, layer, generator, properties):
        """Atualiza uma camada de preenchimento em edição (mesma camada)."""
        try:
            info = helpers.make_info_object(properties)
            if not layer.setGenerator(generator, info):
                return False
        except (AttributeError, RuntimeError, TypeError):
            return False
        document.refreshProjection()
        document.setActiveNode(layer)
        return True

    def _update_filter_mask(self, document, mask, properties):
        """Atualiza a configuração da máscara de meio-tom em edição."""
        try:
            halftone = mask.filter()
            if halftone is None:
                return False
            configuration = halftone.configuration()
            if configuration is None:
                configuration = helpers.make_info_object({})
            configuration.setProperties(properties)
            halftone.setConfiguration(configuration)
            mask.setFilter(halftone)
        except (AttributeError, RuntimeError, TypeError):
            return False
        document.refreshProjection()
        return True

    def apply_fill(self):
        """Aplica a retícula numa macro: um Ctrl+Z desfaz tudo."""
        document = helpers.active_document()
        helpers.run_in_macro(document, self._apply_fill)

    def _apply_fill(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para aplicar a retícula.")
            return
        preset = self.current_preset()
        dpi = helpers.document_dpi(document)
        generator, pattern_name = self._current_generator()

        if generator == core.PATTERN_GENERATOR_ID:
            properties = core.pattern_fill_properties(pattern_name)
        else:
            properties = core.screentone_properties(preset, dpi)

        target = self._find_node_by_id(document, self._edit_fill_id)
        self._edit_fill_id = None
        if target is not None and target.type() == "filllayer":
            if self._update_fill_layer(document, target, generator, properties):
                selection = self._update_selection(document)
                if selection is not None:
                    self._set_selection_mask(document, target, selection)
                helpers.show_message("Retícula atualizada: {0}.".format(target.name()))
                return

        selection = self._apply_selection(document)
        fingerprint = None
        if self.cmb_mask.currentData() != "empty":
            if self.chk_reuse.isChecked() and generator == core.PATTERN_GENERATOR_ID:
                fingerprint = pattern_name
            elif self.chk_reuse.isChecked():
                fingerprint = core.tone_fingerprint(properties)
        if fingerprint is not None:
            existing = self._find_same_tone(document, generator, fingerprint)
            if existing is not None:
                self._set_selection_mask(document, existing, selection)
                document.refreshProjection()
                helpers.show_message("Retícula idêntica reutilizada em '{0}'.".format(existing.name()))
                return

        info = helpers.make_info_object(properties)
        name = helpers.unique_layer_name(document, self.edit_name.text() or "Retícula")
        layer = document.createFillLayer(name, generator, info, selection)
        if layer is None:
            helpers.show_message("Gerador indisponível nesta versão do Krita.")
            return
        helpers.attach(document, layer)
        if self.cmb_mask.currentData() == "empty":
            self._set_selection_mask(document, layer, Selection())
        document.setActiveNode(layer)
        helpers.show_message("Retícula aplicada: {0} a {1} LPI.".format(preset["name"], preset["lpi"]))

    def apply_halftone(self):
        """Aplica o meio-tom numa macro: um Ctrl+Z desfaz tudo."""
        document = helpers.active_document()
        helpers.run_in_macro(document, self._apply_halftone)

    def _apply_halftone(self):
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
        generator, pattern_name = self._current_generator()
        mode = self.cmb_halftone.currentData()

        if mode == "cmyk":
            properties = core.halftone_cmyk_properties(preset, document.colorModel(), dpi)
        else:
            properties = core.halftone_properties(
                preset, document.colorModel(), dpi,
                mode=mode, generator=generator, pattern_name=pattern_name,
            )

        target = self._find_node_by_id(document, self._edit_mask_id)
        self._edit_mask_id = None
        if target is not None and target.type() == "filtermask":
            if self._update_filter_mask(document, target, properties):
                helpers.show_message("Meio-tom atualizado.")
                return

        configuration = halftone.configuration()
        if configuration is None:
            configuration = helpers.make_info_object({})
        configuration.setProperties(properties)
        halftone.setConfiguration(configuration)

        selecao = helpers.active_selection(document) if self.chk_selection.isChecked() else None
        if selecao is not None:
            mask = document.createFilterMask("Meio-tom", halftone, selecao)
        else:
            mask = document.createFilterMask("Meio-tom", halftone, node)
        if mask is None:
            helpers.show_message("Não foi possível criar a máscara de meio-tom.")
            return
        node.addChildNode(mask, None)
        document.refreshProjection()
        helpers.show_message("Meio-tom aplicado na camada ativa.")

    def _set_screentone_fields(self, props):
        for key, default in (
            ("pattern", 0), ("shape", 0), ("interpolation", 0),
            ("equalization_mode", 2), ("units", 0), ("rotation", 45.0),
            ("brightness", 50.0), ("contrast", 95.0), ("invert", False),
            ("align_to_pixel_grid", True),
        ):
            if key not in props:
                continue
            value = props[key]
            if key == "pattern":
                index = self.cmb_pattern.findData(int(value))
                if index >= 0:
                    self.cmb_pattern.setCurrentIndex(index)
                    self._reload_shapes()
            elif key == "shape":
                index = self.cmb_shape.findData(int(value))
                if index >= 0:
                    self.cmb_shape.setCurrentIndex(index)
            elif key == "interpolation":
                index = self.cmb_interpolation.findData(int(value))
                if index >= 0:
                    self.cmb_interpolation.setCurrentIndex(index)
            elif key == "equalization_mode":
                index = self.cmb_equalization.findData(int(value))
                if index >= 0:
                    self.cmb_equalization.setCurrentIndex(index)
            elif key == "units":
                if key == "units":
                    self._unidades_ativas = int(value)
                index = self.cmb_units.findData(int(value))
                if index >= 0:
                    self.cmb_units.setCurrentIndex(index)
            elif key == "rotation":
                self.spin_rotation.setValue(float(value))
            elif key == "brightness":
                self.spin_brightness.setValue(float(value))
            elif key == "contrast":
                self.spin_contrast.setValue(float(value))
            elif key == "invert":
                self.chk_invert.setChecked(bool(value))
            elif key == "align_to_pixel_grid":
                self.chk_align.setChecked(bool(value))
        if "frequency_x" in props:
            self.spin_lpi.setValue(float(props["frequency_x"]))
        if "position_x" in props:
            self.spin_pos_x.setValue(float(props["position_x"]))
        if "position_y" in props:
            self.spin_pos_y.setValue(float(props["position_y"]))
        fg = core.color_xml_to_hex(props.get("foreground_color"))
        if fg:
            self._fg = fg
        bg = core.color_xml_to_hex(props.get("background_color"))
        if bg:
            self._bg = bg
        self._sync_colors()
        self._update_info()

    def _populate_fill(self, layer):
        generator = layer.generatorName()
        props = layer.filterConfig().properties()
        if generator == core.PATTERN_GENERATOR_ID:
            name = props.get("pattern")
            self.chk_pattern.setChecked(True)
            index = self.cmb_krita_pattern.findText(str(name))
            if index >= 0:
                self.cmb_krita_pattern.setCurrentIndex(index)
            self._update_pattern_enabled()
            return
        if generator == core.GENERATOR_ID:
            self.chk_pattern.setChecked(False)
            self._update_pattern_enabled()
            self._set_screentone_fields(props)
            return
        helpers.show_message("A camada usa o gerador '{0}', sem edição aqui.".format(generator))

    def _populate_mask(self, mask):
        halftone_filter = mask.filter()
        if halftone_filter is None:
            helpers.show_message("Não foi possível ler a máscara.")
            return
        props = halftone_filter.configuration().properties()
        mode = props.get("mode", "intensity")
        data = {
            "intensity": "intensity", "alpha": "alpha",
            "independent_channels": "cmyk",
        }.get(mode, "intensity")
        index = self.cmb_halftone.findData(data)
        if index >= 0:
            self.cmb_halftone.setCurrentIndex(index)
        generator = props.get("{0}_generator".format(mode))
        if generator == core.PATTERN_GENERATOR_ID:
            name = props.get("{0}_generator_pattern_pattern".format(mode))
            self.chk_pattern.setChecked(True)
            found = self.cmb_krita_pattern.findText(str(name))
            if found >= 0:
                self.cmb_krita_pattern.setCurrentIndex(found)
            self._update_pattern_enabled()
        elif generator == core.GENERATOR_ID:
            self.chk_pattern.setChecked(False)
            self._update_pattern_enabled()
            prefix = "{0}_generator_screentone_".format(mode)
            screentone = {
                key[len(prefix):]: value
                for key, value in props.items()
                if key.startswith(prefix)
            }
            if screentone:
                self._set_screentone_fields(screentone)
            if "{0}_hardness".format(mode) in props:
                self.spin_hardness.setValue(float(props["{0}_hardness".format(mode)]))

    def edit_selected(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para editar a retícula.")
            return
        node = document.activeNode()
        if node is None:
            helpers.show_message("Selecione a camada de retícula ou a máscara de meio-tom.")
            return
        # Só uma edição pendente por vez. Sem limpar o outro id, editar uma
        # máscara depois de uma camada deixava o alvo antigo no lugar, e o
        # "Aplicar retícula" ia mexer numa camada que o autor não estava
        # editando (ou nem existia mais no documento atual).
        self._edit_fill_id = None
        self._edit_mask_id = None
        if node.type() == "filllayer":
            self._edit_fill_id = self._node_id(node)
            self._populate_fill(node)
            helpers.show_message("Opções carregadas; use Aplicar retícula para atualizar.")
        elif node.type() == "filtermask":
            self._edit_mask_id = self._node_id(node)
            self._populate_mask(node)
            helpers.show_message("Opções carregadas; use Aplicar meio-tom para atualizar.")
        else:
            helpers.show_message("Selecione a camada de retícula ou a máscara de meio-tom.")

    def show_area(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento.")
            return
        node = document.activeNode()
        if node is None or node.type() != "filllayer":
            helpers.show_message("Selecione a camada de retícula para mostrar a área.")
            return
        for child in node.childNodes():
            if child.type() == "selectionmask" and child.selection() is not None:
                document.setSelection(child.selection())
                document.refreshProjection()
                helpers.show_message("Área da retícula carregada como seleção.")
                return
        helpers.show_message("A camada não tem máscara de seleção.")

    def insert_effect_lines(self):
        """Insere as linhas de efeito numa macro: um Ctrl+Z desfaz tudo."""
        document = helpers.active_document()
        helpers.run_in_macro(document, self._insert_effect_lines)

    def _insert_effect_lines(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para inserir as linhas.")
            return
        width = document.width()
        height = document.height()
        dpi = helpers.document_dpi(document)
        mode = self.cmb_effect.currentData()

        if mode == "focus":
            cx = width * self.spin_focus_x.value() / 100.0
            cy = height * self.spin_focus_y.value() / 100.0
            lines = effects.effect_lines_focus(
                width, height, cx, cy,
                count=self.spin_lines.value(),
                inset=self.spin_inset.value() / 100.0,
                thickness=self.spin_effect_thickness.value(),
            )
        else:
            x = width * self.spin_region_x.value() / 100.0
            y = height * self.spin_region_y.value() / 100.0
            w = width * self.spin_region_w.value() / 100.0
            h = height * self.spin_region_h.value() / 100.0
            lines = effects.effect_lines_parallel(
                width, height, x, y, w, h,
                spacing=self.spin_spacing.value(),
                angle_deg=self.spin_angle.value(),
                thickness=self.spin_effect_thickness.value(),
            )

        if not lines:
            helpers.show_message("Nenhuma linha gerada; ajuste os parâmetros.")
            return
        svg = effects.lines_to_svg(lines, width, height, dpi)
        name = helpers.unique_layer_name(document, "Linhas de efeito")
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message("Não foi possível criar a camada vetorial.")
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            helpers.show_message("Não foi possível gerar as formas das linhas.")
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message("{0} linhas inseridas.".format(len(lines)))

    # ------------------------------------------------------------------ presets

    def install_kit_patterns(self):
        """Instala os padrões e texturas do kit nos padrões do Krita."""
        import shutil

        from ...core.paths import KRITA_PATTERNS_DIR, PATTERNS_KIT_DIR

        if not os.path.isdir(PATTERNS_KIT_DIR):
            helpers.show_info("Padrões", "Pasta de padrões não encontrada no plugin.")
            return
        try:
            os.makedirs(KRITA_PATTERNS_DIR, exist_ok=True)
        except OSError as error:
            helpers.show_info("Padrões", "Falha ao criar a pasta: {0}".format(error))
            return
        instalados = 0
        for nome in sorted(os.listdir(PATTERNS_KIT_DIR)):
            if nome.lower().endswith(".png"):
                try:
                    shutil.copy2(
                        os.path.join(PATTERNS_KIT_DIR, nome),
                        os.path.join(KRITA_PATTERNS_DIR, nome),
                    )
                    instalados += 1
                except OSError:
                    continue
        self._reload_patterns()
        helpers.show_info(
            "Padrões",
            "{0} padrões instalados. Reinicie o Krita para usá-los no modo "
            "'tom com padrão' e nos pincéis.".format(instalados),
        )

    def _save_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(
            self.widget(), "Salvar preset", "Nome do preset:"
        )
        if not ok or not name.strip():
            return
        preset = self.current_preset()
        preset["name"] = name.strip()
        self.user_presets = [item for item in self.user_presets if item["name"] != preset["name"]]
        self.user_presets.append(preset)
        core.save_presets(USER_PRESETS_PATH, self.user_presets)
        self._reload_presets()
        helpers.show_message("Preset salvo: {0}".format(preset["name"]))

    def _delete_preset(self):
        preset = self.cmb_preset.currentData()
        if not preset:
            return
        if preset not in self.user_presets:
            helpers.show_message("Presets de fábrica não podem ser excluídos.")
            return
        answer = QtWidgets.QMessageBox.question(
            self.widget(),
            "Excluir preset",
            "Excluir o preset '{0}'?".format(preset["name"]),
            DIALOG_YES | DIALOG_NO,
        )
        if answer != DIALOG_YES:
            return
        self.user_presets = [item for item in self.user_presets if item["name"] != preset["name"]]
        core.save_presets(USER_PRESETS_PATH, self.user_presets)
        self._reload_presets()