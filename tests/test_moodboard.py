"""Testes do núcleo do moodboard (rodam fora do Krita)."""

import os
import shutil
import tempfile
import unittest

from hq_tools.modules.moodboard import core as mb


class TestGrade(unittest.TestCase):
    def test_largura_do_quadro(self):
        self.assertEqual(
            mb.LARGURA,
            mb.MARGEM * 2 + mb.COLUNAS * mb.CELULA + (mb.COLUNAS - 1) * mb.ESPACO,
        )

    def test_posicao_primeira_celula(self):
        self.assertEqual(mb.posicao(0), (mb.MARGEM, mb.MARGEM))

    def test_posicao_segunda_coluna(self):
        self.assertEqual(
            mb.posicao(1), (mb.MARGEM + mb.CELULA + mb.ESPACO, mb.MARGEM)
        )

    def test_posicao_segunda_linha(self):
        self.assertEqual(
            mb.posicao(mb.COLUNAS),
            (mb.MARGEM, mb.MARGEM + mb.CELULA + mb.ESPACO),
        )

    def test_encaixe_sem_ampliar(self):
        self.assertEqual(mb.encaixe(300, 200), 1.0)

    def test_encaixe_por_largura(self):
        self.assertEqual(mb.encaixe(1280, 640), 0.5)

    def test_encaixe_por_altura(self):
        self.assertEqual(mb.encaixe(320, 1280), 0.5)

    def test_encaixe_dimensao_invalida(self):
        self.assertEqual(mb.encaixe(0, 100), 1.0)

    def test_destino_centrado_na_celula(self):
        x, y, escala = mb.destino(0, 1280, 640)
        self.assertAlmostEqual(escala, 0.5)
        self.assertAlmostEqual(x, mb.MARGEM + (mb.CELULA - 640) / 2.0)
        self.assertAlmostEqual(y, mb.MARGEM + (mb.CELULA - 320) / 2.0)

    def test_altura_necessaria_minima(self):
        self.assertEqual(mb.altura_necessaria(1), mb.ALTURA)
        self.assertEqual(mb.altura_necessaria(mb.COLUNAS * mb.LINHAS_MINIMAS), mb.ALTURA)

    def test_altura_necessaria_cresce_em_linhas(self):
        total = mb.COLUNAS * mb.LINHAS_MINIMAS + 1
        self.assertEqual(
            mb.altura_necessaria(total),
            mb.MARGEM * 2
            + (mb.LINHAS_MINIMAS + 1) * mb.CELULA
            + mb.LINHAS_MINIMAS * mb.ESPACO,
        )


class TestEncaixeNaSelecao(unittest.TestCase):
    def test_cabe_pela_largura(self):
        x, y, escala = mb.encaixe_em(100, 200, 400, 400, 800, 400)
        self.assertAlmostEqual(escala, 0.5)
        self.assertAlmostEqual(x, 100)
        self.assertAlmostEqual(y, 200 + (400 - 200) / 2.0)

    def test_amplia_para_preencher(self):
        _, _, escala = mb.encaixe_em(0, 0, 200, 200, 100, 100)
        self.assertAlmostEqual(escala, 2.0)

    def test_caixa_invalida(self):
        self.assertEqual(mb.encaixe_em(10, 20, 0, 100, 50, 50), (10, 20, 1.0))


class TestXmlTransform(unittest.TestCase):
    def test_valores_no_xml(self):
        xml = mb.xml_transform(0.5, 300, 200)
        self.assertIn('<main id="tooltransformparams"/>', xml)
        self.assertIn('<transformedCenter type="pointf" x="300.000" y="200.000"/>', xml)
        self.assertIn('<scaleX value="0.500000" type="value"/>', xml)
        self.assertIn('<scaleY value="0.500000" type="value"/>', xml)
        self.assertIn('<originalCenter type="pointf" x="0" y="0"/>', xml)

    def test_elementos_validados_no_poc(self):
        xml = mb.xml_transform(1.0, 0, 0)
        for elemento in (
            "free_transform",
            "rotationCenterOffset",
            "keepAspectRatio",
            "flattenedPerspectiveTransform",
            "filterId",
        ):
            self.assertIn(elemento, xml)


class TestArquivos(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="moodboard-teste-")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_nome_arquivo(self):
        self.assertEqual(mb.nome_arquivo("Referência Ótima.PNG"), "referencia-otima.jpg")

    def test_caminho_referencia_sem_colisao(self):
        primeiro = mb.caminho_referencia(self.pasta, "ref.png")
        self.assertTrue(primeiro.endswith("ref.jpg"))
        open(primeiro, "wb").close()
        segundo = mb.caminho_referencia(self.pasta, "ref.png")
        self.assertTrue(segundo.endswith("ref-2.jpg"))

    def test_listar_referencias_ordena_e_filtra(self):
        for nome in ("b.jpg", "a.PNG", "nota.txt"):
            open(os.path.join(self.pasta, nome), "wb").close()
        nomes = [nome for nome, _ in mb.listar_referencias(self.pasta)]
        self.assertEqual(nomes, ["a", "b"])

    def test_listar_pasta_inexistente(self):
        self.assertEqual(mb.listar_referencias(os.path.join(self.pasta, "nada")), [])

    def test_apagar_referencia(self):
        caminho = os.path.join(self.pasta, "x.jpg")
        open(caminho, "wb").close()
        mb.apagar_referencia(caminho)
        self.assertFalse(os.path.exists(caminho))

    def test_apagar_recusa_outra_extensao(self):
        caminho = os.path.join(self.pasta, "x.txt")
        open(caminho, "wb").close()
        with self.assertRaises(ValueError):
            mb.apagar_referencia(caminho)

    def test_layout_ida_e_volta(self):
        open(os.path.join(self.pasta, "ref.jpg"), "wb").close()
        item = mb.item_de_layout("ref.jpg", 10.5, 20.25, 0.5, 1280, 640, "uuid-1")
        mb.salvar_layout(self.pasta, [item])
        itens = mb.carregar_layout(self.pasta)
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["arquivo"], "ref.jpg")
        self.assertEqual(itens[0]["camada"], "uuid-1")
        self.assertAlmostEqual(itens[0]["escala"], 0.5)

    def test_layout_ignora_arquivo_sumido(self):
        item = mb.item_de_layout("sumiu.jpg", 0, 0, 1.0, 10, 10)
        mb.salvar_layout(self.pasta, [item])
        self.assertEqual(mb.carregar_layout(self.pasta), [])

    def test_layout_corrompido_devolve_vazio(self):
        with open(mb.layout_path(self.pasta), "w", encoding="utf-8") as arquivo:
            arquivo.write("{isso nao e json")
        self.assertEqual(mb.carregar_layout(self.pasta), [])

    def test_layout_sem_temporario(self):
        mb.salvar_layout(self.pasta, [])
        self.assertFalse(os.path.exists(mb.layout_path(self.pasta) + ".tmp"))


if __name__ == "__main__":
    unittest.main()
