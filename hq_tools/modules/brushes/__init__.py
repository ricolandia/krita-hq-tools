"""Registro de slots de pincel do módulo de pincéis."""

from .sets import SLOT_COUNT  # noqa: F401

_docker = None


def register_docker(docker):
    global _docker
    _docker = docker


def current_docker():
    """Devolve o docker registrado, descartando ponteiro para objeto morto.

    Fechar o docker pelo "x" da janela destrói o objeto C++ mas deixa o
    wrapper Python vivo. Chamar um método nesse wrapper levanta ``RuntimeError``
    e derrubava o atalho de slot, que é justamente o atalho que sobrevive ao
    fechamento do docker. O acesso é testado uma vez e o ponteiro é limpo.
    """
    docker = _docker
    if docker is None:
        return None
    try:
        docker.activate_slot
    except RuntimeError:
        register_docker(None)
        return None
    return docker


def activate_slot(index):
    docker = current_docker()
    if docker is not None:
        docker.activate_slot(index)
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