"""Testes do núcleo da produção (rodam fora do Krita)."""

import os
import shutil
import tempfile
import unittest
from datetime import date

from hq_tools.modules.producao import core as producao

ROTEIRO = """
pagina 1
layout grade2x2
narracao p1: Era uma vez...
fala p1 joao: Voce viu aquilo?
fala p4 maria: Ultima fala.

pagina 2
layout tira3
fala p1: Um
fala p2: Dois
fala p3: Tres
"""


class TestChecklist(unittest.TestCase):
    def test_montar_paginas_e_paineis(self):
        checklist = producao.montar(ROTEIRO)
        self.assertEqual(len(checklist), 2)
        self.assertEqual(checklist[0]["pagina"], 1)
        self.assertEqual(len(checklist[0]["paineis"]), 4)
        self.assertEqual(len(checklist[1]["paineis"]), 3)

    def test_estado_padrao_esboco(self):
        checklist = producao.montar(ROTEIRO)
        self.assertEqual(checklist[0]["paineis"][0]["estado"], "esboco")

    def test_estados_preservados_ao_remontar(self):
        checklist = producao.montar(ROTEIRO, {"1-1": "final", "2-3": "arte"})
        self.assertEqual(checklist[0]["paineis"][0]["estado"], "final")
        self.assertEqual(checklist[1]["paineis"][2]["estado"], "arte")
        self.assertEqual(checklist[0]["paineis"][1]["estado"], "esboco")

    def test_falas_ficam_no_painel_certo(self):
        checklist = producao.montar(ROTEIRO)
        primeiro = checklist[0]["paineis"][0]
        self.assertEqual(len(primeiro["falas"]), 2)
        self.assertEqual(primeiro["falas"][0]["kind"], "narracao")
        self.assertEqual(primeiro["falas"][1]["character"], "joao")
        self.assertEqual(checklist[0]["paineis"][3]["falas"][0]["character"], "maria")

    def test_estados_do_checklist(self):
        checklist = producao.montar(ROTEIRO, {"1-1": "final"})
        estados = producao.estados_do_checklist(checklist)
        self.assertEqual(estados["1-1"], "final")
        self.assertEqual(estados["2-3"], "esboco")
        self.assertEqual(len(estados), 7)

    def test_erro_de_sintaxe_sobe(self):
        with self.assertRaises(Exception):
            producao.montar("pagina 1\ncomando estranho\n")


class TestProgresso(unittest.TestCase):
    def test_contagem(self):
        checklist = producao.montar(
            ROTEIRO, {"1-1": "final", "1-2": "final", "1-3": "arte"}
        )
        contagem = producao.progresso(checklist)
        self.assertEqual(contagem["total"], 7)
        self.assertEqual(contagem["finais"], 2)
        self.assertEqual(contagem["arte"], 1)
        self.assertEqual(contagem["esboco"], 4)

    def test_progresso_da_pagina(self):
        checklist = producao.montar(ROTEIRO, {"1-4": "final"})
        self.assertEqual(producao.progresso_da_pagina(checklist[0]), (1, 4))

    def test_proximo_estado_cicla(self):
        self.assertEqual(producao.proximo_estado("esboco"), "arte")
        self.assertEqual(producao.proximo_estado("arte"), "final")
        self.assertEqual(producao.proximo_estado("final"), "esboco")
        self.assertEqual(producao.proximo_estado("outro"), "esboco")


class TestProjecao(unittest.TestCase):
    def test_semanas_e_data(self):
        semanas, previsao = producao.projecao(16, 8, hoje=date(2026, 10, 6))
        self.assertEqual(semanas, 2)
        self.assertEqual(previsao, date(2026, 10, 20))

    def test_arredonda_para_cima(self):
        semanas, _ = producao.projecao(17, 8, hoje=date(2026, 10, 6))
        self.assertEqual(semanas, 3)

    def test_pronto_nao_tem_previsao(self):
        self.assertEqual(producao.projecao(0, 8), (0, None))

    def test_meta_zero_conta_um(self):
        semanas, _ = producao.projecao(3, 0, hoje=date(2026, 10, 6))
        self.assertEqual(semanas, 3)


class TestMarkdown(unittest.TestCase):
    def test_exportacao(self):
        checklist = producao.montar(ROTEIRO, {"1-1": "final", "1-2": "arte"})
        texto = producao.para_markdown(
            checklist, meta_semanal=8, hoje=date(2026, 10, 6),
            rotulos={"narracao": "Narration"}, titulo="Production checklist",
        )
        self.assertIn("# Production checklist", texto)
        self.assertIn("## Página 1: 1/4 finais", texto)
        self.assertIn("- [x] Painel 1 (Final) · Narration: Era uma vez... · joao: Voce viu aquilo?", texto)
        self.assertIn("- [-] Painel 2 (Arte)", texto)
        self.assertIn("~1 semana(s) · entrega ~13/10", texto)

    def test_resumo_de_falas(self):
        checklist = producao.montar(ROTEIRO)
        painel = checklist[1]["paineis"][0]
        self.assertEqual(producao.falas_resumo(painel), "Um")
        primeiro = checklist[0]["paineis"][0]
        self.assertEqual(
            producao.falas_resumo(primeiro), "Narração: Era uma vez... · joao: Voce viu aquilo?"
        )


class TestArquivos(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="producao-teste-")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_estados_ida_e_volta(self):
        producao.salvar(self.pasta, {"1-1": "final"}, 8)
        estados, meta = producao.carregar(self.pasta)
        self.assertEqual(estados, {"1-1": "final"})
        self.assertEqual(meta, 8)

    def test_estados_quebrados_sao_filtrados(self):
        producao.salvar(self.pasta, {"1-1": "inventado", "1-2": "arte"}, "oito")
        estados, meta = producao.carregar(self.pasta)
        self.assertEqual(estados, {"1-2": "arte"})
        self.assertEqual(meta, 0)

    def test_json_corrompido_devolve_vazio(self):
        with open(producao.caminho_estados(self.pasta), "w", encoding="utf-8") as arquivo:
            arquivo.write("{nao e json")
        self.assertEqual(producao.carregar(self.pasta), ({}, 0))

    def test_sem_temporarios(self):
        producao.salvar(self.pasta, {}, 0)
        producao.salvar_roteiro(self.pasta, "pagina 1\n")
        self.assertFalse(os.path.exists(producao.caminho_estados(self.pasta) + ".tmp"))
        self.assertFalse(os.path.exists(producao.caminho_roteiro(self.pasta) + ".tmp"))

    def test_roteiro_ida_e_volta(self):
        producao.salvar_roteiro(self.pasta, ROTEIRO)
        self.assertEqual(producao.carregar_roteiro(self.pasta), ROTEIRO)

    def test_roteiro_inexistente_devolve_vazio(self):
        self.assertEqual(producao.carregar_roteiro(self.pasta), "")

    def test_pagina_do_arquivo(self):
        for nome in ("pagina_001.kra", "pagina_012.kra", "outra.kra", "nota.txt"):
            open(os.path.join(self.pasta, nome), "wb").close()
        self.assertTrue(producao.pagina_do_arquivo(self.pasta, 12).endswith("pagina_012.kra"))
        self.assertTrue(producao.pagina_do_arquivo(self.pasta, 1).endswith("pagina_001.kra"))
        self.assertIsNone(producao.pagina_do_arquivo(self.pasta, 3))
        self.assertIsNone(producao.pagina_do_arquivo(os.path.join(self.pasta, "nada"), 1))


if __name__ == "__main__":
    unittest.main()
