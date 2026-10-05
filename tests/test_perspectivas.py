"""Testes dos conjuntos de linhas de perspectiva.

A regra do autor: cada linha tem exatamente dois nós, um em cada ponta. As
retas são ``<line>`` e as curvilíneas são ``<path>`` com um único ``M`` e um
único ``A`` (as alças do arco não são nós).
"""

import contextlib
import importlib.util
import io
import os
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET

from hq_tools.modules.perspectiva import linhas

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "gerar-perspectivas.py"
PASTA = REPO / "hq_tools" / "resources" / "perspectivas"
NS = "{http://www.w3.org/2000/svg}"
CORES = {linhas.AZUL, linhas.LARANJA, linhas.CINZA}


def carregar_script():
    spec = importlib.util.spec_from_file_location("gerar_perspectivas", str(SCRIPT))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestDoisNosPorLinha(unittest.TestCase):
    def _arvore(self, nome):
        return ET.fromstring(linhas.gerar(nome, 300, 400))

    def test_todos_os_presets_geram(self):
        self.assertEqual(len(linhas.PRESETS), 9)
        for arquivo, _, _, _ in linhas.PRESETS:
            arvore = self._arvore(arquivo)
            self.assertEqual(arvore.get("viewBox"), "0 0 300 400")

    def test_somente_linhas_e_arcos(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            for filho in self._arvore(arquivo):
                self.assertIn(filho.tag, (NS + "line", NS + "path"), arquivo)

    def test_arcos_tem_dois_nos(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            for caminho in self._arvore(arquivo).findall(NS + "path"):
                d = caminho.get("d")
                self.assertEqual(d.count("M"), 1, arquivo)
                self.assertEqual(d.count("A"), 1, arquivo)
                self.assertNotIn("L", d, arquivo)
                self.assertNotIn("Z", d, arquivo)

    def test_linhas_tem_dois_pontos(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            for linha in self._arvore(arquivo).findall(NS + "line"):
                for atributo in ("x1", "y1", "x2", "y2"):
                    self.assertIsNotNone(linha.get(atributo), arquivo)

    def test_cores_da_paleta(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            cores = {elemento.get("stroke") for elemento in self._arvore(arquivo)}
            self.assertTrue(cores.issubset(CORES), arquivo)

    def test_minimo_de_elementos(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            self.assertGreaterEqual(len(self._arvore(arquivo)), 30, arquivo)


class TestArquivosGerados(unittest.TestCase):
    def test_gerar_todos_escreve_os_nove(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminhos = linhas.gerar_todos(pasta, 300, 400)
            self.assertEqual(len(caminhos), 9)
            for caminho in caminhos:
                self.assertTrue(os.path.isfile(caminho))
                with open(caminho, encoding="utf-8") as arquivo:
                    self.assertIn("<svg", arquivo.read())

    def test_assets_do_repositorio_em_sincronia(self):
        """Os SVGs versionados batem byte a byte com o gerador."""
        for arquivo, _, _, _ in linhas.PRESETS:
            caminho = PASTA / arquivo
            self.assertTrue(caminho.is_file(), arquivo)
            esperado = linhas.gerar(arquivo, 900, 1200)
            self.assertEqual(caminho.read_text(encoding="utf-8"), esperado, arquivo)

    def test_cli_lista_os_presets(self):
        modulo = carregar_script()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(modulo.main(["--listar"]), 0)


if __name__ == "__main__":
    unittest.main()
