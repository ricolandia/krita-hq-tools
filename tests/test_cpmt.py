"""Testes do leitor/escritor do comicsConfig.json (rodam fora do Krita)."""

import json
import os
import shutil
import tempfile
import unittest

from hq_tools.core.cpmt import CPMTProject, create_project_with_page


def make_project(root, name="Meu Projeto", location="pages", legacy=False):
    config = {
        "projectName": name,
        "concept": "teste",
        "language": "pt_BR",
        "pagesLocation": location,
        "exportLocation": "export",
        "templateLocation": "templates",
        "translationsLocation": "translations",
        "pageNumber": 0,
        "pages": [],
    }
    os.makedirs(os.path.join(root, location), exist_ok=True)
    filename = "comicsConfig.json" if legacy else "comicConfig.json"
    encoding = "utf-8" if legacy else "utf-16"
    with open(os.path.join(root, filename), "w", encoding=encoding, newline="") as handle:
        json.dump(config, handle, indent=4, sort_keys=True, ensure_ascii=False)
    return root


class TestCPMTProject(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="hq_tools_cpmt_")
        make_project(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_is_project(self):
        self.assertTrue(CPMTProject.is_project(self.root))

    def test_legado_comicsconfig_utf8(self):
        root = tempfile.mkdtemp(prefix="hq_tools_cpmt_")
        try:
            make_project(root, legacy=True)
            self.assertTrue(CPMTProject.is_project(root))
            project = CPMTProject(root)
            self.assertEqual(project.project_name, "Meu Projeto")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_create_project_with_page(self):
        root = tempfile.mkdtemp(prefix="hq_tools_cpmt_")
        try:
            path = create_project_with_page(root, "pagina_001.kra", "minha-hq")
            self.assertTrue(os.path.isfile(path))
            self.assertEqual(os.path.basename(path), "comicConfig.json")
            project = CPMTProject(root)
            self.assertEqual(project.project_name, "minha-hq")
            self.assertEqual(project.pages_location, ".")
            self.assertEqual(project.page_number, 1)
            self.assertEqual(project.page_relatives(), ["pagina_001.kra"])
            self.assertEqual(project.next_page_name(1), "minha-hq002.kra")
            for sub in ("export", "templates", "translations"):
                self.assertTrue(os.path.isdir(os.path.join(root, sub)), sub)
        finally:
            shutil.rmtree(root, ignore_errors=True)

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
