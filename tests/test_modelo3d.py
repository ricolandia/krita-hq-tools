"""Testes do visualizador 3D (núcleo puro, sem Blender e sem Krita).

O manequim sintético de 2 ossos é o contrato do skinning: um osso raiz na
origem e um filho a 1 m de altura, com vértices presos a cada um. O modelo real
(``low_poly_krita.json``) entra como teste de integração: se o exportador mudar
o formato, o teste acusa.
"""

import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from hq_tools.core import modelo3d

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_REAL = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "modelos", "low_poly_krita.json"
)


def translacao(x, y, z):
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def manequim():
    return {
        "formato": "hq_tools.modelo3d",
        "versao": 1,
        "nome": "manequim",
        "cor_padrao": "#cccccc",
        "ossos": [
            {"nome": "raiz", "pai": None, "matriz": modelo3d.identidade()},
            {"nome": "filho", "pai": 0, "matriz": translacao(0.0, 0.0, 1.0)},
        ],
        "vertices": [
            (0.0, 0.0, 0.0),
            (0.0, 0.1, 1.0),
            (0.1, 0.0, 1.0),
        ],
        "pesos": [[[0, 1.0]], [[1, 1.0]], [[1, 1.0]]],
        "faces": [[0, 1, 2]],
    }


def triangulo_visivel():
    dados = manequim()
    dados["vertices"] = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)]
    dados["pesos"] = [[[0, 1.0]], [[0, 1.0]], [[0, 1.0]]]
    dados["faces"] = [[0, 1, 2]]
    return dados


class TestMatematica(unittest.TestCase):
    def test_inversa_afim(self):
        matriz = translacao(1.0, 2.0, 3.0)
        produto = modelo3d.multiplicar(matriz, modelo3d.inversa_afim(matriz))
        for esperado, valor in zip(modelo3d.identidade(), produto):
            self.assertAlmostEqual(esperado, valor, places=9)

    def test_rotacao_euler_ordem_xyz(self):
        direto = modelo3d.rotacao_euler((30.0, 0.0, 0.0))
        esperado = modelo3d.rotacao_x(30.0)
        for a, b in zip(direto, esperado):
            self.assertAlmostEqual(a, b, places=9)


class TestManequim(unittest.TestCase):
    def setUp(self):
        self.modelo = modelo3d.Modelo(manequim())

    def test_carregar_contagens(self):
        self.assertEqual(len(self.modelo.ossos), 2)
        self.assertEqual(len(self.modelo.vertices), 3)
        self.assertEqual(len(self.modelo.faces), 1)
        self.assertEqual(self.modelo.nomes_dos_ossos(), ["raiz", "filho"])

    def test_pose_rotaciona_em_torno_da_cabeca_do_osso(self):
        vertices = self.modelo.vertices_em_pose({"filho": (90.0, 0.0, 0.0)})
        x, y, z = vertices[1]
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)
        self.assertAlmostEqual(z, 1.1, places=6)
        self.assertAlmostEqual(vertices[0], (0.0, 0.0, 0.0), places=6)

    def test_pose_na_raiz_move_o_filho_junto(self):
        vertices = self.modelo.vertices_em_pose({"raiz": (0.0, 0.0, 90.0)})
        x, y, z = vertices[1]
        self.assertAlmostEqual(x, -0.1, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)
        self.assertAlmostEqual(z, 1.0, places=6)

    def test_projecao_z_para_cima(self):
        tela = self.modelo.vertices_em_tela(largura=700, altura=700)
        self.assertLess(tela[1][1], tela[0][1])

    def test_svg_face_visivel(self):
        modelo = modelo3d.Modelo(triangulo_visivel())
        svg = modelo.renderizar(largura=400, altura=400)
        raiz = ET.fromstring(svg)
        poligonos = raiz.findall("{http://www.w3.org/2000/svg}polygon")
        self.assertEqual(len(poligonos), 1)

    def test_svg_face_de_costas_aparece_por_padrao(self):
        dados = triangulo_visivel()
        dados["faces"] = [[0, 2, 1]]
        modelo = modelo3d.Modelo(dados)
        svg = modelo.renderizar(largura=400, altura=400)
        raiz = ET.fromstring(svg)
        self.assertEqual(len(raiz.findall("{http://www.w3.org/2000/svg}polygon")), 1)

    def test_svg_face_de_costas_some_com_cull(self):
        dados = triangulo_visivel()
        dados["faces"] = [[0, 2, 1]]
        modelo = modelo3d.Modelo(dados)
        svg = modelo.renderizar(largura=400, altura=400, cull=True)
        raiz = ET.fromstring(svg)
        self.assertEqual(raiz.findall("{http://www.w3.org/2000/svg}polygon"), [])

    def test_painter_desenha_o_longe_primeiro(self):
        dados = triangulo_visivel()
        dados["vertices"] = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0),
            (10.0, 1.0, 0.0), (11.0, 1.0, 0.0), (10.0, 1.0, 1.0),
        ]
        dados["pesos"] = [[[0, 1.0]]] * 6
        dados["faces"] = [[0, 1, 2], [3, 4, 5]]
        modelo = modelo3d.Modelo(dados)
        svg = modelo.renderizar(largura=400, altura=400)
        raiz = ET.fromstring(svg)
        poligonos = raiz.findall("{http://www.w3.org/2000/svg}polygon")
        self.assertEqual(len(poligonos), 2)
        primeiro_x = float(poligonos[0].get("points").split()[0].split(",")[0])
        self.assertGreater(primeiro_x, 5.0)

    def test_formato_desconhecido(self):
        dados = manequim()
        dados["formato"] = "outro"
        with self.assertRaises(ValueError):
            modelo3d.Modelo(dados)

    def test_versao_futura(self):
        dados = manequim()
        dados["versao"] = modelo3d.VERSAO + 1
        with self.assertRaises(ValueError):
            modelo3d.Modelo(dados)

    def test_carregar_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "manequim.json")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump(manequim(), arquivo)
            modelo = modelo3d.Modelo.carregar(caminho)
            self.assertEqual(modelo.nome, "manequim")


