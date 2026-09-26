"""Testes das specs de modelos de página (fora do Krita)."""

import unittest

from hq_tools.modules.pages import modelos


class TestModelos(unittest.TestCase):
    def test_layout_unico(self):
        paineis = modelos.layout_paineis("unico")
        self.assertEqual(paineis, modelos.PAINEL_UNICO)

    def test_tirinhas(self):
        self.assertEqual(len(modelos.layout_paineis("tira1")), 1)
        self.assertEqual(len(modelos.layout_paineis("tira2")), 2)
        self.assertEqual(len(modelos.layout_paineis("tira3")), 3)

    def test_grades(self):
        self.assertEqual(len(modelos.layout_paineis("grade2x2")), 4)
        self.assertEqual(len(modelos.layout_paineis("grade3x3")), 9)

    def test_todos_os_modelos_tem_layout_valido(self):
        for nome, formato, chave in modelos.MODELOS:
            self.assertIn(formato, ("A4", "A3", "tirinha"), nome)
            paineis = modelos.layout_paineis(chave)
            self.assertTrue(paineis, nome)
            for painel in paineis:
                self.assertEqual(len(painel), 4, nome)
                self.assertGreaterEqual(painel[0], 0.0, nome)
                self.assertLessEqual(painel[0] + painel[2], 1.0, nome)

    def test_slug(self):
        self.assertEqual(modelos.slug("A4 padrão"), "a4-padrao")
        self.assertEqual(modelos.slug("Tirinha 2 tiras"), "tirinha-2-tiras")


if __name__ == "__main__":
    unittest.main()