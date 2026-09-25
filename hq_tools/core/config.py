"""Configuração persistente do plugin em JSON.

O arquivo fica em ``~/.local/share/krita/hq_tools/config.json`` e guarda os
módulos habilitados, presets do usuário, pastas e preferências de interface.
"""

import copy
import json
import os
import tempfile

from .paths import CONFIG_PATH, ensure_user_dirs

DEFAULT_CONFIG = {
    "modules": {
        "screentone": True,
        "balloons": True,
        "onomatopeias": True,
        "palettes": True,
        "pages": True,
        "brushes": True,
        "biblioteca": True,
    },
    "screentone": {
        "last_preset": "Sombra média 60 LPI",
        "user_presets": [],
    },
    "balloons": {
        "folder": "",
        "insert_as_text_layer": False,
    },
    "onomatopeias": {
        "folder": "",
    },
    "biblioteca": {
        "folder": "",
    },
    "palettes": {
        "last_template": "tons-hq",
    },
    "pages": {
        "last_project": "",
        "last_folder": "",
        "format": "A4",
        "dpi": 300,
    },
    "brushes": {
        "slots": [""] * 16,
    },
}


def _deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Config:
    """Leitura e escrita tolerante a falhas da configuração do plugin."""

    def __init__(self, path=None):
        self.path = path or CONFIG_PATH
        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self):
        try:
            ensure_user_dirs()
            with open(self.path, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
            if isinstance(stored, dict):
                self.data = _deep_merge(DEFAULT_CONFIG, stored)
        except (OSError, ValueError):
            self.data = copy.deepcopy(DEFAULT_CONFIG)

    def save(self):
        ensure_user_dirs()
        directory = os.path.dirname(self.path)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=directory, delete=False
        )
        try:
            with handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)
            os.replace(handle.name, self.path)
        except OSError:
            try:
                os.unlink(handle.name)
            except OSError:
                pass

    def get(self, key_path, default=None):
        """Lê um valor usando caminho com pontos, ex.: ``screentone.last_preset``."""
        node = self.data
        for key in key_path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, key_path, value, save=True):
        """Grava um valor usando caminho com pontos."""
        keys = key_path.split(".")
        node = self.data
        for key in keys[:-1]:
            if not isinstance(node.get(key), dict):
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value
        if save:
            self.save()
        return value
