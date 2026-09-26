"""Testes dos caminhos do plugin (fora do Krita)."""

import os
import unittest

from hq_tools.core import paths


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

    def test_pastas_do_usuario(self):
        self.assertTrue(paths.USER_DIR.endswith("krita/hq_tools"))
        self.assertTrue(paths.MODELOS_DIR.endswith("modelos"))
        self.assertTrue(paths.BIBLIOTECA_DIR.endswith("biblioteca"))


if __name__ == "__main__":
    unittest.main()