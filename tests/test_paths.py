"""Testes dos caminhos do plugin (fora do Krita)."""

import os
import shutil
import tempfile
import unittest

from hq_tools.core import paths
from hq_tools.core.paths import mesma_copia


class TestPaths(unittest.TestCase):
    def test_home_definido(self):
        self.assertEqual(paths.HOME, os.path.expanduser("~"))

    def test_pastas_de_recursos(self):
        self.assertTrue(paths.PACKAGE_DIR.endswith("hq_tools"))
        self.assertTrue(paths.RESOURCES_DIR.endswith("resources"))
        self.assertTrue(paths.BRUSHES_KIT_DIR.endswith("brushes"))
        self.assertTrue(paths.PATTERNS_KIT_DIR.endswith("patterns"))
        self.assertTrue(paths.KRITA_PATTERNS_DIR.endswith("patterns"))
        self.assertTrue(paths.KRITA_PALETTES_DIR.endswith("palettes"))
        self.assertTrue(paths.VIEWER3D_POSES_CORPO_DIR.endswith("corpo"))
        self.assertTrue(paths.VIEWER3D_POSES_MAOS_DIR.endswith("maos"))

    def test_pastas_do_usuario(self):
        self.assertTrue(paths.KRITA_HOME.endswith("krita"))
        self.assertTrue(
            paths.USER_DIR.endswith(os.path.join("krita", "hq_tools"))
        )
        self.assertTrue(paths.MODELOS_DIR.endswith("modelos"))
        self.assertTrue(paths.BIBLIOTECA_DIR.endswith("biblioteca"))

    def test_pasta_de_fontes(self):
        self.assertTrue(paths.FONTS_TARGET.startswith(paths.FONTS_DIR))


if __name__ == "__main__":
    unittest.main()

class TestMesmaCopia(unittest.TestCase):
    """A cópia de fontes e de packs não pode ser refeita à toa."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="hq_tools_paths_")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.origem = os.path.join(self.pasta, "fonte.ttf")
        self.destino = os.path.join(self.pasta, "instalada.ttf")
        with open(self.origem, "wb") as handle:
            handle.write(b"conteudo da fonte")

    def copiar(self):
        shutil.copy2(self.origem, self.destino)

    def test_destino_ausente_nao_e_igual(self):
        self.assertFalse(mesma_copia(self.origem, self.destino))

    def test_origem_ausente_nao_e_igual(self):
        self.copiar()
        self.assertFalse(mesma_copia(os.path.join(self.pasta, "nada.ttf"), self.destino))

    def test_copia_recem_feita_e_a_mesma(self):
        self.copiar()
        self.assertTrue(mesma_copia(self.origem, self.destino))

    def test_conteudo_diferente_no_mesmo_tamanho(self):
        # Mesmo nome, mesmo tamanho, mtime mexido na mão: tem que instalar de
        # novo, senão a fonte nova nunca chega ao sistema.
        self.copiar()
        with open(self.destino, "wb") as handle:
            handle.write(b"outro conteu")
        os.utime(self.destino, (0, 0))
        self.assertFalse(mesma_copia(self.origem, self.destino))

    def test_arquivo_zerado_e_diferente(self):
        self.copiar()
        with open(self.destino, "wb") as handle:
            handle.write(b"")
        os.utime(self.destino, (0, 0))
        self.assertFalse(mesma_copia(self.origem, self.destino))


class TestPastasPorSistema(unittest.TestCase):
    """No Linux o XDG manda: é o que o Flatpak define (tabela do INSTALL.md)."""

    def test_linux_sem_xdg(self):
        self.assertEqual(
            paths._pasta_do_krita("linux", {}, "/home/x"),
            os.path.join("/home/x", ".local", "share", "krita"),
        )

    def test_linux_com_xdg_data(self):
        ambiente = {"XDG_DATA_HOME": "/home/x/.var/app/org.kde.krita/data"}
        self.assertEqual(
            paths._pasta_do_krita("linux", ambiente, "/home/x"),
            os.path.join(ambiente["XDG_DATA_HOME"], "krita"),
        )

    def test_linux_cache_com_xdg(self):
        ambiente = {"XDG_CACHE_HOME": "/home/x/.var/app/org.kde.krita/cache"}
        self.assertEqual(
            paths._pasta_de_cache("linux", ambiente, "/home/x"),
            os.path.join(ambiente["XDG_CACHE_HOME"], "hq_tools"),
        )

    def test_linux_cache_sem_xdg(self):
        self.assertEqual(
            paths._pasta_de_cache("linux", {}, "/home/x"),
            os.path.join("/home/x", ".cache", "hq_tools"),
        )

    def test_windows_usa_appdata(self):
        ambiente = {"APPDATA": os.path.join("C:", "Users", "x", "AppData", "Roaming")}
        self.assertEqual(
            paths._pasta_do_krita("win32", ambiente, os.path.join("C:", "Users", "x")),
            os.path.join(ambiente["APPDATA"], "krita"),
        )

    def test_macos(self):
        self.assertEqual(
            paths._pasta_do_krita("darwin", {}, "/Users/x"),
            os.path.join("/Users/x", "Library", "Application Support", "krita"),
        )
