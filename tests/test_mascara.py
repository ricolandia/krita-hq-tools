"""Testes da máscara de transparência dos painéis (núcleo puro)."""

import unittest

from hq_tools.modules.pages import mascara


class TestMascaraDosPaineis(unittest.TestCase):
    def test_painel_unico_cobre_tudo(self):
        self.assertEqual(
            mascara.mascara_dos_paineis([(0.0, 0.0, 1.0, 1.0)], 4, 3),
            b"\xff" * 12,
        )

    def test_dois_paineis(self):
        dados = mascara.mascara_dos_paineis([(0.0, 0.0, 0.5, 1.0)], 4, 2)
        self.assertEqual(dados, b"\xff\xff\x00\x00" * 2)

    def test_lista_vazia(self):
        self.assertEqual(mascara.mascara_dos_paineis([], 4, 2), b"\x00" * 8)

    def test_retangulo_em_pixels_com_recorte(self):
        self.assertEqual(
            mascara.retangulo_em_pixels((-0.1, 0.0, 0.5, 1.2), 100, 50),
            (0, 0, 40, 50),
        )
        self.assertEqual(
            mascara.retangulo_em_pixels((0.5, 0.5, 0.5, 0.5), 100, 50),
            (50, 25, 50, 25),
        )
        self.assertEqual(
            mascara.retangulo_em_pixels((0.0, 0.0, 0.0, 0.0), 100, 50),
            (0, 0, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
