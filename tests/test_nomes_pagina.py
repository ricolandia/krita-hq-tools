"""Testes do próximo número de página (duplicação sem sobrescrever)."""

import unittest

from hq_tools.modules.pages import nomes


class TestProximoIndiceLivre(unittest.TestCase):
    def test_lista_vazia_comeca_em_um(self):
        self.assertEqual(1, nomes.proximo_indice_livre([]))

    def test_primeiro_numero_livre(self):
        arquivos = ["pagina_001.kra", "pagina_002.kra"]
        self.assertEqual(3, nomes.proximo_indice_livre(arquivos))

    def test_aproveita_buraco(self):
        arquivos = ["pagina_001.kra", "pagina_003.kra"]
        self.assertEqual(2, nomes.proximo_indice_livre(arquivos))

    def test_ignora_maiusculas(self):
        # O Windows não diferencia maiúsculas: "Pagina_005.KRA" ocupa o 5.
        arquivos = [
            "pagina_001.kra",
            "pagina_002.kra",
            "pagina_003.kra",
            "pagina_004.kra",
            "Pagina_005.KRA",
        ]
        self.assertEqual(6, nomes.proximo_indice_livre(arquivos))

    def test_prefixo_e_extensao_em_maiusculas(self):
        arquivos = ["PAGINA_001.KRA", "pagina_002.kra"]
        self.assertEqual(3, nomes.proximo_indice_livre(arquivos))

    def test_ignora_nomes_fora_do_padrao(self):
        arquivos = [
            "pagina_extra.kra",
            "modelo-001.kra",
            "outra_005.kra",
            "pagina_001.kra.bak",
        ]
        self.assertEqual(1, nomes.proximo_indice_livre(arquivos))

    def test_prefixo_configuravel(self):
        self.assertEqual(
            2, nomes.proximo_indice_livre(["quadro_001.kra"], prefixo="quadro")
        )


if __name__ == "__main__":
    unittest.main()
