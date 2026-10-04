"""Testes da ordem de camadas (base -> topo)."""

import unittest

from hq_tools.core import camadas


class TestOrdemComNoAbaixo(unittest.TestCase):
    def test_insere_no_meio(self):
        self.assertEqual(
            camadas.ordem_com_no_abaixo([1, 2, 3], 2, 9), [1, 9, 2, 3]
        )

    def test_insere_no_fundo(self):
        self.assertEqual(
            camadas.ordem_com_no_abaixo([1, 2, 3], 1, 9), [9, 1, 2, 3]
        )

    def test_insere_abaixo_do_topo(self):
        self.assertEqual(
            camadas.ordem_com_no_abaixo([1, 2, 3], 3, 9), [1, 2, 9, 3]
        )

    def test_alvo_ausente(self):
        self.assertIsNone(camadas.ordem_com_no_abaixo([1, 2], 9, 8))

    def test_novo_ja_na_lista_nao_duplica(self):
        self.assertEqual(
            camadas.ordem_com_no_abaixo([1, 9, 2], 2, 9), [1, 9, 2]
        )

    def test_chave_para_objetos(self):
        class No:
            def __init__(self, nome):
                self.nome = nome

        a, b, c = No("a"), No("b"), No("c")
        resultado = camadas.ordem_com_no_abaixo(
            [a, b, c], b, No("novo"), chave=lambda no: no.nome
        )
        self.assertEqual([no.nome for no in resultado], ["a", "novo", "b", "c"])


if __name__ == "__main__":
    unittest.main()
