"""Registro de slots de pincel do módulo de pincéis."""

from .sets import SLOT_COUNT  # noqa: F401

_docker = None


def register_docker(docker):
    global _docker
    _docker = docker


def activate_slot(index):
    if _docker is not None:
        _docker.activate_slot(index)