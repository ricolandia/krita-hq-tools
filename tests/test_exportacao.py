"""Testes do núcleo da exportação de páginas (``pages.exportacao``).

O plano é puro: nome do arquivo, atalho do ``mergedimage`` na resolução
nativa, dimensões da cópia reamostrada e o preparo do destino. O export em si
(``exportImage``) roda no docker e valida-se no Krita real.
"""

import os
import tempfile
import unittest

from hq_tools.modules.pages import exportacao


class TestPlanoDeExportacao(unittest.TestCase):
    def test_nome_de_saida_troca_a_extensao(self):
        self.assertEqual(
            "pagina_001.png", exportacao.nome_de_saida("pagina_001.kra", "png")
        )
        self.assertEqual(
            "pagina_001.jpg", exportacao.nome_de_saida("/a/b/pagina_001.kra", "jpg")
        )

    def test_atalho_so_na_resolucao_nativa(self):
        self.assertTrue(exportacao.usar_atalho("png", 300, 300))
        self.assertTrue(exportacao.usar_atalho("jpg", 300, 300))
        self.assertFalse(exportacao.usar_atalho("png", 300, 96))
        self.assertFalse(exportacao.usar_atalho("tiff", 300, 300))

    def test_precisa_reamostrar_tolera_lixo(self):
        self.assertFalse(exportacao.precisa_reamostrar(300, 300.0))
        self.assertTrue(exportacao.precisa_reamostrar(300, 96))
        self.assertTrue(exportacao.precisa_reamostrar(None, 300))

    def test_dimensoes_reamostradas(self):
        # Os números da validação interativa (A4 300 dpi -> 96 dpi).
        self.assertEqual(
            (794, 1123), exportacao.dimensoes_reamostradas(2480, 3508, 300, 96)
        )
        self.assertEqual(
            (2480, 3508), exportacao.dimensoes_reamostradas(2480, 3508, 300, 300)
        )
        # dpi de página ausente usa o pedido (sem escala).
        self.assertEqual(
            (2480, 3508), exportacao.dimensoes_reamostradas(2480, 3508, 0, 300)
        )

    def test_preparar_destino_cria_e_valida(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "exportacao")
            self.assertIsNone(exportacao.preparar_destino(destino))
            self.assertTrue(os.path.isdir(destino))
            self.assertIsNotNone(exportacao.preparar_destino(""))
            arquivo = os.path.join(pasta, "arquivo.txt")
            with open(arquivo, "w", encoding="utf-8") as handle:
                handle.write("x")
            self.assertIsNotNone(exportacao.preparar_destino(arquivo))


if __name__ == "__main__":
    unittest.main()
