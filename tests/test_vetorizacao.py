"""Testes do script de vetorização de balões (fora do Krita).

O ponto principal é a reprodutibilidade: o lote em
``Referencias/baloes-vetorizados`` foi gerado por este script, e uma refactor
que muda o pescoço ou a cauda sem querer entrega um resultado diferente do
que o autor vai revisar na tela. O teste roda o script de verdade e compara
byte a byte com o que está no repositório.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(RAIZ, "scripts")
VETORIZADOR = os.path.join(SCRIPTS, "vetorizar-baloes.py")
VETORIZADOR_LOTE = os.path.join(SCRIPTS, "vetorizar-lote.py")
LOTE = os.path.join(RAIZ, "Referencias", "baloes-vetorizados")


def tem_dependencias():
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    return True


PULA_SEM_DEPENDENCIAS = unittest.skipUnless(
    tem_dependencias(), "o script precisa de numpy e Pillow (fora da suíte do plugin)"
)


@unittest.skipUnless(os.path.isfile(VETORIZADOR), "script fora do repositório")
class TestVetorizador(unittest.TestCase):
    def rodar(self, argumentos, entrada=None):
        comando = [sys.executable, VETORIZADOR] + argumentos
        return subprocess.run(comando, capture_output=True, text=True, input=entrada)

    def arquivo_valido(self):
        from PIL import Image, ImageDraw

        pasta = tempfile.mkdtemp(prefix="hq_tools_ref_")
        caminho = os.path.join(pasta, "ref.png")
        imagem = Image.new("L", (240, 200), 255)
        desenho = ImageDraw.Draw(imagem)
        # Balão com pescoço: corpo em cima, cauda em baixo.
        desenho.ellipse((50, 30, 190, 120), outline=0, width=5)
        desenho.polygon(
            [(100, 118), (120, 118), (150, 180), (128, 168)], outline=0, width=5
        )
        imagem.save(caminho)
        return caminho

    @PULA_SEM_DEPENDENCIAS
    def test_gera_svg_com_dois_grupos(self):
        imagem = self.arquivo_valido()
        saida = os.path.join(os.path.dirname(imagem), "balao.svg")
        resultado = self.rodar([imagem, "50", "30", "140", "90", saida])
        self.assertEqual(0, resultado.returncode, resultado.stderr)
        with open(saida, encoding="utf-8") as handle:
            svg = handle.read()
        self.assertIn('<g id="balao">', svg)
        self.assertIn('<g id="cauda">', svg)
        # A cauda é desenhada sem fechar o traço, para o autor poder unir.
        cauda = svg.split('<g id="cauda">')[1].split("</g>")[0]
        self.assertNotIn(" Z", cauda)

    @PULA_SEM_DEPENDENCIAS
    def test_tamanho_saida_e_em_pontos(self):
        imagem = self.arquivo_valido()
        saida = os.path.join(os.path.dirname(imagem), "balao.svg")
        self.rodar([imagem, "50", "30", "140", "90", saida, "--tamanho-pt", "150"])
        with open(saida, encoding="utf-8") as handle:
            svg = handle.read()
        self.assertIn("width=\"150.00pt\"", svg)

    @PULA_SEM_DEPENDENCIAS
    def test_imagem_inexistente_da_erro_legivel(self):
        resultado = self.rodar(["/nao/existe.png", "0", "0", "10", "10", "/tmp/x.svg"])
        self.assertNotEqual(0, resultado.returncode)
        # Sem traceback: o autor precisa saber o que corrigir.
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertIn("não encontrei", resultado.stderr.lower())

    @PULA_SEM_DEPENDENCIAS
    def test_corte_invalido_da_erro_legivel(self):
        imagem = self.arquivo_valido()
        resultado = self.rodar(
            [imagem, "50", "30", "140", "90", os.path.join(os.path.dirname(imagem), "b.svg"),
             "--corte", "1,2,3"]
        )
        self.assertNotEqual(0, resultado.returncode)
        self.assertIn("I,J", resultado.stderr)


@unittest.skipUnless(
    os.path.isfile(VETORIZADOR_LOTE) and os.path.isdir(LOTE),
    "lote de vetores fora do repositório",
)
class TestLoteEntregue(unittest.TestCase):
    """O lote versionado tem que continuar sendo reproduzível pelo script."""

    def trabalhos(self):
        # O nome do arquivo tem hífen, então não dá para importar direto.
        especificacao = importlib.util.spec_from_file_location(
            "vetorizar_lote", VETORIZADOR_LOTE
        )
        modulo = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(modulo)
        return modulo.TRABALHOS

    def test_todo_svg_do_lote_e_reproduzivel(self):
        if not tem_dependencias():
            self.skipTest("o script precisa de numpy e Pillow")
        trabalhos = self.trabalhos()
        with tempfile.TemporaryDirectory(prefix="hq_tools_lote_") as saida:
            subprocess.run(
                [sys.executable, VETORIZADOR_LOTE, "--saida", saida],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(trabalhos)
            for nome in trabalhos:
                with self.subTest(balao=nome):
                    gerado = os.path.join(saida, nome + ".svg")
                    self.assertTrue(os.path.isfile(gerado), gerado)
                    with open(gerado, encoding="utf-8") as a:
                        with open(os.path.join(LOTE, nome + ".svg"), encoding="utf-8") as b:
                            self.assertEqual(
                                a.read(),
                                b.read(),
                                "{0} mudou em relação ao lote versionado".format(nome),
                            )

    def test_todos_os_svgs_do_lote_sao_svg_importavel(self):
        nomes = [n for n in os.listdir(LOTE) if n.endswith(".svg")]
        self.assertTrue(nomes, "nenhum SVG no lote")
        espaco = "{http://www.w3.org/2000/svg}"
        for nome in nomes:
            with self.subTest(svg=nome):
                caminho = os.path.join(LOTE, nome)
                # Parsear é o teste que importa: o Krita importa o SVG com
                # addShapesFromSvg, e um XML quebrado vira "nada importado"
                # sem dizer qual linha foi.
                arvore = ElementTree.parse(caminho)
                raiz = arvore.getroot()
                self.assertEqual(espaco + "svg", raiz.tag)
                self.assertTrue(raiz.get("viewBox"), "sem viewBox: o Krita não escala")
                # O 05a é vetor do autor (tem camadas do Inkscape); os outros
                # saem do script e têm os dois grupos com nome.
                if nome not in self.trabalhos():
                    self.assertTrue(len(raiz), nome)
                    continue
                grupos = {g.get("id"): g for g in raiz.findall(espaco + "g")}
                self.assertEqual({"balao", "cauda"}, set(grupos), nome)
                for identificador, grupo in grupos.items():
                    caminhos = grupo.findall(espaco + "path")
                    self.assertEqual(1, len(caminhos), "{0}/{1}".format(nome, identificador))
                    d = caminhos[0].get("d") or ""
                    self.assertTrue(d.startswith("M"), nome)
                    self.assertTrue(len(d) > 20, "path vazio em " + nome)
                    self.assertTrue(caminhos[0].get("stroke-width"), nome)

    def test_indice_lista_todos_os_svgs(self):
        indice = os.path.join(LOTE, "INDEX.md")
        if not os.path.isfile(indice):
            self.skipTest("sem INDEX.md no lote")
        with open(indice, encoding="utf-8") as handle:
            texto = handle.read()
        for nome in os.listdir(LOTE):
            if nome.endswith(".svg"):
                self.assertIn(nome, texto, "{0} não está no INDEX.md".format(nome))


if __name__ == "__main__":
    unittest.main()
