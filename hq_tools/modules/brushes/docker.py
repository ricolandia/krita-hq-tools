"""Docker de pincéis: 12 slots com presets do próprio Krita e atalhos.

Os atalhos são registrados como ações do plugin (``hq_tools_brush_1`` a
``hq_tools_brush_12``) e aparecem em Configurar Krita > Atalhos, na categoria
Scripts > HQ Tools. Aqui o usuário escolhe qual preset instalado cada slot usa.
"""

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import QtWidgets
from ...core.config import Config
from . import SLOT_COUNT, register_docker

RECOMMENDED_HINTS = (
    ("Basic-5", "Basic-1", "Basic"),
    ("Eraser", "Borracha"),
    ("Ink", "Nanquim"),
    ("Pencil", "Lapis", "Lápis"),
    ("Airbrush", "Aerografo", "Aerógrafo"),
    ("Fill", "Preenchimento"),
    ("Blend", "Misturar"),
    ("Marker", "Marcador"),
    ("Watercolor", "Aquarela"),
    ("Chalk", "Giz"),
    ("Texture", "Textura"),
    ("Smudge", "Borrar"),
)


def pick_recommended(names):
    """Sugere presets instalados para os slots, a partir de nomes conhecidos."""
    slots = []
    used = set()
    for group in RECOMMENDED_HINTS:
        chosen = ""
        for hint in group:
            for name in names:
                if hint.lower() in name.lower() and name not in used:
                    chosen = name
                    break
            if chosen:
                break
        if chosen:
            used.add(chosen)
        slots.append(chosen)
    while len(slots) < SLOT_COUNT:
        slots.append("")
    return slots[:SLOT_COUNT]


class BrushesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: pincéis")
        self.config = Config()
        self.resources = {}
        self.rows = []
        self.slot_names = [""] * SLOT_COUNT
        register_docker(self)
        self._build_ui()
        self.reload_presets()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        group = widgets.QGroupBox("Slots de pincel")
        form = widgets.QFormLayout(group)
        for index in range(SLOT_COUNT):
            row = widgets.QHBoxLayout()
            combo = widgets.QComboBox()
            combo.currentIndexChanged.connect(
                lambda position, slot=index: self._on_combo_changed(slot)
            )
            row.addWidget(combo, 1)
            button = widgets.QPushButton("Usar")
            button.clicked.connect(
                lambda checked=False, slot=index: self.activate_slot(slot)
            )
            row.addWidget(button)
            form.addRow("{0}.".format(index + 1), row)
            self.rows.append(combo)
        layout.addWidget(group)

        buttons = widgets.QHBoxLayout()
        button_reload = widgets.QPushButton("Atualizar presets")
        button_reload.clicked.connect(self.reload_presets)
        buttons.addWidget(button_reload)
        button_suggest = widgets.QPushButton("Sugerir padrões")
        button_suggest.clicked.connect(self.apply_recommended)
        buttons.addWidget(button_suggest)
        layout.addLayout(buttons)

        hint = widgets.QLabel(
            "Configure os atalhos em Configurar Krita > Atalhos > Scripts > "
            "HQ Tools (HQ Tools: pincel 1 a 12)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch(1)
        self.setWidget(main)

    def reload_presets(self):
        self.resources = dict(Krita.instance().resources("preset") or {})
        names = sorted(self.resources.keys())
        stored = self.config.get("brushes.slots", [""] * SLOT_COUNT)
        if not isinstance(stored, list):
            stored = [""] * SLOT_COUNT
        while len(stored) < SLOT_COUNT:
            stored.append("")
        self.slot_names = [str(name or "") for name in stored[:SLOT_COUNT]]

        for index, combo in enumerate(self.rows):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("", "")
            for name in names:
                combo.addItem(name, name)
            current = self.slot_names[index]
            position = combo.findData(current)
            if position < 0 and current:
                combo.addItem("{0} (não encontrado)".format(current), current)
                position = combo.count() - 1
            combo.setCurrentIndex(max(0, position))
            combo.blockSignals(False)

    def _on_combo_changed(self, index):
        combo = self.rows[index]
        self.slot_names[index] = combo.currentData() or ""
        self.config.set("brushes.slots", list(self.slot_names))

    def apply_recommended(self):
        suggested = pick_recommended(sorted(self.resources.keys()))
        for index, name in enumerate(suggested):
            self.slot_names[index] = name
            combo = self.rows[index]
            combo.blockSignals(True)
            position = combo.findData(name)
            combo.setCurrentIndex(max(0, position))
            combo.blockSignals(False)
        self.config.set("brushes.slots", list(self.slot_names))
        helpers.show_message("Sugestão de pincéis aplicada aos slots.")

    def activate_slot(self, index):
        if index < 0 or index >= SLOT_COUNT:
            return
        name = self.slot_names[index]
        view = helpers.active_view()
        if view is None:
            helpers.show_message("Abra um documento para trocar de pincel.")
            return
        resource = self.resources.get(name)
        if resource is None:
            helpers.show_message("Escolha um preset no slot {0}.".format(index + 1))
            return
        view.activateResource(resource)
        helpers.show_message("Pincel {0}: {1}".format(index + 1, name))
