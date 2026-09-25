"""Testes das linhas de efeito e velocidade (fora do Krita)."""

import unittest

from hq_tools.modules.screentone import effects


class TestEffectLines(unittest.TestCase):
    def test_focus_conta_e_geometria(self):
        lines = effects.effect_lines_focus(1000, 800, 500, 400, count=8, inset=0.1)
        self.assertEqual(len(lines), 8)
        radius = (1000 ** 2 + 800 ** 2) ** 0.5 * 1.15 / 2.0
        for line in lines:
            self.assertAlmostEqual(line["width"], 2.0, delta=0.4)
            dx1 = line["x1"] - 500
            dy1 = line["y1"] - 400
            dx2 = line["x2"] - 500
            dy2 = line["y2"] - 400
            cross = dx1 * dy2 - dy1 * dx2
            self.assertAlmostEqual(cross, 0.0, delta=0.001)
            self.assertLessEqual(abs(line["x2"] - 500), radius + 0.01)
            self.assertLessEqual(abs(line["y2"] - 400), radius + 0.01)

    def test_focus_inset_zero_passa_pelo_centro(self):
        lines = effects.effect_lines_focus(1000, 800, 100, 100, count=4, inset=0.0)
        for line in lines:
            self.assertAlmostEqual(line["x1"], 100, delta=0.001)
            self.assertAlmostEqual(line["y1"], 100, delta=0.001)

    def test_parallel_dentro_da_regiao(self):
        lines = effects.effect_lines_parallel(1000, 800, 100, 100, 400, 300,
                                              spacing=50, angle_deg=0)
        self.assertGreater(len(lines), 4)
        for line in lines:
            self.assertGreaterEqual(min(line["x1"], line["x2"]), 99.0)
            self.assertLessEqual(max(line["x1"], line["x2"]), 501.0)
            self.assertGreaterEqual(min(line["y1"], line["y2"]), 99.0)
            self.assertLessEqual(max(line["y1"], line["y2"]), 401.0)

    def test_parallel_vertical(self):
        lines = effects.effect_lines_parallel(1000, 800, 0, 0, 1000, 800,
                                              spacing=100, angle_deg=90)
        self.assertGreater(len(lines), 4)
        for line in lines:
            self.assertAlmostEqual(line["x1"], line["x2"], delta=0.001)

    def test_lines_to_svg(self):
        lines = effects.effect_lines_focus(1000, 800, 500, 400, count=3)
        svg = effects.lines_to_svg(lines, 1000, 800, 300)
        self.assertIn("<svg", svg)
        self.assertIn("<line", svg)
        self.assertEqual(svg.count("<line"), 3)


if __name__ == "__main__":
    unittest.main()