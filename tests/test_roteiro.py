"""Testes do parser de roteiro (rodam fora do Krita)."""

import unittest

from hq_tools.modules.pages import roteiro


SCRIPT = """
# página de teste
pagina 1
formato A4
dpi 300
layout grade2x2
margem 5%
sarjeta 2%
narracao p1: Era uma vez...
fala p1: Voce viu aquilo?
fala p4: Ultima fala.

pagina 2
layout tira3
direcao rtl
fala p1: Um
fala p2: Dois
fala p3: Tres
"""


class TestRoteiro(unittest.TestCase):
    def test_parse_basico(self):
        pages = roteiro.parse_script(SCRIPT)
        self.assertEqual(len(pages), 2)
        first = pages[0]
        self.assertEqual(first["format"], "A4")
        self.assertEqual(first["dpi"], 300)
        self.assertEqual(first["rows"], 2)
        self.assertEqual(first["cols"], 2)
        self.assertEqual(len(first["panels"]), 4)
        self.assertEqual(len(first["balloons"]), 3)
        self.assertEqual(first["balloons"][0]["kind"], "narracao")
        self.assertEqual(first["balloons"][0]["panel"], 1)

    def test_direcao_rtl_inverte_colunas(self):
        pages = roteiro.parse_script(SCRIPT)
        second = pages[1]
        self.assertEqual(second["direction"], "rtl")
        ltr = roteiro.build_panels(1, 3, 0.05, 0.02, "ltr")
        rtl = roteiro.build_panels(1, 3, 0.05, 0.02, "rtl")
        self.assertEqual(len(ltr), len(rtl))
        self.assertAlmostEqual(ltr[0][0], rtl[2][0])
        self.assertAlmostEqual(ltr[2][0], rtl[0][0])

    def test_layout_personalizado(self):
        page = roteiro.new_page()
        page["layout"] = "2x3"
        roteiro.finalize_page(page)
        self.assertEqual(page["rows"], 2)
        self.assertEqual(page["cols"], 3)
        self.assertEqual(len(page["panels"]), 6)

    def test_layout_grade_generico(self):
        self.assertEqual(roteiro.parse_layout("grade3x3"), (3, 3))
        self.assertEqual(roteiro.parse_layout("grade 4x2"), (4, 2))
        self.assertEqual(roteiro.parse_layout("grade2x3"), (2, 3))
        self.assertEqual(roteiro.parse_layout("5x2"), (5, 2))
        self.assertEqual(roteiro.parse_layout("grade10x10"), (6, 6))

    def test_script_com_grade_generica(self):
        pages = roteiro.parse_script("pagina 1\nlayout grade3x3\nfala p9: Ultimo.\n")
        self.assertEqual(len(pages[0]["panels"]), 9)
        self.assertEqual(pages[0]["layout"], "3x3")

    def test_layout_desconhecido_orienta(self):
        with self.assertRaises(roteiro.RoteiroError) as contexto:
            roteiro.parse_layout("grade")
        self.assertIn("gradeRxC", str(contexto.exception))

    def test_painel_invalido(self):
        with self.assertRaises(roteiro.RoteiroError):
            roteiro.parse_script("pagina 1\nlayout quadro\nfala p2: fora do painel\n")

    def test_erro_de_comando(self):
        with self.assertRaises(roteiro.RoteiroError):
            roteiro.parse_script("pagina 1\ncomando estranho\n")

    def test_plano_com_e_sem_dois_pontos(self):
        pages = roteiro.parse_script(
            "pagina 1\nlayout grade2x2\nplano p1: geral\nplano p2 close\nnarracao p1: cena\n"
        )
        self.assertEqual(pages[0]["planos"], {1: "geral", 2: "close"})

    def test_plano_valor_livre(self):
        pages = roteiro.parse_script("pagina 1\nplano p1: plano médio com grua baixa\n")
        self.assertEqual(pages[0]["planos"][1], "plano médio com grua baixa")

    def test_plano_sem_valor(self):
        with self.assertRaises(roteiro.RoteiroError):
            roteiro.parse_script("pagina 1\nplano p1:\n")

    def test_plano_sem_painel(self):
        with self.assertRaises(roteiro.RoteiroError):
            roteiro.parse_script("pagina 1\nplano geral\n")

    def test_plano_painel_invalido(self):
        with self.assertRaises(roteiro.RoteiroError):
            roteiro.parse_script("pagina 1\nlayout quadro\nplano p9: close\n")

    def test_personagem_na_fala(self):
        pages = roteiro.parse_script(
            "pagina 1\nlayout grade2x2\nfala p1 joao: Voce viu aquilo?\n"
        )
        balloon = pages[0]["balloons"][0]
        self.assertEqual(balloon["character"], "joao")
        self.assertEqual(balloon["text"], "Voce viu aquilo?")

    def test_fala_sem_personagem_fica_vazia(self):
        pages = roteiro.parse_script(SCRIPT)
        self.assertEqual(pages[0]["balloons"][0]["character"], "")
        self.assertEqual(pages[0]["balloons"][1]["character"], "")

    def test_texto_com_dois_pontos_depois_do_personagem(self):
        pages = roteiro.parse_script(
            "pagina 1\nlayout quadro\nfala p1 joao: Ele disse: oi.\n"
        )
        balloon = pages[0]["balloons"][0]
        self.assertEqual(balloon["character"], "joao")
        self.assertEqual(balloon["text"], "Ele disse: oi.")

    def test_narracao_sem_personagem(self):
        pages = roteiro.parse_script(
            "pagina 1\nlayout quadro\nnarracao p1: Era uma vez.\n"
        )
        self.assertEqual(pages[0]["balloons"][0]["character"], "")

    def test_page_pixels(self):
        page = roteiro.new_page()
        width, height = roteiro.page_pixels(page, "A4", 300)
        self.assertEqual(width, 2480)
        self.assertEqual(height, 3508)

    def test_page_pixels_a3_e_tirinha(self):
        width, height = roteiro.page_pixels(roteiro.new_page(), "A3", 300)
        self.assertEqual(width, 3508)
        self.assertEqual(height, 4961)
        width, height = roteiro.page_pixels(roteiro.new_page(), "tirinha", 300)
        self.assertEqual(width, 3508)
        self.assertEqual(height, 2480)

    def test_build_strip_panels(self):
        paineis = roteiro.build_strip_panels(3)
        self.assertEqual(len(paineis), 3)
        self.assertAlmostEqual(sum(p[2] for p in paineis) + 2 * 0.02, 0.9, delta=1e-9)
        for painel in paineis:
            self.assertAlmostEqual(painel[1], 0.05)
            self.assertAlmostEqual(painel[3], 0.9)
        self.assertAlmostEqual(paineis[0][0], 0.05)
        self.assertGreater(paineis[1][0], paineis[0][0])

    def test_build_strip_panels_limites(self):
        self.assertEqual(len(roteiro.build_strip_panels(0)), 1)
        self.assertEqual(len(roteiro.build_strip_panels(9)), 8)

    def test_wrap_text(self):
        lines = roteiro.wrap_text("uma frase um pouco maior para quebrar", 12)
        self.assertTrue(all(len(line) <= 12 for line in lines))
        self.assertEqual(" ".join(lines), "uma frase um pouco maior para quebrar")

    def test_parse_fraction(self):
        self.assertAlmostEqual(roteiro.parse_fraction("5%"), 0.05)
        self.assertAlmostEqual(roteiro.parse_fraction("0.05"), 0.05)
        self.assertAlmostEqual(roteiro.parse_fraction("50"), 0.45)


if __name__ == "__main__":
    unittest.main()
