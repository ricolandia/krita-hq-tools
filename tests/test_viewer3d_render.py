"""Testes da resolução do preview do 3D (puro, sem Krita)."""

import unittest

from hq_tools.modules.viewer3d.render import LIMITE_PARADO, resolucao_do_render


class TestResolucaoDoRender(unittest.TestCase):
    def test_pequeno_nao_reduz(self):
        self.assertEqual((300, 200), resolucao_do_render(300, 200))

    def test_limita_o_maior_lado(self):
        self.assertEqual((LIMITE_PARADO, 540), resolucao_do_render(1200, 900))

    def test_quadrado(self):
        self.assertEqual((720, 720), resolucao_do_render(1000, 1000))

    def test_retrato(self):
        self.assertEqual((360, 720), resolucao_do_render(600, 1200))

    def test_no_limite_nao_reduz(self):
        self.assertEqual((720, 480), resolucao_do_render(720, 480))

    def test_proporcao_preservada(self):
        largura, altura = resolucao_do_render(1600, 900)
        self.assertAlmostEqual(largura / altura, 1600 / 900, places=2)

    def test_limite_customizado(self):
        self.assertEqual((360, 270), resolucao_do_render(1200, 900, limite=360))

    def test_dimensao_invalida_vira_um(self):
        self.assertEqual((1, 1), resolucao_do_render(0, -10))


if __name__ == "__main__":
    unittest.main()
