"""Testes das guias de margem (núcleo puro, sem Krita)."""

import unittest

from hq_tools.modules.pages import guias


class TestPosicoesDeMargem(unittest.TestCase):
    def test_a4_300dpi(self):
        # A4 = 210 x 297 mm; a 300 dpi, 2480 x 3508 px (arredondado).
        verticais, horizontais = guias.posicoes_de_margem(2480, 3508, 300)
        self.assertEqual(len(verticais), 6)
        self.assertEqual(len(horizontais), 6)
        # 0,5 cm a 300 dpi = 0,5 * 300 / 2,54 = 59,055...
        self.assertAlmostEqual(min(verticais), 59.055, places=2)
        self.assertAlmostEqual(max(verticais), 2480 - 59.055, places=2)
        self.assertAlmostEqual(min(horizontais), 59.055, places=2)
        self.assertAlmostEqual(max(horizontais), 3508 - 59.055, places=2)

    def test_mesclar_ordena(self):
        verticais, horizontais = guias.posicoes_de_margem(1000, 2000, 300)
        self.assertEqual(
            guias.mesclar([], verticais),
            sorted(round(valor, 3) for valor in verticais),
        )
        self.assertEqual(
            guias.mesclar([], horizontais),
            sorted(round(valor, 3) for valor in horizontais),
        )


class TestMesclar(unittest.TestCase):
    def test_preserva_as_existentes(self):
        # Guia de perspectiva em 500 px não pode sumir ao criar as de margem.
        resultado = guias.mesclar([500.0], [100.0, 900.0])
        self.assertEqual(resultado, [100.0, 500.0, 900.0])

    def test_nao_duplica(self):
        resultado = guias.mesclar([100.0, 900.0], [100.0, 900.0])
        self.assertEqual(resultado, [100.0, 900.0])

    def test_arredonda_para_comparar(self):
        resultado = guias.mesclar([100.0004], [100.0001])
        self.assertEqual(resultado, [100.0])

    def test_listas_vazias(self):
        self.assertEqual(guias.mesclar([], []), [])
        self.assertEqual(guias.mesclar(None, [10.0]), [10.0])
        self.assertEqual(guias.mesclar([10.0], None), [10.0])


if __name__ == "__main__":
    unittest.main()
