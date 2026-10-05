"""Testes das linhas de efeito e velocidade (fora do Krita)."""

import unittest

from hq_tools.modules.screentone import effects


class TestEffectLines(unittest.TestCase):
    def test_focus_conta_e_geometria(self):
        lines = effects.effect_lines_focus(1000, 800, 500, 400, count=8, inset=0.1)
        self.assertEqual(len(lines), 8)
        # O raio tem de alcançar o canto mais distante do foco, senão as linhas
        # saem do quadro antes da borda (era metade da diagonal,independente
        # de onde o foco estivesse).
        raio = effects.focus_radius(1000, 800, 500, 400)
        canto = max(
            ((x - 500) ** 2 + (y - 400) ** 2) ** 0.5
            for x in (0, 1000)
            for y in (0, 800)
        )
        self.assertGreaterEqual(raio, canto)
        for line in lines:
            self.assertAlmostEqual(line["width"], 2.0, delta=0.4)
            dx1 = line["x1"] - 500
            dy1 = line["y1"] - 400
            dx2 = line["x2"] - 500
            dy2 = line["y2"] - 400
            cross = dx1 * dy2 - dy1 * dx2
            self.assertAlmostEqual(cross, 0.0, delta=0.001)
            self.assertAlmostEqual((dx2 ** 2 + dy2 ** 2) ** 0.5, raio, delta=0.01)

    def test_foco_deslocado_cobre_o_quadro(self):
        # Foco no canto inferior direito: o raio da diagonal antiga deixava o
        # facho cortado no lado esquerdo.
        cx, cy = 900.0, 700.0
        raio = effects.focus_radius(1000, 800, cx, cy)
        linhas = effects.effect_lines_focus(1000, 800, cx, cy, count=16, inset=0.0)
        # A ponta final de cada linha tem de sair do quadro (a inicial é o
        # próprio foco, que fica dentro dele por definição).
        for line in linhas:
            x, y = line["x2"], line["y2"]
            fora = x <= 0 or x >= 1000 or y <= 0 or y >= 800
            self.assertTrue(
                fora, "linha termina dentro do quadro: {0},{1}".format(x, y)
            )
        self.assertGreater(raio, 1200.0 * 0.9)

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

    def test_recortar_segmentos_ao_retangulo(self):
        # Diagonal cruzando o retângulo: fica só o trecho de dentro.
        linhas = [{"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0, "width": 2.0}]
        recortadas = effects.recortar_segmentos(linhas, 25.0, 25.0, 50.0, 50.0)
        self.assertEqual(len(recortadas), 1)
        self.assertAlmostEqual(recortadas[0]["x1"], 25.0, places=3)
        self.assertAlmostEqual(recortadas[0]["y1"], 25.0, places=3)
        self.assertAlmostEqual(recortadas[0]["x2"], 75.0, places=3)
        self.assertAlmostEqual(recortadas[0]["y2"], 75.0, places=3)
        self.assertEqual(recortadas[0]["width"], 2.0)

    def test_recortar_segmentos_fora_some(self):
        linhas = [{"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 10.0, "width": 1.0}]
        self.assertEqual(
            effects.recortar_segmentos(linhas, 50.0, 50.0, 20.0, 20.0), []
        )

    def test_recortar_paralelas_nao_muda(self):
        # As paralelas já nascem dentro da região; recortar mantém todas.
        linhas = effects.effect_lines_parallel(
            1000, 800, 100, 100, 400, 300, spacing=40, angle_deg=0
        )
        recortadas = effects.recortar_segmentos(linhas, 100, 100, 400, 300)
        self.assertEqual(len(recortadas), len(linhas))


if __name__ == "__main__":
    unittest.main()