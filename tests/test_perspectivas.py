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

    def test_somente_caminhos(self):
        # <line> não tem garantia de virar forma no importador do Krita; tudo
        # é <path>, que vira forma vetorial de dois nós.
        for arquivo, _, _, _ in linhas.PRESETS:
            for filho in self._arvore(arquivo):
                self.assertEqual(filho.tag, NS + "path", arquivo)

    def test_dois_nos_por_linha(self):
        for arquivo, _, _, _ in linhas.PRESETS:
            for caminho in self._arvore(arquivo).findall(NS + "path"):
                d = caminho.get("d")
                self.assertEqual(d.count("M"), 1, arquivo)
                self.assertEqual(d.count("L") + d.count("A"), 1, arquivo)
                self.assertNotIn("Z", d, arquivo)

    def test_tem_retas_e_arcos(self):
        tem_reta = tem_arco = False
        for arquivo, _, _, _ in linhas.PRESETS:
            for caminho in self._arvore(arquivo).findall(NS + "path"):
                tem_reta = tem_reta or " L " in caminho.get("d")
                tem_arco = tem_arco or " A " in caminho.get("d")
        self.assertTrue(tem_reta)
        self.assertTrue(tem_arco)

    def test_deslocamento_embrulha_em_g(self):
        svg = linhas.gerar("01-frontal.svg", 300, 400, deslocamento=(10, 20))
        self.assertIn('translate(10.0 20.0)', svg)
        arvore = ET.fromstring(svg)
        grupo = arvore.find(NS + "g")
        self.assertIsNotNone(grupo)
        self.assertGreater(len(grupo.findall(NS + "path")), 0)

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
