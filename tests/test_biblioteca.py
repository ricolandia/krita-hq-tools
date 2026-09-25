"""Testes do núcleo da biblioteca do projeto (fora do Krita)."""

import os
import shutil
import tempfile
import unittest

from hq_tools.modules.biblioteca import core


class TestBiblioteca(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="hq_tools_biblio_")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_tamanho_novo_documento(self):
        self.assertEqual(core.tamanho_novo_documento(), 1772)
        self.assertEqual(core.tamanho_novo_documento(cm=15, dpi=300), 1772)

    def test_pasta_do_tipo(self):
        pasta = core.pasta_do_tipo(self.base, "balao")
        self.assertTrue(os.path.isdir(pasta))
        self.assertTrue(pasta.endswith("baloes"))
        with self.assertRaises(ValueError):
            core.pasta_do_tipo(self.base, "nao-existe")

    def test_slugify(self):
        self.assertEqual(core.slugify("Meu Balão!"), "meu-balao")
        self.assertEqual(core.slugify("   "), "recurso")

    def test_salvar_e_listar(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Teste")
        self.assertTrue(os.path.isfile(path))
        items = core.listar_recursos(self.base, "balao")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], "teste")
        self.assertEqual(items[0][1], path)

    def test_salvar_sem_colisao(self):
        core.salvar_recurso("<svg/>", self.base, "balao", "Teste")
        segundo = core.salvar_recurso("<svg/>", self.base, "balao", "Teste")
        self.assertNotEqual(
            segundo, os.path.join(self.base, "baloes", "teste.svg")
        )
        self.assertTrue(os.path.isfile(segundo))

    def test_nome_padrao(self):
        nome = core.nome_padrao("painel")
        self.assertTrue(nome.startswith("painel-"))


if __name__ == "__main__":
    unittest.main()