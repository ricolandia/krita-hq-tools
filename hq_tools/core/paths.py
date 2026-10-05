"""Caminhos de dados do plugin (pasta do usuário e cache).

A pasta de recursos do Krita muda por sistema: ``%APPDATA%\\krita`` no Windows
(a mesma do ``pykrita``), ``~/Library/Application Support/krita`` no macOS e
``~/.local/share/krita`` no Linux (dentro do sandbox no Flatpak).
"""

import os
import sys

HOME = os.path.expanduser("~")


def _pasta_do_krita(plataforma=None, ambiente=None, home=None):
    """Pasta de dados do Krita por sistema.

    No Linux o ``XDG_DATA_HOME`` manda quando existe: é o que o Flatpak define
    (``~/.var/app/org.kde.krita/data``) e o que a tabela do ``INSTALL.md``
    promete. Sem a variável, segue ``~/.local/share/krita``.
    """
    plataforma = sys.platform if plataforma is None else plataforma
    ambiente = os.environ if ambiente is None else ambiente
    home = HOME if home is None else home
    if plataforma.startswith("win"):
        base = ambiente.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(base, "krita")
    if plataforma == "darwin":
        return os.path.join(home, "Library", "Application Support", "krita")
    dados = ambiente.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(dados, "krita")


def _pasta_de_cache(plataforma=None, ambiente=None, home=None):
    plataforma = sys.platform if plataforma is None else plataforma
    ambiente = os.environ if ambiente is None else ambiente
    home = HOME if home is None else home
    if plataforma.startswith("win"):
        base = ambiente.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        return os.path.join(base, "hq_tools", "cache")
    if plataforma == "darwin":
        return os.path.join(home, "Library", "Caches", "hq_tools")
    cache = ambiente.get("XDG_CACHE_HOME") or os.path.join(home, ".cache")
    return os.path.join(cache, "hq_tools")


def _pasta_de_fontes():
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(HOME, "AppData", "Local")
        return os.path.join(base, "Microsoft", "Windows", "Fonts")
    if sys.platform == "darwin":
        return os.path.join(HOME, "Library", "Fonts")
    return os.path.join(HOME, ".local", "share", "fonts")


KRITA_HOME = _pasta_do_krita()
FONTS_DIR = _pasta_de_fontes()
if sys.platform.startswith("win") or sys.platform == "darwin":
    FONTS_TARGET = FONTS_DIR
else:
    FONTS_TARGET = os.path.join(FONTS_DIR, "hq_tools")

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(PACKAGE_DIR, "modules")
RESOURCES_DIR = os.path.join(PACKAGE_DIR, "resources")
BRUSHES_KIT_DIR = os.path.join(RESOURCES_DIR, "brushes")
PATTERNS_KIT_DIR = os.path.join(RESOURCES_DIR, "patterns")
KRITA_PATTERNS_DIR = os.path.join(KRITA_HOME, "patterns")

USER_DIR = os.path.join(KRITA_HOME, "hq_tools")
CACHE_DIR = _pasta_de_cache()
BALLOONS_DIR = os.path.join(USER_DIR, "balloons")
ONOMATOPEIAS_DIR = os.path.join(USER_DIR, "onomatopeias")
BIBLIOTECA_DIR = os.path.join(USER_DIR, "biblioteca")
MODELOS_DIR = os.path.join(USER_DIR, "modelos")
VIEWER3D_DIR = os.path.join(MODULES_DIR, "viewer3d")
VIEWER3D_MODELOS = (
    ("homem", "Homem", os.path.join(VIEWER3D_DIR, "modelos", "homem.json")),
    ("mulher", "Mulher", os.path.join(VIEWER3D_DIR, "modelos", "mulher.json")),
)
VIEWER3D_POSES_DIR = os.path.join(VIEWER3D_DIR, "poses")
VIEWER3D_POSE_PADRAO = "idle_maos_fechadas.json"
ICONE_PATH = os.path.join(RESOURCES_DIR, "icon.png")
KRITA_PALETTES_DIR = os.path.join(KRITA_HOME, "palettes")
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


def mesma_copia(origem, destino):
    """Diz se o destino já é esta mesma cópia do arquivo.

    Mesmo tamanho e mtime. Serve para as instalações repetidas: recopiar o kit
    inteiro a cada clique não instala nada novo e obriga a refazer o cache do
    sistema (no caso das fontes, o ``fc-cache`` leva segundos com a interface
    travada). O mtime só é confiável porque quem copia é o ``shutil.copy2``,
    que preserva os metadados.
    """
    try:
        info_origem = os.stat(origem)
        info_destino = os.stat(destino)
    except OSError:
        return False
    return (
        info_origem.st_size == info_destino.st_size
        and int(info_origem.st_mtime) == int(info_destino.st_mtime)
    )
