"""Testes do leitor/escritor do comicsConfig.json (rodam fora do Krita)."""

import json
import os
import shutil
import tempfile
import unittest

from hq_tools.core.cpmt import CPMTProject


def make_project(root, name="Meu Projeto", location="pages"):
    config = {
        "projectName": name,
        "concept": "teste",
        "pagesLocation": location,
        "exportLocation": "export",
        "templateLocation": "templates",
        "translationsLocation": "translations",
        "pageNumber": 0,
        "pages": [],
    }
    os.makedirs(os.path.join(root, location), exist_ok=True)
    with open(os.path.join(root, "comicsConfig.json"), "w", encoding="utf-8") as handle:
        json.dump(config, handle)
    return root


class TestCPMTProject(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="hq_tools_cpmt_")
        make_project(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_is_project(self):
        self.assertTrue(CPMTProject.is_project(self.root))

    def test_nome_da_proxima_pagina(self):
        project = CPMTProject(self.root)
        self.assertEqual(project.project_name, "Meu Projeto")
        self.assertEqual(project.next_page_name(1), "Meu_Projeto001.kra")
        self.assertEqual(
            project.next_page_relative(2), os.path.join("pages", "Meu_Projeto002.kra")
        )

    def test_nome_com_digito_no_final(self):
        root = tempfile.mkdtemp(prefix="hq_tools_cpmt_")
        try:
            make_project(root, name="Projeto2")
            project = CPMTProject(root)
            self.assertEqual(project.next_page_name(1), "Projeto2_001.kra")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_registrar_e_reordenar(self):
        project = CPMTProject(self.root)
        relatives = [
            os.path.join("pages", "Meu_Projeto001.kra"),
            os.path.join("pages", "Meu_Projeto002.kra"),
        ]
        project.register_pages(relatives)
        self.assertEqual(project.page_number, 2)
        self.assertEqual(project.next_page_name(1), "Meu_Projeto003.kra")

        project.set_page_order(list(reversed(relatives)))
        reloaded = CPMTProject(self.root)
        self.assertEqual(reloaded.page_relatives(), list(reversed(relatives)))


if __name__ == "__main__":
    unittest.main()
