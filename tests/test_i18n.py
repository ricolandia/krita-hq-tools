"""Testes da camada de idioma (PT/EN) e da cobertura das traduções.

O teste de cobertura varre o código do plugin atrás de chamadas
``i18n.t("...")`` e exige que toda string visível tenha entrada no dicionário
(uma string nova sem tradução quebraria o teste, não a interface).
"""

import ast
import json
import pathlib
import unittest

from hq_tools.core import i18n
from hq_tools.core.i18n_en import TRADUCOES

REPO = pathlib.Path(__file__).resolve().parent.parent
PACOTE = REPO / "hq_tools"


def strings_usadas():
    usadas = set()
    for caminho in PACOTE.rglob("*.py"):
        if "__pycache__" in str(caminho):
            continue
        arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call):
                continue
            func = no.func
            if not isinstance(func, ast.Attribute) or func.attr != "t":
                continue
            if (
                no.args
                and isinstance(no.args[0], ast.Constant)
                and isinstance(no.args[0].value, str)
            ):
                usadas.add(no.args[0].value)
    # Os nomes das poses são chaves dinâmicas: o docker mostra o campo "nome"
    # do JSON passando por i18n.t; entram aqui para a cobertura valer para eles.
    for caminho in PACOTE.rglob("poses/*/*.json"):
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        nome = dados.get("nome")
        if isinstance(nome, str) and nome:
            usadas.add(nome)
    return usadas


class TestEscolhaDeIdioma(unittest.TestCase):
    def test_portugues(self):
        self.assertEqual(i18n.escolher_idioma("pt_BR"), i18n.PT)
        self.assertEqual(i18n.escolher_idioma("pt"), i18n.PT)

    def test_resto_usa_ingles(self):
        self.assertEqual(i18n.escolher_idioma("en_US"), i18n.EN)
        self.assertEqual(i18n.escolher_idioma("fr_FR"), i18n.EN)
        self.assertEqual(i18n.escolher_idioma(None), i18n.EN)


class TestTraducao(unittest.TestCase):
    def tearDown(self):
        i18n.definir_idioma(None)

    def test_em_portugues_devolve_o_original(self):
        i18n.definir_idioma(i18n.PT)
        self.assertEqual(i18n.t("Atualizar"), "Atualizar")

    def test_em_ingles_traduz(self):
        i18n.definir_idioma(i18n.EN)
        self.assertEqual(i18n.t("Atualizar"), "Refresh")

    def test_sem_traducao_devolve_o_original(self):
        i18n.definir_idioma(i18n.EN)
        self.assertEqual(i18n.t("string que não existe"), "string que não existe")


class TestCobertura(unittest.TestCase):
    def test_toda_string_visivel_tem_traducao(self):
        usadas = strings_usadas()
        faltando = sorted(usadas - set(TRADUCOES))
        self.assertEqual([], faltando, "\n".join(faltando))

    def test_nenhuma_traducao_orfa(self):
        # Chave sem uso é sinal de erro de digitação na chave (a string real
        # ficaria sem tradução e o teste de cobertura acima não acharia o par).
        usadas = strings_usadas()
        orfas = sorted(set(TRADUCOES) - usadas)
        self.assertEqual([], orfas, "\n".join(orfas))

    def test_nenhuma_traducao_vazia(self):
        vazias = sorted(chave for chave, valor in TRADUCOES.items() if not valor)
        self.assertEqual([], vazias, "\n".join(vazias))


if __name__ == "__main__":
    unittest.main()
