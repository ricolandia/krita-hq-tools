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


MODULOS = [
    ("pages", "Páginas"),
    ("producao", "Produção"),
    ("moodboard", "Moodboard"),
    ("biblioteca", "Biblioteca"),
    ("perspectiva", "Perspectiva"),
    ("viewer3d", "3D"),
    ("palettes", "Paletas"),
    ("brushes", "Pincéis"),
    ("screentone", "Retículas"),
    ("balloons", "Balões"),
    ("onomatopeias", "Onomatopeias"),
]


class TestAgrupamento(unittest.TestCase):
    def test_grupos_na_ordem(self):
        grupos = registro.agrupar(MODULOS)
        chaves = [tuple(chave for chave, _ in grupo) for grupo in grupos]
        self.assertEqual(
            chaves,
            [
                ("pages", "producao"),
                ("moodboard", "biblioteca"),
                ("perspectiva", "viewer3d"),
                ("palettes", "brushes"),
                ("screentone", "balloons"),
                ("onomatopeias",),
            ],
        )

    def test_todos_os_modulos_aparecem_uma_vez(self):
        grupos = registro.agrupar(MODULOS)
        vistas = [chave for grupo in grupos for chave, _ in grupo]
        self.assertEqual(sorted(vistas), sorted(chave for chave, _ in MODULOS))
        self.assertEqual(len(vistas), len(set(vistas)))

    def test_modulo_fora_dos_grupos_cai_no_fim(self):
        grupos = registro.agrupar(MODULOS + [("novo", "Novo")])
        self.assertEqual(grupos[-1], [("novo", "Novo")])

    def test_grupo_incompleto_nao_deixa_buraco(self):
        grupos = registro.agrupar([("pages", "Páginas"), ("balloons", "Balões")])
        self.assertEqual(
            [tuple(chave for chave, _ in grupo) for grupo in grupos],
            [("pages",), ("balloons",)],
        )

    def test_lista_vazia(self):
        self.assertEqual(registro.agrupar([]), [])


if __name__ == "__main__":
    unittest.main()
