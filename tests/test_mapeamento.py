"""Testes da conversão widget -> pixels do documento (núcleo puro)."""

import unittest

from hq_tools.core import mapeamento


class TestWidgetParaImagem(unittest.TestCase):
    def test_sem_transformacao(self):
        ponto = mapeamento.widget_para_imagem(
            (150.0, 100.0), (100.0, 100.0), (500.0, 400.0), 1.0
        )
        self.assertAlmostEqual(ponto[0], 550.0, places=6)
        self.assertAlmostEqual(ponto[1], 400.0, places=6)

    def test_zoom_dois(self):
        ponto = mapeamento.widget_para_imagem(
            (120.0, 100.0), (100.0, 100.0), (500.0, 400.0), 2.0
        )
        self.assertAlmostEqual(ponto[0], 510.0, places=6)
        self.assertAlmostEqual(ponto[1], 400.0, places=6)

    def test_zoom_meio(self):
        ponto = mapeamento.widget_para_imagem(
            (120.0, 100.0), (100.0, 100.0), (500.0, 400.0), 0.5
        )
        self.assertAlmostEqual(ponto[0], 540.0, places=6)

    def test_pan(self):
        ponto = mapeamento.widget_para_imagem(
            (100.0, 100.0), (100.0, 100.0), (500.0, 400.0), 1.0,
            pan=(20.0, -10.0),
        )
        self.assertAlmostEqual(ponto[0], 480.0, places=6)
        self.assertAlmostEqual(ponto[1], 410.0, places=6)

    def test_espelhado(self):
        ponto = mapeamento.widget_para_imagem(
            (120.0, 100.0), (100.0, 100.0), (500.0, 400.0), 1.0, espelhado=True
        )
        self.assertAlmostEqual(ponto[0], 480.0, places=6)

    def test_rotacao_90(self):
        ponto = mapeamento.widget_para_imagem(
            (200.0, 100.0), (100.0, 100.0), (500.0, 400.0), 1.0, rotacao=90.0
        )
        self.assertAlmostEqual(ponto[0], 500.0, places=6)
        self.assertAlmostEqual(ponto[1], 300.0, places=6)


class TestIdaEVolta(unittest.TestCase):
    def test_ida_e_volta_sem_transformacao(self):
        widget = mapeamento.imagem_para_widget(
            (120.0, 80.0), (100.0, 100.0), (500.0, 400.0), 1.0
        )
        volta = mapeamento.widget_para_imagem(
            widget, (100.0, 100.0), (500.0, 400.0), 1.0
        )
        self.assertAlmostEqual(volta[0], 120.0, places=6)
        self.assertAlmostEqual(volta[1], 80.0, places=6)

    def test_ida_e_volta_com_zoom_pan_rotacao_espelho(self):
        argumentos = dict(zoom=2.5, rotacao=37.0, pan=(13.0, -7.0), espelhado=True)
        widget = mapeamento.imagem_para_widget(
            (700.0, 300.0), (400.0, 350.0), (500.0, 400.0), **argumentos
        )
        volta = mapeamento.widget_para_imagem(
            widget, (400.0, 350.0), (500.0, 400.0), **argumentos
        )
        self.assertAlmostEqual(volta[0], 700.0, places=6)
        self.assertAlmostEqual(volta[1], 300.0, places=6)

    def test_retangulo_para_widget(self):
        self.assertEqual(
            mapeamento.retangulo_para_widget(
                (450.0, 350.0, 100.0, 80.0), (100.0, 100.0), (500.0, 400.0), 1.0
            ),
            (50, 50, 100, 80),
        )


class TestDeslocamentoDaBarra(unittest.TestCase):
    def test_centrada_e_zero(self):
        self.assertEqual(mapeamento.deslocamento_da_barra(0, 100, 50), 0.0)

    def test_rolada_para_o_fim_e_negativa(self):
        self.assertEqual(mapeamento.deslocamento_da_barra(0, 100, 100), -50.0)

    def test_rolada_para_o_inicio_e_positiva(self):
        self.assertEqual(mapeamento.deslocamento_da_barra(0, 100, 0), 50.0)

    def test_sem_rolagem(self):
        self.assertEqual(mapeamento.deslocamento_da_barra(0, 0, 0), 0.0)


class TestRetanguloParaImagem(unittest.TestCase):
    def test_sem_rotacao(self):
        self.assertEqual(
            mapeamento.retangulo_para_imagem(
                (50.0, 50.0, 100.0, 80.0), (100.0, 100.0), (500.0, 400.0), 1.0
            ),
            (450, 350, 100, 80),
        )

    def test_com_zoom(self):
        self.assertEqual(
            mapeamento.retangulo_para_imagem(
                (50.0, 60.0, 100.0, 80.0), (100.0, 100.0), (500.0, 400.0), 2.0
            ),
            (475, 380, 50, 40),
        )

    def test_rotacao_90_troca_largura_e_altura(self):
        self.assertEqual(
            mapeamento.retangulo_para_imagem(
                (50.0, 50.0, 100.0, 80.0), (100.0, 100.0), (500.0, 400.0), 1.0,
                rotacao=90.0,
            ),
            (450, 350, 80, 100),
        )

    def test_intersecao(self):
        self.assertEqual(
            mapeamento.intersecao_com_documento((10, 20, 100, 80), 1000, 800),
            (10, 20, 100, 80),
        )
        self.assertEqual(
            mapeamento.intersecao_com_documento((-10, -20, 100, 80), 1000, 800),
            (0, 0, 90, 60),
        )
        self.assertEqual(
            mapeamento.intersecao_com_documento((990, 790, 100, 80), 1000, 800),
            (990, 790, 10, 10),
        )
        self.assertEqual(
            mapeamento.intersecao_com_documento((1100, 0, 50, 50), 1000, 800),
            (1100, 0, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
