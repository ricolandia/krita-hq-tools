"""Registro do plugin HQ Tools no Krita.

Cada módulo (retículas, balões, paletas, páginas, pincéis) registra o seu
docker aqui, conforme a configuração salva em ``~/.local/share/krita/hq_tools``.
"""

from krita import DockWidgetFactory, DockWidgetFactoryBase, Extension, Krita

from .core.config import Config
from .modules import brushes


class HQTools(Extension):
    """Extensão principal: registra os módulos habilitados e as ações de pincel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.config = Config()

    def setup(self):
        instance = Krita.instance()
        modules = self.config.get("modules", {}) or {}

        if modules.get("screentone", True):
            from .modules.screentone.docker import ScreentoneDocker

            instance.addDockWidgetFactory(
                DockWidgetFactory(
                    "hq_tools_screentone",
                    DockWidgetFactoryBase.DockRight,
                    ScreentoneDocker,
                )
            )

        if modules.get("balloons", True):
            from .modules.balloons.docker import BalloonsDocker

            instance.addDockWidgetFactory(
                DockWidgetFactory(
                    "hq_tools_balloons",
                    DockWidgetFactoryBase.DockRight,
                    BalloonsDocker,
                )
            )

        if modules.get("palettes", True):
            from .modules.palettes.docker import PalettesDocker

            instance.addDockWidgetFactory(
                DockWidgetFactory(
                    "hq_tools_palettes",
                    DockWidgetFactoryBase.DockRight,
                    PalettesDocker,
                )
            )

        if modules.get("pages", True):
            from .modules.pages.manager_docker import PagesDocker

            instance.addDockWidgetFactory(
                DockWidgetFactory(
                    "hq_tools_pages",
                    DockWidgetFactoryBase.DockRight,
                    PagesDocker,
                )
            )

        if modules.get("brushes", True):
            from .modules.brushes.docker import BrushesDocker

            instance.addDockWidgetFactory(
                DockWidgetFactory(
                    "hq_tools_brushes",
                    DockWidgetFactoryBase.DockRight,
                    BrushesDocker,
                )
            )

    def createActions(self, window):
        modules = self.config.get("modules", {}) or {}
        if not modules.get("brushes", True):
            return
        for index in range(brushes.SLOT_COUNT):
            action = window.createAction(
                "hq_tools_brush_{0}".format(index + 1),
                "HQ Tools: pincel {0}".format(index + 1),
                "tools/scripts/hq_tools",
            )
            action.triggered.connect(
                lambda checked=False, slot=index: brushes.activate_slot(slot)
            )


Krita.instance().addExtension(HQTools(Krita.instance()))
