"""Configuração persistente do plugin em JSON.

O arquivo fica em ``~/.local/share/krita/hq_tools/config.json`` e guarda os
módulos habilitados, presets do usuário, pastas e preferências de interface.
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import time

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
        "model": "",
        "use_model": False,
        "strip_panels": 3,
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
        except FileNotFoundError:
            self.data = copy.deepcopy(DEFAULT_CONFIG)
        except (OSError, ValueError):
            # Arquivo ilegível ou JSON inválido: guarda uma cópia antes de
            # voltar ao padrão, porque o próximo `set()` sobrescreve o
            # arquivo e o usuário perderia a configuração sem ter como recuperar.
            self._preservar_ilegivel()
            self.data = copy.deepcopy(DEFAULT_CONFIG)

    def _preservar_ilegivel(self):
        try:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            backup = "{0}.ilegivel-{1}".format(self.path, stamp)
            shutil.copy2(self.path, backup)
            sys.stderr.write(
                "[hq_tools] config.json ilegível; cópia em {0}\n".format(backup)
            )
        except OSError:
            pass

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

    def get_int(self, key_path, default=0):
        """Lê um inteiro, ignorando valor corrompido.

        Usado nos widgets, que chamam ``int()`` direto: uma string ou um
        ``null`` deixado no JSON derrubava a construção do docker inteiro.
        """
        try:
            return int(self.get(key_path, default))
        except (TypeError, ValueError):
            return default

    def get_float(self, key_path, default=0.0):
        """Lê um float, ignorando valor corrompido."""
        try:
            return float(self.get(key_path, default))
        except (TypeError, ValueError):
            return default

    def _resolve_container(self, keys, create=True):
        """Desce pelo caminho devolvendo ``(pai, última_chave)``.

        Nível intermediário que não é dicionário é considerado arquivo
        corrompido: antes ele era sobrescrito por ``{}`` sem aviso, o que
        apagava de uma vez uma lista inteira (os slots de pincel, por exemplo)
        por causa de um erro de digitação no caminho.
        """
        node = self.data
        for key in keys[:-1]:
            child = node.get(key)
            if child is None:
                if not create:
                    return None, keys[-1]
                child = {}
                node[key] = child
            elif not isinstance(child, dict):
                raise TypeError(
                    "'{0}' não é um grupo de configuração (é {1}). Use um "
                    "caminho existente em vez de sobrescrever.".format(
                        key, type(child).__name__
                    )
                )
            node = child
        return node, keys[-1]

    def set(self, key_path, value, save=True):
        """Grava um valor usando caminho com pontos.

        Rele o arquivo antes de escrever: cada docker tem a sua instância de
        :class:`Config` e elas ficam abertas horas a fio. Sem a releitura, a
        última escrita apagava o que os outros módulos gravaram no intervalo
        (mudar o preset de retícula apagava os slots de pincel, por exemplo).
        """
        keys = key_path.split(".")
        if save:
            self.load()
        node, last = self._resolve_container(keys)
        node[last] = value
        if save:
            self.save()
        return value
