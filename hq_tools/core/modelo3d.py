"""Visualizador 3D do HQ Tools: núcleo puro, sem Krita e sem numpy.

O modelo vem do exportador ``scripts/exportar-modelo3d.py`` (FBX -> JSON). Aqui
ficam a cinemática direta dos ossos, o skinning linear, a projeção ortográfica
com câmera orbit e a saída SVG. O Blender não é dependência em tempo de
execução; o FBX também não, porque é binário e o Python do Krita não o lê.

Convenções: o modelo é Z-up (padrão do Blender). A câmera orbita em torno do
eixo Z (``yaw``) e inclina em torno do eixo horizontal (``pitch``); o ``y`` do
espaço do modelo é a profundidade (a câmera olha do ``-y`` para o ``+y``). As
rotações das juntas são locais, em graus, aplicadas na ordem X, depois Y,
depois Z.
"""

import json
import math

FORMATO = "hq_tools.modelo3d"
VERSAO = 1
POSE_FORMATO = "hq_tools.pose3d"
POSE_VERSAO = 1

LUZ_PADRAO = (0.4, -0.8, 0.45)


def identidade():
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def multiplicar(a, b):
    resultado = [0.0] * 16
    for linha in range(4):
        base = linha * 4
        for coluna in range(4):
            resultado[base + coluna] = (
                a[base] * b[coluna]
                + a[base + 1] * b[4 + coluna]
                + a[base + 2] * b[8 + coluna]
                + a[base + 3] * b[12 + coluna]
            )
    return resultado


def aplicar_ponto(matriz, ponto):
    x, y, z = ponto
    return (
        matriz[0] * x + matriz[1] * y + matriz[2] * z + matriz[3],
        matriz[4] * x + matriz[5] * y + matriz[6] * z + matriz[7],
        matriz[8] * x + matriz[9] * y + matriz[10] * z + matriz[11],
    )


def inversa_afim(matriz):
    a, b, c, tx = matriz[0], matriz[1], matriz[2], matriz[3]
    d, e, f, ty = matriz[4], matriz[5], matriz[6], matriz[7]
    g, h, i, tz = matriz[8], matriz[9], matriz[10], matriz[11]
    determinante = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(determinante) < 1e-12:
        raise ValueError("matriz de repouso sem inversa")
    fator = 1.0 / determinante
    r00 = (e * i - f * h) * fator
    r01 = (c * h - b * i) * fator
    r02 = (b * f - c * e) * fator
    r10 = (f * g - d * i) * fator
    r11 = (a * i - c * g) * fator
    r12 = (c * d - a * f) * fator
    r20 = (d * h - e * g) * fator
    r21 = (b * g - a * h) * fator
    r22 = (a * e - b * d) * fator
    return [
        r00, r01, r02, -(r00 * tx + r01 * ty + r02 * tz),
        r10, r11, r12, -(r10 * tx + r11 * ty + r12 * tz),
        r20, r21, r22, -(r20 * tx + r21 * ty + r22 * tz),
        0.0, 0.0, 0.0, 1.0,
    ]