class TestEixosSemanticos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(MODELO_REAL):
            raise unittest.SkipTest("low_poly_krita.json não está no repositório")
        cls.modelo = modelo3d.Modelo.carregar(MODELO_REAL)

    def _vertice_da_coxa(self):
        alvo = next(
            indice
            for indice, osso in enumerate(self.modelo.ossos)
            if osso["nome"] == "thigh_stretch.l"
        )
        return max(
            ((indice, dict(pares).get(alvo, 0.0)) for indice, pares in enumerate(self.modelo.pesos)),
            key=lambda item: item[1],
        )[0]

    def test_mapa_da_coxa(self):
        mapa = modelo3d.eixos_semanticos(self.modelo.osso_por_nome["thigh_stretch.l"])
        self.assertEqual(mapa["dobrar"][0], "z")
        self.assertEqual(mapa["abrir"][0], "x")
        self.assertEqual(mapa["girar"], ("y", 1))

    def test_mapa_da_cabeca(self):
        mapa = modelo3d.eixos_semanticos(self.modelo.osso_por_nome["head.x"])
        self.assertEqual(mapa["dobrar"][0], "x")
        self.assertEqual(mapa["abrir"][0], "z")

    def test_dobrar_positivo_vai_para_frente(self):
        indice = self._vertice_da_coxa()
        repouso = self.modelo.vertices_em_pose()[indice]
        rotacoes = self.modelo.aplicar_semantica(
            {"thigh_stretch.l": {"dobrar": 40.0}}
        )
        posado = self.modelo.vertices_em_pose(rotacoes)[indice]
        self.assertLess(posado[1], repouso[1] - 0.02)

    def test_abrir_positivo_vai_para_fora(self):
        indice = self._vertice_da_coxa()
        repouso = self.modelo.vertices_em_pose()[indice]
        rotacoes = self.modelo.aplicar_semantica(
            {"thigh_stretch.l": {"abrir": 40.0}}
        )
        posado = self.modelo.vertices_em_pose(rotacoes)[indice]
        self.assertGreater(posado[0], repouso[0] + 0.02)

    def test_osso_desconhecido_e_ignorado(self):
        self.assertEqual(
            self.modelo.aplicar_semantica({"nao_existe": {"dobrar": 30.0}}), {}
        )


class TestModeloReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(MODELO_REAL):
            raise unittest.SkipTest("low_poly_krita.json não está no repositório")
        cls.modelo = modelo3d.Modelo.carregar(MODELO_REAL)

    def test_estrutura(self):
        self.assertEqual(len(self.modelo.ossos), 68)
        self.assertEqual(len(self.modelo.vertices), 1591)
        self.assertEqual(len(self.modelo.faces), 1570)
        for pares in self.modelo.pesos:
            self.assertTrue(pares)
            self.assertLessEqual(len(pares), 4)
            self.assertAlmostEqual(sum(peso for _, peso in pares), 1.0, places=4)

    def test_renderiza_com_muitas_faces(self):
        svg = self.modelo.renderizar(largura=500, altura=500)
        raiz = ET.fromstring(svg)
        poligonos = raiz.findall("{http://www.w3.org/2000/svg}polygon")
        self.assertGreater(len(poligonos), 500)
        self.assertLessEqual(len(poligonos), 2 * len(self.modelo.faces))

    def test_pose_move_vertices(self):
        repouso = self.modelo.vertices_em_pose()
        pose = self.modelo.vertices_em_pose({"head.x": (0.0, 0.0, 30.0)})
        diferente = sum(
            1 for a, b in zip(repouso, pose)
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) > 1e-6
        )
        self.assertGreater(diferente, 0)


if __name__ == "__main__":
    unittest.main()
