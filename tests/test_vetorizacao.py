"""Testes do vetorizador de balões e do lote desenhado pelo autor.

Duas partes:

1. ``TestVetorizador`` roda ``scripts/vetorizar-baloes.py`` de verdade com uma
   imagem de teste e confere o contrato do script (dois grupos, cauda aberta,
   erros legíveis). É a ferramenta que sobra para vetorizar pranchas novas.
2. ``TestLoteDoAutor`` trava o lote entregue em ``Referencias/
   baloes-vetorizados``: 22 SVGs desenhados à mão (02 e 03/10/2026), que
   substituíram o lote gerado de 29/09. O contrato aqui é o que o Krita exige
   para importar (XML válido, viewBox, paths com traço, sem texto e sem
   imagem externa) mais a sincronia entre a pasta, o ``lote.json`` e o
   ``INDEX.md``.

``Referencias/`` é material de trabalho local do autor e ficou fora do
repositório (`.gitignore`): essas duas classes pulam quando a pasta não existe
(é o caso do CI), e rodam inteiras na máquina do autor, onde o kit fica.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(RAIZ, "scripts")
VETORIZADOR = os.path.join(SCRIPTS, "vetorizar-baloes.py")
LOTE = os.path.join(RAIZ, "Referencias", "baloes-vetorizados")
ESPACO_SVG = "{http://www.w3.org/2000/svg}"
TIPO_POR_PREFIXO = {
    "Fala": "fala",
    "Pensa": "pensamento",
    "Ono": "onomatopeia",
    "Cauda": "cauda",
}


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


@unittest.skipUnless(os.path.isdir(LOTE), "lote de vetores fora do repositório")
class TestLoteDoAutor(unittest.TestCase):
    """O lote entregue (desenho do autor) tem que continuar importável."""

    def svgs(self):
        return sorted(n for n in os.listdir(LOTE) if n.endswith(".svg"))

    def manifesto(self):
        with open(os.path.join(LOTE, "lote.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def test_lote_nao_esta_vazio(self):
        self.assertTrue(self.svgs(), "nenhum SVG no lote")

    def test_nomes_seguem_a_convencao(self):
        # Tipo_Nome_NN_.svg, com o tipo no começo (Fala/Pensa/Ono/Cauda).
        for nome in self.svgs():
            with self.subTest(svg=nome):
                prefixo = nome.split("_", 1)[0]
                self.assertIn(
                    prefixo, TIPO_POR_PREFIXO,
                    "prefixo fora do padrão (Fala_/Pensa_/Ono_/Cauda_)",
                )
                self.assertRegex(
                    nome, r"^[A-Za-z]+_[A-Za-z]+_\d\d_\.svg$",
                    "nome fora do padrão Tipo_Nome_NN_.svg",
                )

    def test_todos_sao_svg_importavel(self):
        for nome in self.svgs():
            with self.subTest(svg=nome):
                caminho = os.path.join(LOTE, nome)
                with open(caminho, encoding="utf-8") as handle:
                    bruto = handle.read()
                # Parsear é o teste que importa: o Krita importa o SVG com
                # addShapesFromSvg, e um XML quebrado vira "nada importado"
                # sem dizer qual linha foi.
                raiz = ElementTree.parse(caminho).getroot()
                self.assertEqual(ESPACO_SVG + "svg", raiz.tag)
                self.assertTrue(raiz.get("viewBox"), "sem viewBox: o Krita não escala")
                paths = raiz.findall(".//" + ESPACO_SVG + "path")
                self.assertTrue(paths, "sem path")
                for indice, path in enumerate(paths):
                    with self.subTest(path=indice):
                        d = (path.get("d") or "").strip()
                        # O Inkscape escreve comandos relativos minúsculos (m).
                        self.assertEqual("m", d[:1].lower(), "path sem comando inicial")
                        self.assertGreater(len(d), 20, "path vazio")
                        estilo = path.get("style") or ""
                        self.assertIn(
                            "stroke:#000000", estilo, "path sem traço preto"
                        )
                self.assertFalse(
                    raiz.findall(".//" + ESPACO_SVG + "text"),
                    "tem <text>: o kit é sem texto",
                )
                self.assertNotIn("<image", bruto, "SVG com imagem embutida")
                self.assertNotIn("href", bruto, "SVG com referência externa")

    def test_manifesto_cobre_o_lote(self):
        itens = self.manifesto()["itens"]
        self.assertEqual(
            set(self.svgs()), set(itens),
            "lote.json e a pasta divergem",
        )
        for nome, dados in itens.items():
            with self.subTest(svg=nome):
                self.assertIn(
                    dados["tipo"], set(TIPO_POR_PREFIXO.values()),
                    "tipo desconhecido",
                )
                self.assertTrue(dados["descricao"].strip(), "descrição vazia")

    def test_prefixo_bate_com_o_tipo_do_manifesto(self):
        for nome, dados in self.manifesto()["itens"].items():
            with self.subTest(svg=nome):
                prefixo = nome.split("_", 1)[0]
                self.assertEqual(TIPO_POR_PREFIXO[prefixo], dados["tipo"])

    def test_indice_lista_todos_os_svgs(self):
        with open(os.path.join(LOTE, "INDEX.md"), encoding="utf-8") as handle:
            indice = handle.read()
        for nome in self.svgs():
            self.assertIn(nome, indice, "{0} não está no INDEX.md".format(nome))


@unittest.skipUnless(os.path.isdir(LOTE), "lote de vetores fora do repositório")
class TestAmostrasEmbarcadas(unittest.TestCase):
    """O kit do autor e o que o plugin copia na primeira execução não divergem."""

    AMOSTRAS_BALOES = os.path.join(RAIZ, "hq_tools", "modules", "balloons", "samples")
    AMOSTRAS_ONO = os.path.join(
        RAIZ, "hq_tools", "modules", "onomatopeias", "samples"
    )

    def kit(self, prefixos):
        return {
            nome for nome in os.listdir(LOTE)
            if nome.endswith(".svg") and nome.split("_", 1)[0] in prefixos
        }

    def iguais(self, nome, pasta):
        with open(os.path.join(LOTE, nome), "rb") as a:
            with open(os.path.join(pasta, nome), "rb") as b:
                self.assertEqual(a.read(), b.read(), nome + " divergiu do kit")

    def test_amostras_de_baloes_sao_o_kit_do_autor(self):
        kit = self.kit({"Cauda", "Fala", "Pensa"})
        self.assertTrue(kit)
        amostras = {
            nome for nome in os.listdir(self.AMOSTRAS_BALOES) if nome.endswith(".svg")
        }
        self.assertEqual(
            kit, amostras,
            "as amostras de balão têm que ser exatamente o kit do autor",
        )
        for nome in sorted(kit):
            with self.subTest(svg=nome):
                self.iguais(nome, self.AMOSTRAS_BALOES)

    def test_amostras_de_onomatopeias_sao_o_kit_do_autor(self):
        kit = self.kit({"Ono"})
        self.assertTrue(kit)
        amostras = {
            nome for nome in os.listdir(self.AMOSTRAS_ONO) if nome.endswith(".svg")
        }
        self.assertEqual(
            kit, amostras,
            "as amostras de onomatopeia têm que ser exatamente o kit do autor",
        )
        for nome in sorted(kit):
            with self.subTest(svg=nome):
                self.iguais(nome, self.AMOSTRAS_ONO)


if __name__ == "__main__":
    unittest.main()
