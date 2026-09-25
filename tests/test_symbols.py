"""Testes da extração de símbolos das bibliotecas do Krita (fora do Krita)."""

import unittest

from hq_tools.modules.balloons import symbols as symbols_lib

LIBRARY = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000"/>
      <stop offset="1" stop-color="#fff"/>
    </linearGradient>
  </defs>
  <symbol id="RoundedBalloon">
    <title>Balão redondo</title>
    <path d="M 10 10 L 90 10 L 90 60 L 10 60 Z" fill="#ffffff" stroke="#000000"/>
  </symbol>
  <g id="speech_balloon_1">
    <ellipse cx="50" cy="50" rx="40" ry="30" fill="#ffffff" stroke="#000000"/>
  </g>
  <g id="speech_balloon_1_transform">
    <ellipse cx="50" cy="50" rx="40" ry="30" fill="#cccccc"/>
  </g>
</svg>
"""


class TestSymbols(unittest.TestCase):
    def test_list_symbols(self):
        items = symbols_lib.list_symbols(LIBRARY)
        ids = [item["id"] for item in items]
        self.assertIn("RoundedBalloon", ids)
        self.assertIn("speech_balloon_1", ids)
        self.assertNotIn("speech_balloon_1_transform", ids)
        balloon = next(item for item in items if item["id"] == "RoundedBalloon")
        self.assertEqual(balloon["title"], "Balão redondo")
        self.assertEqual(balloon["kind"], "symbol")

    def test_extract_symbol(self):
        svg = symbols_lib.extract_symbol_svg(LIBRARY, "RoundedBalloon")
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertIn('<linearGradient', svg)
        self.assertIn('id="RoundedBalloon"', svg)
        self.assertIn('<path', svg)

    def test_extract_group(self):
        svg = symbols_lib.extract_symbol_svg(LIBRARY, "speech_balloon_1")
        self.assertIn('<ellipse', svg)
        self.assertNotIn('speech_balloon_1_transform', svg)

    def test_extract_desconhecido(self):
        with self.assertRaises(ValueError):
            symbols_lib.extract_symbol_svg(LIBRARY, "nao-existe")

    def test_lista_libraries_sem_pasta(self):
        libraries = symbols_lib.list_libraries(folder="/caminho/inexistente/xyz")
        self.assertEqual(libraries, {})


if __name__ == "__main__":
    unittest.main()