def rotacao_x(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, cosseno, -seno, 0.0,
        0.0, seno, cosseno, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def rotacao_y(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        cosseno, 0.0, seno, 0.0,
        0.0, 1.0, 0.0, 0.0,
        -seno, 0.0, cosseno, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def rotacao_z(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        cosseno, -seno, 0.0, 0.0,
        seno, cosseno, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def rotacao_euler(rotacao):
    rx, ry, rz = rotacao
    return multiplicar(rotacao_z(rz), multiplicar(rotacao_y(ry), rotacao_x(rx)))


def _normalizar(vetor):
    tamanho = math.sqrt(vetor[0] ** 2 + vetor[1] ** 2 + vetor[2] ** 2)
    if tamanho < 1e-12:
        return (0.0, 0.0, 0.0)
    return (vetor[0] / tamanho, vetor[1] / tamanho, vetor[2] / tamanho)


def carregar_pose(caminho):
    """Lê um JSON de pose do visualizador (``hq_tools.pose3d``)."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if dados.get("formato") != POSE_FORMATO:
        raise ValueError(
            "formato de pose desconhecido: {0}".format(dados.get("formato"))
        )
    if int(dados.get("versao", 0)) > POSE_VERSAO:
        raise ValueError(
            "pose versão {0}; o plugin entende até {1}".format(
                dados["versao"], POSE_VERSAO
            )
        )
    return dados


EIXOS = {"x": 0, "y": 1, "z": 2}


def eixos_semanticos(osso):
    """Mapeia os eixos locais do osso para nomes de junta.

    Devolve ``{"dobrar": (eixo, sinal), "abrir": (eixo, sinal), "girar": ...}``
    onde ``eixo`` é "x", "y" ou "z" e ``sinal`` é +1 ou -1. O eixo alinhado com
    o lado do corpo (mundo X) é o de dobrar (frente/trás); o outro é o de abrir
    para o lado; o eixo do osso (Y) é o de girar. Os sinais são escolhidos para
    que "dobrar" positivo vá para frente e "abrir" positivo vá para fora do
    corpo. Medido no rig do autor (Auto-Rig Pro): coxa e braço têm dobrar no Z
    e abrir no X; cabeça e tronco, o contrário.
    """
    matriz = osso["matriz"]

    def coluna(indice):
        return _normalizar((
            matriz[indice], matriz[4 + indice], matriz[8 + indice]
        ))

    eixo_x, eixo_y, eixo_z = coluna(0), coluna(1), coluna(2)
    if abs(eixo_z[0]) >= abs(eixo_x[0]):
        dobrar = ("z", eixo_z)
        abrir = ("x", eixo_x)
    else:
        dobrar = ("x", eixo_x)
        abrir = ("z", eixo_z)

    def sinal(escolhido, alvo):
        a = escolhido[1]
        cruzamento = (
            a[1] * eixo_y[2] - a[2] * eixo_y[1],
            a[2] * eixo_y[0] - a[0] * eixo_y[2],
            a[0] * eixo_y[1] - a[1] * eixo_y[0],
        )
        produto = (
            cruzamento[0] * alvo[0]
            + cruzamento[1] * alvo[1]
            + cruzamento[2] * alvo[2]
        )
        return 1 if produto > 0 else -1

    frente = (0.0, -1.0, 0.0)
    lado = (1.0, 0.0, 0.0) if osso["nome"].endswith(".l") else (-1.0, 0.0, 0.0)
    return {
        "dobrar": (dobrar[0], sinal(dobrar, frente)),
        "abrir": (abrir[0], sinal(abrir, lado)),
        "girar": ("y", 1),
    }


def _hex_para_rgb(cor):
    cor = cor.lstrip("#")
    return (int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16))


def _rgb_para_hex(rgb):
    return "#{0:02x}{1:02x}{2:02x}".format(
        max(0, min(255, int(round(rgb[0])))),
        max(0, min(255, int(round(rgb[1])))),
        max(0, min(255, int(round(rgb[2])))),
    )


class Modelo:
    """Modelo 3D com ossos, malha e pesos, pronto para posar e desenhar."""

    def __init__(self, dados):
        if dados.get("formato") != FORMATO:
            raise ValueError(
                "formato de modelo desconhecido: {0}".format(dados.get("formato"))
            )
        if int(dados.get("versao", 0)) > VERSAO:
            raise ValueError(
                "modelo versão {0}; o plugin entende até {1}".format(
                    dados["versao"], VERSAO
                )
            )
        self.nome = dados.get("nome", "modelo")
        self.cor_padrao = dados.get("cor_padrao", "#d8c3b0")
        self.ossos = list(dados["ossos"])
        self.vertices = [tuple(vertice) for vertice in dados["vertices"]]
        self.pesos = [list(pares) for pares in dados["pesos"]]
        self.faces = [tuple(face) for face in dados["faces"]]
        self.osso_por_nome = {osso["nome"]: osso for osso in self.ossos}
        self.caixa = self._calcular_caixa()

    @classmethod
    def carregar(cls, caminho):
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return cls(json.load(arquivo))

    def _calcular_caixa(self):
        xs = [vertice[0] for vertice in self.vertices]
        ys = [vertice[1] for vertice in self.vertices]
        zs = [vertice[2] for vertice in self.vertices]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def centro(self):
        x0, y0, z0, x1, y1, z1 = self.caixa
        return ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)

    def diagonal(self):
        x0, y0, z0, x1, y1, z1 = self.caixa
        return math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)

    def nomes_dos_ossos(self):
        return [osso["nome"] for osso in self.ossos]

    def matrizes_de_pele(self, rotacoes=None):
        """Matrizes que levam cada vértice de repouso à pose pedida."""
        rotacoes = rotacoes or {}
        poses = []
        for osso in self.ossos:
            repouso = osso["matriz"]
            rotacao = rotacao_euler(rotacoes.get(osso["nome"], (0.0, 0.0, 0.0)))
            pai = osso["pai"]
            if pai is None:
                pose = multiplicar(repouso, rotacao)
            else:
                relativo = multiplicar(inversa_afim(self.ossos[pai]["matriz"]), repouso)
                pose = multiplicar(poses[pai], multiplicar(relativo, rotacao))
            poses.append(pose)
        return [
            multiplicar(poses[indice], inversa_afim(osso["matriz"]))
            for indice, osso in enumerate(self.ossos)
        ]

    def aplicar_semantica(self, valores):
        """Converte valores de junta (dobrar/abrir/girar) em rotações locais.

        ``valores`` é ``{nome_do_osso: {"dobrar": graus, ...}}``; o mapeamento
        de cada osso vem de :func:`eixos_semanticos`.
        """
        rotacoes = {}
        for nome, pedidos in valores.items():
            osso = self.osso_por_nome.get(nome)
            if osso is None:
                continue
            mapa = eixos_semanticos(osso)
            vetor = [0.0, 0.0, 0.0]
            for chave, graus in pedidos.items():
                if chave not in mapa:
                    continue
                eixo, sinal = mapa[chave]
                vetor[EIXOS[eixo]] += sinal * float(graus)
            rotacoes[nome] = tuple(vetor)
        return rotacoes

    def vertices_em_pose(self, rotacoes=None):
        """Vértices no espaço do modelo com o skinning aplicado."""
        matrizes = self.matrizes_de_pele(rotacoes)
        resultado = []
        for indice, vertice in enumerate(self.vertices):
            x = y = z = 0.0
            for osso, peso in self.pesos[indice]:
                matriz = matrizes[osso]
                x += peso * (
                    matriz[0] * vertice[0] + matriz[1] * vertice[1]
                    + matriz[2] * vertice[2] + matriz[3]
                )
                y += peso * (
                    matriz[4] * vertice[0] + matriz[5] * vertice[1]
                    + matriz[6] * vertice[2] + matriz[7]
                )
                z += peso * (
                    matriz[8] * vertice[0] + matriz[9] * vertice[1]
                    + matriz[10] * vertice[2] + matriz[11]
                )
            resultado.append((x, y, z))
        return resultado

    def _contorno(self, na_camera):
        """Arestas de silhueta: as que separam face da frente de face de trás.

        Percorre os triângulos, marca a orientação de cada um e devolve os
        pares de vértices cujas faces vizinhas discordam (ou que só têm uma
        face). É o que desenha a linha do contorno do modelo projetado.
        """
        vizinhanca = {}
        for face in self.faces:
            for triangulo in self._triangular(face):
                p0, p1, p2 = (na_camera[indice] for indice in triangulo)
                aresta1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                aresta2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                normal_y = aresta1[2] * aresta2[0] - aresta1[0] * aresta2[2]
                frente = normal_y < -1e-9
                for a, b in ((0, 1), (1, 2), (2, 0)):
                    chave = (
                        min(triangulo[a], triangulo[b]),
                        max(triangulo[a], triangulo[b]),
                    )
                    registro = vizinhanca.setdefault(chave, [0, 0])
                    registro[0 if frente else 1] += 1
        return [
            chave
            for chave, (frente, tras) in vizinhanca.items()
            if (frente > 0 and tras > 0) or (frente + tras) == 1
        ]

    @staticmethod
    def _triangular(face):
        """Leque de triângulos: o culling e o painter ficam estáveis com quads
        não planares, que é o caso de todas as faces do modelo exportado."""
        if len(face) <= 3:
            return [face]
        return [(face[0], face[indice], face[indice + 1]) for indice in range(1, len(face) - 1)]

    def _camera(self, yaw, pitch, zoom, largura, altura, pan_x, pan_y):
        visao = multiplicar(rotacao_x(pitch), rotacao_z(yaw))
        centro = aplicar_ponto(visao, self.centro())
        escala = min(largura, altura) / max(self.diagonal(), 1e-6) * 0.85 * zoom
        return visao, centro, escala

    def vertices_em_tela(self, rotacoes=None, yaw=0.0, pitch=-10.0, zoom=1.0,
                         largura=700, altura=700, pan_x=0.0, pan_y=0.0,
                         posados=None):
        """Projeta os vértices posados: (x, y na tela, profundidade)."""
        visao, centro, escala = self._camera(yaw, pitch, zoom, largura, altura, pan_x, pan_y)
        if posados is None:
            posados = self.vertices_em_pose(rotacoes)
        resultado = []
        for vertice in posados:
            x, y, z = aplicar_ponto(visao, vertice)
            tela_x = largura / 2.0 + (x - centro[0]) * escala + pan_x
            tela_y = altura / 2.0 - (z - centro[2]) * escala + pan_y
            resultado.append((tela_x, tela_y, y))
        return resultado

    def renderizar(self, rotacoes=None, yaw=0.0, pitch=-10.0, zoom=1.0,
                   largura=700, altura=700, pan_x=0.0, pan_y=0.0,
                   cor=None, fundo=None, luz=LUZ_PADRAO, cull=False, posados=None,
                   estilo="sombreado"):
        """Devolve o SVG do modelo posado.

        ``estilo="sombreado"`` (padrão) usa painter's algorithm e sombreamento
        por face. ``estilo="chapado"`` desenha a silhueta: todas as faces numa
        cor só, num único ``path``, sem ordenar nem sombrear; é mais barato de
        gerar e de rasterizar. ``estilo="contorno"`` desenha só a linha de
        silhueta (as arestas entre faces da frente e de trás).
        """
        visao, centro, escala = self._camera(yaw, pitch, zoom, largura, altura, pan_x, pan_y)
        if posados is None:
            posados = self.vertices_em_pose(rotacoes)
        na_camera = [aplicar_ponto(visao, vertice) for vertice in posados]
        tela = [
            (
                largura / 2.0 + (x - centro[0]) * escala + pan_x,
                altura / 2.0 - (z - centro[2]) * escala + pan_y,
                y,
            )
            for x, y, z in na_camera
        ]
        luz_normalizada = _normalizar(luz)
        base = _hex_para_rgb(cor or self.cor_padrao)

        partes = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
            'viewBox="0 0 {0} {1}">'.format(largura, altura)
        ]
        if fundo:
            partes.append(
                '<rect width="{0}" height="{1}" fill="{2}"/>'.format(largura, altura, fundo)
            )

        if estilo in ("chapado", "contorno"):
            cor_solida = _rgb_para_hex(_hex_para_rgb(cor or self.cor_padrao))
            if estilo == "chapado":
                caminho = []
                for face in self.faces:
                    for triangulo in self._triangular(face):
                        a, b, c = (tela[indice] for indice in triangulo)
                        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
                        if area < 0:
                            b, c = c, b
                        caminho.append(
                            "M{0:.1f} {1:.1f}L{2:.1f} {3:.1f}L{4:.1f} {5:.1f}Z".format(
                                a[0], a[1], b[0], b[1], c[0], c[1],
                            )
                        )
                partes.append(
                    '<path d="{0}" fill="{1}"/>'.format("".join(caminho), cor_solida)
                )
            else:
                caminho = []
                for inicio, fim in self._contorno(na_camera):
                    caminho.append(
                        "M{0:.1f} {1:.1f}L{2:.1f} {3:.1f}".format(
                            tela[inicio][0], tela[inicio][1],
                            tela[fim][0], tela[fim][1],
                        )
                    )
                partes.append(
                    '<path d="{0}" fill="none" stroke="{1}" stroke-width="1.5" '
                    'stroke-linejoin="round"/>'.format("".join(caminho), cor_solida)
                )
            partes.append("</svg>")
            return "".join(partes)

        desenhaveis = []
        for face in self.faces:
            for triangulo in self._triangular(face):
                p0, p1, p2 = (
                    na_camera[triangulo[0]],
                    na_camera[triangulo[1]],
                    na_camera[triangulo[2]],
                )
                aresta1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                aresta2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                normal = _normalizar((
                    aresta1[1] * aresta2[2] - aresta1[2] * aresta2[1],
                    aresta1[2] * aresta2[0] - aresta1[0] * aresta2[2],
                    aresta1[0] * aresta2[1] - aresta1[1] * aresta2[0],
                ))
                if cull and normal[1] >= -1e-9:
                    continue
                difusa = abs(
                    normal[0] * luz_normalizada[0]
                    + normal[1] * luz_normalizada[1]
                    + normal[2] * luz_normalizada[2]
                )
                brilho = 0.35 + 0.65 * difusa
                profundidade = (
                    p0[1] + p1[1] + p2[1]
                ) / 3.0
                desenhaveis.append((profundidade, triangulo, brilho))

        desenhaveis.sort(key=lambda item: item[0], reverse=True)
        for _, face, brilho in desenhaveis:
            rgb = tuple(canal * brilho for canal in base)
            pontos_svg = " ".join(
                "{0:.1f},{1:.1f}".format(tela[indice][0], tela[indice][1])
                for indice in face
            )
            cor_face = _rgb_para_hex(rgb)
            partes.append(
                '<polygon points="{0}" fill="{1}" stroke="{1}" stroke-width="0.4"/>'.format(
                    pontos_svg, cor_face
                )
            )
        partes.append("</svg>")
        return "".join(partes)
