"""Caminhos de dados do plugin (pasta do usuário e cache)."""

import os

HOME = os.path.expanduser("~")

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(PACKAGE_DIR, "modules")
RESOURCES_DIR = os.path.join(PACKAGE_DIR, "resources")
BRUSHES_KIT_DIR = os.path.join(RESOURCES_DIR, "brushes")
PATTERNS_KIT_DIR = os.path.join(RESOURCES_DIR, "patterns")
KRITA_PATTERNS_DIR = os.path.join(HOME, ".local", "share", "krita", "patterns")

USER_DIR = os.path.join(HOME, ".local", "share", "krita", "hq_tools")
CACHE_DIR = os.path.join(HOME, ".cache", "hq_tools")
BALLOONS_DIR = os.path.join(USER_DIR, "balloons")
ONOMATOPEIAS_DIR = os.path.join(USER_DIR, "onomatopeias")
BIBLIOTECA_DIR = os.path.join(USER_DIR, "biblioteca")
MODELOS_DIR = os.path.join(USER_DIR, "modelos")
VIEWER3D_MODELO = os.path.join(
    MODULES_DIR, "viewer3d", "modelos", "low_poly_krita.json"
)
ICONE_PATH = os.path.join(RESOURCES_DIR, "icon.png")
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
