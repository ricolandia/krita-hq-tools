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

    def test_salvar_bytes_png(self):
        path = core.salvar_bytes(b"\x89PNG\r\n\x1a\n", self.base, "balao", "Pintura", ".png")
        self.assertTrue(path.endswith(".png"))
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")

    def test_listar_svg_e_png(self):
        core.salvar_recurso("<svg/>", self.base, "balao", "Vetor")
        core.salvar_bytes(b"dados", self.base, "balao", "Pintura", ".png")
        items = core.listar_recursos(self.base, "balao")
        nomes = [nome for nome, _ in items]
        self.assertIn("vetor", nomes)
        self.assertIn("pintura", nomes)

    def test_caminho_livre_com_extensao(self):
        primeiro = core.salvar_bytes(b"a", self.base, "balao", "teste", ".png")
        pasta = core.pasta_do_tipo(self.base, "balao")
        segundo = core.caminho_livre(pasta, "teste", ".png")
        self.assertTrue(primeiro.endswith(".png"))
        self.assertNotEqual(primeiro, segundo)

    def test_renomear_recurso(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Antes")
        novo = core.renomear_recurso(path, "Depois")
        self.assertFalse(os.path.exists(path))
        self.assertEqual(os.path.basename(novo), "depois.svg")
        self.assertEqual(core.listar_recursos(self.base, "balao")[0][0], "depois")

    def test_renomear_para_o_mesmo_nome_nao_mexe(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Igual")
        self.assertEqual(core.renomear_recurso(path, "Igual"), path)
        self.assertTrue(os.path.isfile(path))

    def test_renomear_recusa_colisao(self):
        primeiro = core.salvar_recurso("<svg/>", self.base, "balao", "Um")
        core.salvar_recurso("<svg/>", self.base, "balao", "Dois")
        with self.assertRaises(FileExistsError):
            core.renomear_recurso(primeiro, "Dois")
        self.assertTrue(os.path.isfile(primeiro))

    def test_duplicar_recurso_gera_sufixo(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Original")
        copia = core.duplicar_recurso(path)
        self.assertNotEqual(copia, path)
        self.assertEqual(os.path.basename(copia), "original-copia.svg")
        nomes = sorted(nome for nome, _ in core.listar_recursos(self.base, "balao"))
        self.assertEqual(nomes, ["original", "original-copia"])

    def test_duplicar_recurso_com_nome(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Base")
        copia = core.duplicar_recurso(path, "Copia nova")
        self.assertTrue(copia.endswith("copia-nova.svg"))

    def test_duplicar_preserva_extensao_png(self):
        path = core.salvar_bytes(b"\x89PNG", self.base, "balao", "Pintura", ".png")
        copia = core.duplicar_recurso(path)
        self.assertTrue(copia.endswith(".png"))
        self.assertNotEqual(copia, path)

    def test_apagar_recurso(self):
        path = core.salvar_recurso("<svg/>", self.base, "balao", "Some")
        core.apagar_recurso(path)
        self.assertFalse(os.path.exists(path))
        self.assertEqual(core.listar_recursos(self.base, "balao"), [])

    def test_apagar_recusa_extensao_estranha(self):
        path = os.path.join(self.base, "nota.txt")
        with open(path, "w") as handle:
            handle.write("nao é recurso")
        with self.assertRaises(ValueError):
            core.apagar_recurso(path)
        self.assertTrue(os.path.isfile(path))


if __name__ == "__main__":
    unittest.main()