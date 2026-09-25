"""Testes de paletas GPL (rodam fora do Krita)."""

import os
import tempfile
import unittest

from hq_tools.core import gpl

TEMPLATES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "hq_tools",
    "modules",
    "palettes",
    "templates",
)


class TestGpl(unittest.TestCase):
    def test_parse_template(self):
        palette = gpl.load_gpl(os.path.join(TEMPLATES, "tons-hq.gpl"))
        self.assertEqual(palette["name"], "HQ Tons")
        self.assertGreaterEqual(len(palette["colors"]), 10)
        self.assertEqual(palette["colors"][0]["rgb"], (255, 255, 255))
        self.assertEqual(palette["colors"][-1]["rgb"], (0, 0, 0))

    def test_todos_os_templates(self):
        names = [name for name in os.listdir(TEMPLATES) if name.endswith(".gpl")]
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            palette = gpl.load_gpl(os.path.join(TEMPLATES, name))
            self.assertTrue(palette["colors"], name)

    def test_round_trip(self):
        palette = {
            "name": "Teste",
            "columns": 3,
            "colors": [
                {"rgb": (0, 0, 0), "name": "Preto"},
                {"rgb": (255, 255, 255), "name": "Branco"},
            ],
        }
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "teste.gpl")
            gpl.save_gpl(path, palette)
            reloaded = gpl.load_gpl(path)
        self.assertEqual(reloaded["name"], "Teste")
        self.assertEqual(reloaded["colors"][0]["rgb"], (0, 0, 0))
        self.assertEqual(reloaded["colors"][1]["name"], "Branco")

    def test_arquivo_invalido(self):
        with self.assertRaises(ValueError):
            gpl.parse_gpl("não é uma paleta")


if __name__ == "__main__":
    unittest.main()
