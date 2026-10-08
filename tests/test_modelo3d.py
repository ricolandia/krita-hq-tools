"""Testes do visualizador 3D (núcleo puro, sem Blender e sem Krita).

O manequim sintético de 2 ossos é o contrato do skinning: um osso raiz na
origem e um filho a 1 m de altura, com vértices presos a cada um. O modelo real
(``homem.json`` e ``mulher.json``) entra como teste de integração: se o
exportador mudar o formato, o teste acusa.
"""

import json
import math
import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

from hq_tools.core import modelo3d

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_REAL = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "modelos", "homem.json"
)
MODELO_MULHER = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "modelos", "mulher.json"
)
POSE_IDLE = os.path.join(
    RAIZ, "hq_tools", "modules", "viewer3d", "poses", "corpo", "idle.json"
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

    def test_pan_desloca_a_tela(self):
        base = self.modelo.vertices_em_tela(largura=700, altura=700)
        movido = self.modelo.vertices_em_tela(
            largura=700, altura=700, pan_x=50.0, pan_y=-30.0
        )
        self.assertAlmostEqual(movido[0][0] - base[0][0], 50.0, places=6)
        self.assertAlmostEqual(movido[0][1] - base[0][1], -30.0, places=6)

    def test_zoom_escala_a_partir_do_centro(self):
        base = self.modelo.vertices_em_tela(largura=700, altura=700)
        ampliado = self.modelo.vertices_em_tela(largura=700, altura=700, zoom=2.0)

        def distancia(ponto):
            return math.hypot(ponto[0] - 350.0, ponto[1] - 350.0)

        indice = max(range(len(base)), key=lambda i: distancia(base[i]))
        self.assertAlmostEqual(
            distancia(ampliado[indice]), 2.0 * distancia(base[indice]), places=4
        )

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

    def test_svg_chapado_e_um_path(self):
        modelo = modelo3d.Modelo(triangulo_visivel())
        svg = modelo.renderizar(largura=400, altura=400, estilo="chapado")
        raiz = ET.fromstring(svg)
        caminhos = raiz.findall("{http://www.w3.org/2000/svg}path")
        self.assertEqual(len(caminhos), 1)
        self.assertEqual(raiz.findall("{http://www.w3.org/2000/svg}polygon"), [])
        self.assertIn("M", caminhos[0].get("d"))

    def test_chapado_normaliza_o_winding(self):
        dados = triangulo_visivel()
        dados["vertices"] = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0),
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0),
        ]
        dados["pesos"] = [[[0, 1.0]]] * 6
        dados["faces"] = [[0, 1, 2], [5, 4, 3]]
        modelo = modelo3d.Modelo(dados)
        svg = modelo.renderizar(largura=400, altura=400, estilo="chapado")
        raiz = ET.fromstring(svg)
        caminho = raiz.find("{http://www.w3.org/2000/svg}path").get("d")
        numeros = [float(valor) for valor in re.findall(r"-?\d+(?:\.\d+)?", caminho)]
        areas = []
        for inicio in range(0, len(numeros), 6):
            x0, y0, x1, y1, x2, y2 = numeros[inicio:inicio + 6]
            areas.append((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
        self.assertTrue(areas)
        self.assertTrue(all(area >= 0 for area in areas))

    def test_svg_contorno_sem_preenchimento(self):
        modelo = modelo3d.Modelo(triangulo_visivel())
        svg = modelo.renderizar(largura=400, altura=400, estilo="contorno")
        raiz = ET.fromstring(svg)
        caminhos = raiz.findall("{http://www.w3.org/2000/svg}path")
        self.assertEqual(len(caminhos), 1)
        self.assertEqual(caminhos[0].get("fill"), "none")
        self.assertIn("stroke", caminhos[0].attrib)
        self.assertEqual(caminhos[0].get("d").count("M"), 3)

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

    def test_carregar_pose(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "pose.json")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump({
                    "formato": "hq_tools.pose3d",
                    "versao": 1,
                    "nome": "teste",
                    "ossos": {"filho": {"dobrar": 10.0}},
                }, arquivo)
            pose = modelo3d.carregar_pose(caminho)
            self.assertEqual(pose["nome"], "teste")

    def test_carregar_pose_formato_errado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "pose.json")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump({"formato": "outro", "versao": 1, "ossos": {}}, arquivo)
            with self.assertRaises(ValueError):
                modelo3d.carregar_pose(caminho)


class TestEspelhoDePose(unittest.TestCase):
    """As poses de mão são da mão direita; o espelho as leva para a esquerda."""

    def test_espelhar_troca_de_lado_e_nega_o_giro(self):
        resultado = modelo3d.espelhar({"arm.r": {"dobrar": 5.0, "girar": 10.0}})
        self.assertEqual(resultado, {"arm.l": {"dobrar": 5.0, "girar": -10.0}})

    def test_espelhar_osso_sem_lado_fica_igual(self):
        resultado = modelo3d.espelhar({"spine_01.x": {"dobrar": 2.0}})
        self.assertEqual(resultado, {"spine_01.x": {"dobrar": 2.0}})

    def test_espelhar_confere_com_o_idle_do_repositorio(self):
        # No Idle real, os lados só diferem no sinal de "girar": espelhar os
        # ossos .r tem que reproduzir os .l do próprio arquivo.
        if not os.path.isfile(POSE_IDLE):
            self.skipTest("pose idle não está no repositório")
        ossos = modelo3d.carregar_pose(POSE_IDLE)["ossos"]
        direita = {
            nome: valores for nome, valores in ossos.items() if nome.endswith(".r")
        }
        espelhado = modelo3d.espelhar(direita)
        self.assertTrue(espelhado)
        for nome, valores in espelhado.items():
            self.assertIn(nome, ossos, nome)
            for chave, valor in valores.items():
                self.assertAlmostEqual(
                    valor, ossos[nome].get(chave, 0.0), places=1, msg=nome
                )

    def test_pose_maos_por_lado(self):
        valores = {"hand.r": {"girar": 10.0}}
        self.assertEqual(
            modelo3d.pose_maos_por_lado(valores, modelo3d.LADO_DIREITA), valores
        )
        self.assertEqual(
            modelo3d.pose_maos_por_lado(valores, modelo3d.LADO_ESQUERDA),
            {"hand.l": {"girar": -10.0}},
        )
        self.assertEqual(
            modelo3d.pose_maos_por_lado(valores, modelo3d.LADO_AMBAS),
            {"hand.r": {"girar": 10.0}, "hand.l": {"girar": -10.0}},
        )

    def test_pose_maos_com_os_dois_lados_respeita_o_seletor(self):
        # As poses antigas guardavam os dois lados; o seletor tem que mandar
        # (a esquerda do arquivo é descartada antes de aplicar o lado).
        misto = {"hand.r": {"girar": 10.0}, "hand.l": {"girar": 99.0}}
        self.assertEqual(
            modelo3d.pose_maos_por_lado(misto, modelo3d.LADO_DIREITA),
            {"hand.r": {"girar": 10.0}},
        )
        self.assertEqual(
            modelo3d.pose_maos_por_lado(misto, modelo3d.LADO_ESQUERDA),
            {"hand.l": {"girar": -10.0}},
        )
        self.assertEqual(
            modelo3d.pose_maos_por_lado(misto, modelo3d.LADO_AMBAS),
            {"hand.r": {"girar": 10.0}, "hand.l": {"girar": -10.0}},
        )

    def test_combinar_poses_corpo_com_as_duas_maos(self):
        corpo = {"spine_01.x": {"dobrar": 5.0}, "arm_stretch.r": {"dobrar": 10.0}}
        direita = {"hand.r": {"dobrar": 20.0}, "index1.r": {"dobrar": 30.0}}
        esquerda = {"hand.r": {"girar": 15.0}}
        combinado = modelo3d.combinar_poses(corpo, direita, esquerda)
        self.assertEqual(combinado["spine_01.x"], {"dobrar": 5.0})
        self.assertEqual(combinado["arm_stretch.r"], {"dobrar": 10.0})
        self.assertEqual(combinado["hand.r"], {"dobrar": 20.0})
        self.assertEqual(combinado["index1.r"], {"dobrar": 30.0})
        self.assertEqual(combinado["hand.l"], {"girar": -15.0})

    def test_combinar_poses_mao_vazia_nao_mexe_na_outra(self):
        # Regressão: mudar a pose do corpo não pode devolver a mão ao repouso
        # (as poses de corpo não têm ossos de mão).
        corpo = {"arm_stretch.l": {"dobrar": 7.0}}
        direita = {"hand.r": {"dobrar": 20.0}}
        combinado = modelo3d.combinar_poses(corpo, direita, None)
        self.assertEqual(combinado["hand.r"], {"dobrar": 20.0})
        self.assertNotIn("hand.l", combinado)
        self.assertEqual(combinado["arm_stretch.l"], {"dobrar": 7.0})
        self.assertEqual(
            modelo3d.combinar_poses(corpo, direita, None),
            modelo3d.combinar_poses(corpo, direita, {}),
        )

    def test_combinar_poses_com_arquivos_do_repositorio(self):
        pasta = os.path.join(
            RAIZ, "hq_tools", "modules", "viewer3d", "poses", "maos"
        )
        direita = modelo3d.carregar_pose(os.path.join(pasta, "joinha.json"))["ossos"]
        esquerda = modelo3d.carregar_pose(os.path.join(pasta, "fechada.json"))["ossos"]
        combinado = modelo3d.combinar_poses({}, direita, esquerda)
        self.assertIn("index1.r", combinado)
        self.assertIn("hand.l", combinado)
        self.assertNotIn("hand.r", combinado)
        self.assertEqual(
            combinado["hand.l"],
            modelo3d.pose_maos_por_lado(
                esquerda, modelo3d.LADO_ESQUERDA
            )["hand.l"],
        )

    def test_modelos_do_repositorio_cobrem_as_poses(self):
        from hq_tools.core.paths import VIEWER3D_MODELOS

        usados = set()
        pasta = os.path.join(RAIZ, "hq_tools", "modules", "viewer3d", "poses")
        for parte in ("corpo", "maos"):
            for nome in sorted(os.listdir(os.path.join(pasta, parte))):
                if nome.endswith(".json"):
                    usados |= set(
                        modelo3d.carregar_pose(os.path.join(pasta, parte, nome))["ossos"].keys()
                    )
        self.assertTrue(usados)
        for _, _, caminho in VIEWER3D_MODELOS:
            modelo = modelo3d.Modelo.carregar(caminho)
            self.assertTrue(modelo.vertices, caminho)
            self.assertTrue(modelo.faces, caminho)
            self.assertTrue(all(pesos for pesos in modelo.pesos), "vértice sem peso em " + caminho)
            faltando = sorted(osso for osso in usados if osso not in modelo.osso_por_nome)
            self.assertEqual(faltando, [], "%s sem os ossos: %s" % (caminho, faltando))

    def test_substituir_mao_preserva_o_resto(self):
        semantica = {
            "spine_01.x": {"dobrar": 5.0},
            "arm_stretch.r": {"dobrar": 10.0},
            "hand.r": {"dobrar": 20.0},
            "hand.l": {"girar": -15.0},
            "index1.l": {"dobrar": 30.0},
        }
        nova = modelo3d.substituir_mao(
            semantica, {"hand.r": {"girar": 40.0}}, modelo3d.LADO_DIREITA
        )
        self.assertEqual(nova["spine_01.x"], {"dobrar": 5.0})
        self.assertEqual(nova["arm_stretch.r"], {"dobrar": 10.0})
        self.assertEqual(nova["hand.r"], {"girar": 40.0})
        self.assertEqual(nova["hand.l"], {"girar": -15.0})
        self.assertEqual(nova["index1.l"], {"dobrar": 30.0})

    def test_substituir_mao_remove_o_que_a_nova_nao_tem(self):
        semantica = {
            "hand.r": {"dobrar": 20.0},
            "index1.r": {"dobrar": 30.0},
            "hand.l": {"girar": 1.0},
        }
        nova = modelo3d.substituir_mao(
            semantica, {"thumb1.r": {"abrir": 5.0}}, modelo3d.LADO_DIREITA
        )
        self.assertNotIn("hand.r", nova)
        self.assertNotIn("index1.r", nova)
        self.assertEqual(nova["thumb1.r"], {"abrir": 5.0})
        self.assertEqual(nova["hand.l"], {"girar": 1.0})

    def test_substituir_mao_esquerda_espelha(self):
        nova = modelo3d.substituir_mao(
            {}, {"hand.r": {"girar": 10.0}}, modelo3d.LADO_ESQUERDA
        )
        self.assertEqual(nova, {"hand.l": {"girar": -10.0}})

    def test_substituir_corpo_preserva_as_maos(self):
        semantica = {
            "spine_01.x": {"dobrar": 5.0},
            "arm_stretch.r": {"dobrar": 10.0},
            "hand.r": {"dobrar": 20.0},
        }
        nova = modelo3d.substituir_corpo(semantica, {"head.x": {"girar": 30.0}})
        self.assertEqual(nova["head.x"], {"girar": 30.0})
        self.assertEqual(nova["hand.r"], {"dobrar": 20.0})
        self.assertNotIn("spine_01.x", nova)
        self.assertNotIn("arm_stretch.r", nova)

    def test_osso_de_mao(self):
        self.assertTrue(modelo3d.osso_de_mao("hand.r"))
        self.assertTrue(modelo3d.osso_de_mao("index1.l"))
        self.assertFalse(modelo3d.osso_de_mao("arm_stretch.r"))
        self.assertFalse(modelo3d.osso_de_mao("head.x"))

    def test_poses_de_mao_do_repositorio_sao_da_direita(self):
        pasta = os.path.join(
            RAIZ, "hq_tools", "modules", "viewer3d", "poses", "maos"
        )
        arquivos = [
            nome for nome in sorted(os.listdir(pasta)) if nome.endswith(".json")
        ]
        self.assertTrue(arquivos)
        for nome in arquivos:
            ossos = modelo3d.carregar_pose(os.path.join(pasta, nome))["ossos"]
            self.assertTrue(ossos, nome)
            for nome_osso in ossos:
                self.assertTrue(nome_osso.endswith(".r"), nome_osso)

    def test_poses_do_repositorio_separadas_por_parte(self):
        prefixos = ("hand", "index", "middle", "pinky", "ring", "thumb")
        corpo = modelo3d.carregar_pose(POSE_IDLE)["ossos"]
        maos = modelo3d.carregar_pose(
            os.path.join(RAIZ, "hq_tools", "modules", "viewer3d", "poses", "maos", "fechada.json")
        )["ossos"]
        self.assertTrue(corpo)
        self.assertTrue(maos)
        self.assertFalse(
            [n for n in corpo if n.split(".")[0].startswith(prefixos)], "corpo com mão"
        )
        self.assertTrue(
            all(n.split(".")[0].startswith(prefixos) for n in maos), "mão com corpo"
        )


class TestCorDoRender(unittest.TestCase):
    def test_cor_escolhida_aparece_no_svg(self):
        if not os.path.isfile(MODELO_REAL):
            self.skipTest("homem.json não está no repositório")
        modelo = modelo3d.Modelo.carregar(MODELO_REAL)
        svg = modelo.renderizar(
            largura=300, altura=300, cor="#123456", estilo="chapado"
        )
        self.assertIn("#123456", svg)

    def test_sem_cor_usa_a_padrao_do_modelo(self):
        if not os.path.isfile(MODELO_REAL):
            self.skipTest("homem.json não está no repositório")
        modelo = modelo3d.Modelo.carregar(MODELO_REAL)
        svg = modelo.renderizar(largura=300, altura=300, estilo="chapado")
        self.assertIn(modelo.cor_padrao, svg)


class TestLentes(unittest.TestCase):
    """Câmera ortográfica (padrão) e perspectiva com lentes."""

    def test_distancia_da_lente_cresce_com_a_lente(self):
        perto = modelo3d.distancia_da_lente(300.0, 700, 14.0)
        longe = modelo3d.distancia_da_lente(300.0, 700, 35.0)
        self.assertGreater(longe, perto)
        self.assertAlmostEqual(perto, 700 * 14.0 / (36.0 * 300.0), places=6)

    def test_distancia_sem_escala_e_zero(self):
        self.assertEqual(modelo3d.distancia_da_lente(0.0, 700, 35.0), 0.0)

    def test_fator_perspectiva_no_plano_central_e_um(self):
        self.assertEqual(modelo3d.fator_perspectiva(0.0, 2.0), 1.0)

    def test_fator_maior_perto_e_menor_longe(self):
        self.assertGreater(modelo3d.fator_perspectiva(-0.5, 2.0), 1.0)
        self.assertLess(modelo3d.fator_perspectiva(0.5, 2.0), 1.0)

    def test_fator_sem_distancia_e_ortografico(self):
        self.assertEqual(modelo3d.fator_perspectiva(0.5, 0.0), 1.0)

    def test_lente_curta_converge_mais(self):
        # À mesma profundidade, a 14 mm (distância menor) deforma mais que a 35.
        escala = 300.0
        d14 = modelo3d.distancia_da_lente(escala, 700, 14.0)
        d35 = modelo3d.distancia_da_lente(escala, 700, 35.0)
        self.assertGreater(
            modelo3d.fator_perspectiva(-0.3, d14),
            modelo3d.fator_perspectiva(-0.3, d35),
        )

    def test_perspectiva_cabe_no_espaco_da_ortografica(self):
        # O ajuste da lente garante que o conjunto projetado não estoure o
        # quadro além do que a ortográfica ocupa (nada de pé cortado).
        if not os.path.isfile(MODELO_REAL):
            self.skipTest("homem.json não está no repositório")
        modelo = modelo3d.Modelo.carregar(MODELO_REAL)
        largura = altura = 700
        base = modelo.vertices_em_tela(largura=largura, altura=altura)
        max_orto_x = max(abs(ponto[0] - largura / 2.0) for ponto in base)
        max_orto_y = max(abs(ponto[1] - altura / 2.0) for ponto in base)
        self.assertGreater(max_orto_x, 1.0)
        for lente in (14.0, 28.0, 35.0):
            persp = modelo.vertices_em_tela(
                largura=largura, altura=altura, lente=lente
            )
            self.assertEqual(len(persp), len(base))
            max_x = max(abs(ponto[0] - largura / 2.0) for ponto in persp)
            max_y = max(abs(ponto[1] - altura / 2.0) for ponto in persp)
            self.assertLessEqual(max_x, max_orto_x + 1e-6, lente)
            self.assertLessEqual(max_y, max_orto_y + 1e-6, lente)


class TestEixosSemanticos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(MODELO_REAL):
            raise unittest.SkipTest("homem.json não está no repositório")
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


class TestModeloMulher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(MODELO_MULHER):
            raise unittest.SkipTest("mulher.json não está no repositório")
        cls.modelo = modelo3d.Modelo.carregar(MODELO_MULHER)

    def test_estrutura(self):
        self.assertEqual(len(self.modelo.ossos), 146)
        self.assertEqual(len(self.modelo.vertices), 1144)
        self.assertEqual(len(self.modelo.faces), 1166)

    def test_mesmos_ossos_do_homem(self):
        if not os.path.isfile(MODELO_REAL):
            self.skipTest("homem.json não está no repositório")
        homem = modelo3d.Modelo.carregar(MODELO_REAL)
        self.assertEqual(
            set(self.modelo.nomes_dos_ossos()), set(homem.nomes_dos_ossos())
        )

    def test_pose_idle_move_o_corpo(self):
        if not os.path.isfile(POSE_IDLE):
            self.skipTest("pose idle não está no repositório")
        pose = modelo3d.carregar_pose(POSE_IDLE)
        repouso = self.modelo.vertices_em_pose()
        posado = self.modelo.vertices_em_pose(
            self.modelo.aplicar_semantica(pose["ossos"])
        )
        diferente = sum(
            1 for a, b in zip(repouso, posado)
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) > 1e-6
        )
        self.assertGreater(diferente, 100)


class TestModeloReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(MODELO_REAL):
            raise unittest.SkipTest("homem.json não está no repositório")
        cls.modelo = modelo3d.Modelo.carregar(MODELO_REAL)

    def test_estrutura(self):
        self.assertEqual(len(self.modelo.ossos), 146)
        self.assertEqual(len(self.modelo.vertices), 1144)
        self.assertEqual(len(self.modelo.faces), 1166)
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

    def test_contorno_tem_muitos_segmentos(self):
        svg = self.modelo.renderizar(largura=500, altura=500, estilo="contorno")
        raiz = ET.fromstring(svg)
        caminho = raiz.find("{http://www.w3.org/2000/svg}path")
        self.assertIsNotNone(caminho)
        self.assertGreater(caminho.get("d").count("M"), 50)

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
