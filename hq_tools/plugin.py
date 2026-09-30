"""Registro do plugin HQ Tools no Krita.

Cada módulo (retículas, balões, paletas, páginas, pincéis) registra o seu
docker aqui, conforme a configuração salva em ``~/.local/share/krita/hq_tools``.
"""

from krita import DockWidgetFactory, DockWidgetFactoryBase, Extension, Krita

from .core.config import Config
from .core.krita_helpers import log

# (chave do módulo, id do docker, classe, caminho de import relativo a hq_tools)
# A lista fica num lugar só para que o registro e a ação de pincel não
# dependam de sete blocos de código repetidos.
MODULOS = (
    (
        "screentone",
        "hq_tools_screentone",
        "ScreentoneDocker",
        "modules.screentone.docker",
    ),
    ("balloons", "hq_tools_balloons", "BalloonsDocker", "modules.balloons.docker"),
    (
        "onomatopeias",
        "hq_tools_onomatopeias",
        "OnomatopoeiasDocker",
        "modules.onomatopeias.docker",
    ),
    (
        "palettes",
        "hq_tools_palettes",
        "PalettesDocker",
        "modules.palettes.docker",
    ),
    ("pages", "hq_tools_pages", "PagesDocker", "modules.pages.manager_docker"),
    (
        "biblioteca",
        "hq_tools_biblioteca",
        "BibliotecaDocker",
        "modules.biblioteca.docker",
    ),
    ("brushes", "hq_tools_brushes", "BrushesDocker", "modules.brushes.docker"),
)


def _importar_classe(caminho, nome):
    """Importa ``nome`` do módulo relativo indicado, com erro claros."""
    from importlib import import_module

    modulo = import_module("." + caminho, __package__)
    return getattr(modulo, nome)


class HQTools(Extension):
    """Extensão principal: registra os módulos habilitados e as ações de pincel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.config = Config()
        self.modulos_com_erro = []

    def setup(self):
        instance = Krita.instance()
        modules = self.config.get("modules", {}) or {}
        self.modulos_com_erro = []
        for chave, dock_id, classe, caminho in MODULOS:
            if not modules.get(chave, True):
                continue
            try:
                tipo_docker = _importar_classe(caminho, classe)
            except (ImportError, AttributeError, RuntimeError) as error:
                # Um módulo quebrado não pode derrubar os outros seis: o autor
                # perdia o plugin inteiro por causa de um erro de import num
                # arquivo só dele, sem nenhuma pista do que aconteceu.
                self.modulos_com_erro.append((chave, str(error)))
                log("módulo {0} não registrado: {1}".format(chave, error))
                continue
            try:
                instance.addDockWidgetFactory(
                    DockWidgetFactory(
                        dock_id,
                        DockWidgetFactoryBase.DockRight,
                        tipo_docker,
                    )
                )
            except (RuntimeError, TypeError) as error:
                self.modulos_com_erro.append((chave, str(error)))
                log("módulo {0} não registrado: {1}".format(chave, error))

    def createActions(self, window):
        modules = self.config.get("modules", {}) or {}
        if not modules.get("brushes", True):
            return
        # Importado aqui, não no topo: ``brushes`` é o único módulo que os
        # atalhos precisam, e um erro de import nele derrubava o registro dos
        # outros seis na versão anterior.
        try:
            from .modules import brushes
        except (ImportError, AttributeError, RuntimeError) as error:
            log("atalhos não criados: {0}".format(error))
            return
        for index in range(brushes.SLOT_COUNT):
            try:
                action = window.createAction(
                    "hq_tools_brush_{0}".format(index + 1),
                    "HQ Tools: pincel {0}".format(index + 1),
                    "tools/scripts/hq_tools",
                )
                action.triggered.connect(
                    lambda checked=False, slot=index: brushes.activate_slot(slot)
                )
            except (AttributeError, RuntimeError) as error:
                log("atalho do slot {0} não criado: {1}".format(index + 1, error))
                return


Krita.instance().addExtension(HQTools(Krita.instance()))
