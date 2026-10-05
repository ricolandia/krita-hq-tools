"""Testes do registro de instâncias dos dockers (puro, sem Krita)."""

import unittest

from hq_tools.core import registro


class TestRegistro(unittest.TestCase):
    def setUp(self):
        registro.limpar()

    def tearDown(self):
        registro.limpar()

    def test_registrar_e_obter(self):
        alvo = object()
        registro.registrar("pages", alvo)
        self.assertIs(registro.obter("pages"), alvo)

    def test_chave_ausente_devolve_none(self):
        self.assertIsNone(registro.obter("nada"))

    def test_instancias_devolve_copia(self):
        registro.registrar("pages", object())
        copia = registro.instancias()
        copia["outro"] = object()
        self.assertNotIn("outro", registro.instancias())

    def test_observador_recebe_o_registro(self):
        recebidos = []
        registro.ao_registrar(lambda chave, docker: recebidos.append((chave, docker)))
        alvo = object()
        registro.registrar("hub", alvo)
        self.assertEqual(recebidos, [("hub", alvo)])

    def test_observador_que_falha_nao_derruba_o_registro(self):
        def quebrado(chave, docker):
            raise RuntimeError("observador com erro")

        registro.ao_registrar(quebrado)
        alvo = object()
        registro.registrar("pages", alvo)
        self.assertIs(registro.obter("pages"), alvo)

    def test_registrar_de_novo_substitui(self):
        primeiro, segundo = object(), object()
        registro.registrar("pages", primeiro)
        registro.registrar("pages", segundo)
        self.assertIs(registro.obter("pages"), segundo)

    def test_limpar_esvazia_tudo(self):
        registro.registrar("pages", object())
        registro.limpar()
        self.assertEqual(registro.instancias(), {})


if __name__ == "__main__":
    unittest.main()
