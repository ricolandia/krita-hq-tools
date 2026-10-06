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


def _rotulos_do_ast(caminho, nome, indice=None):
    """Rótulos de dados de um módulo (lidos por AST: os dockers importam Krita).

    Aceita um dicionário (usa os valores) ou uma sequência de pares, pegando
    a coluna ``indice`` (0 quando omitido).
    """
    valores = set()
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign):
            continue
        if not any(getattr(alvo, "id", "") == nome for alvo in no.targets):
            continue
        try:
            dados = ast.literal_eval(no.value)
        except ValueError:
            continue
        if isinstance(dados, dict):
            for valor in dados.values():
                if isinstance(valor, str):
                    valores.add(valor)
        else:
            for item in dados:
                if isinstance(item, str):
                    valores.add(item)
                elif isinstance(item, (list, tuple)) and len(item) > (indice or 0):
                    alvo = item[indice or 0]
                    if isinstance(alvo, str):
                        valores.add(alvo)
    return valores


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
    # Rótulos de dados mostrados por i18n.t em tempo de execução (o teste
    # estático de t() não os vê): rótulos do hub, formatos de página, tipos da
    # biblioteca, opções das retículas, conjuntos de pincéis e o catálogo de
    # perspectiva.
    usadas |= _rotulos_do_ast(PACOTE / "modules/hub/docker.py", "ROTULOS")
    usadas |= _rotulos_do_ast(
        PACOTE / "modules/pages/manager_docker.py", "FORMATO_ITENS", 1
    )
    usadas |= _rotulos_do_ast(
        PACOTE / "modules/biblioteca/docker.py", "MODOS_CAMADA", 0
    )
    for nome_modo in ("MASK_MODES", "HALFTONE_MODES", "EFFECT_MODES"):
        usadas |= _rotulos_do_ast(PACOTE / "modules/screentone/docker.py", nome_modo, 0)
    from hq_tools.modules.perspectiva import linhas as linhas_perspectiva

    for _, titulo, _, legenda in linhas_perspectiva.PRESETS:
        usadas.add(titulo)
        usadas.add(legenda)
    from hq_tools.modules.brushes import sets as brushes_sets

    for nome_conjunto, _ in brushes_sets.BRUSH_SETS:
        usadas.add(nome_conjunto)
    from hq_tools.modules.screentone import core as screentone_core

    for lista in (
        screentone_core.PATTERNS,
        screentone_core.DOT_SHAPES,
        screentone_core.LINE_SHAPES,
        screentone_core.INTERPOLATIONS,
        screentone_core.EQUALIZATIONS,
        screentone_core.UNITS,
    ):
        for rotulo, _ in lista:
            usadas.add(rotulo)
    from hq_tools.modules.biblioteca import core as biblioteca_core

    for _, rotulo, _ in biblioteca_core.TIPOS:
        usadas.add(rotulo)
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
