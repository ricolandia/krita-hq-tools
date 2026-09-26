"""Registro de slots de pincel do módulo de pincéis."""

from .sets import SLOT_COUNT  # noqa: F401

_docker = None


def register_docker(docker):
    global _docker
    _docker = docker


def activate_slot(index):
    if _docker is not None:
        _docker.activate_slot(index)
        return
    _activate_without_docker(index)


def _activate_without_docker(index):
    """Ativa o preset do slot mesmo com o docker fechado (atalho direto)."""
    try:
        from krita import Krita

        from ...core import krita_helpers as helpers
        from ...core.config import Config

        slots = Config().get("brushes.slots", [""] * SLOT_COUNT) or []
        name = slots[index] if index < len(slots) else ""
        if not name:
            return
        view = helpers.active_view()
        if view is None:
            return
        resource = (Krita.instance().resources("preset") or {}).get(name)
        if resource is not None:
            view.activateResource(resource)
    except (ImportError, AttributeError, RuntimeError):
        pass