"""Caminhos de dados do plugin (pasta do usuário e cache)."""

import os

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(PACKAGE_DIR, "modules")
RESOURCES_DIR = os.path.join(PACKAGE_DIR, "resources")
BRUSHES_KIT_DIR = os.path.join(RESOURCES_DIR, "brushes")
PATTERNS_KIT_DIR = os.path.join(RESOURCES_DIR, "patterns")
KRITA_PATTERNS_DIR = os.path.join(HOME, ".local", "share", "krita", "patterns")

HOME = os.path.expanduser("~")
USER_DIR = os.path.join(HOME, ".local", "share", "krita", "hq_tools")
CACHE_DIR = os.path.join(HOME, ".cache", "hq_tools")
BALLOONS_DIR = os.path.join(USER_DIR, "balloons")
ONOMATOPEIAS_DIR = os.path.join(USER_DIR, "onomatopeias")
BIBLIOTECA_DIR = os.path.join(USER_DIR, "biblioteca")
MODELOS_DIR = os.path.join(USER_DIR, "modelos")
KRITA_PALETTES_DIR = os.path.join(HOME, ".local", "share", "krita", "palettes")
CONFIG_PATH = os.path.join(USER_DIR, "config.json")


def ensure_user_dirs():
    """Garante que as pastas de dados do usuário existam."""
    for path in (
        USER_DIR,
        CACHE_DIR,
        BALLOONS_DIR,
        ONOMATOPEIAS_DIR,
        BIBLIOTECA_DIR,
        MODELOS_DIR,
    ):
        os.makedirs(path, exist_ok=True)


def module_dir(*parts):
    """Retorna um caminho dentro da pasta ``modules`` do plugin."""
    return os.path.join(MODULES_DIR, *parts)
