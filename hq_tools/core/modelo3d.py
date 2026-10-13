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

import functools
import json
import math
import os
import re
import unicodedata

FORMATO = "hq_tools.modelo3d"
VERSAO = 1
POSE_FORMATO = "hq_tools.pose3d"
POSE_VERSAO = 1

LUZ_PADRAO = (0.4, -0.8, 0.45)

# Limite do estilo "toon": acima dele a face fica no tom de luz; abaixo, no de
# sombra (dois tons chapados de alto contraste).
LIMITE_TOON = 0.20


def luz_de_angulos(azimute, altura):
    """Vetor de luz (espaço da câmera) a partir do azimute e da altura (graus).

    Azimute 0 = luz vindo de frente para o modelo; o negativo traz a luz da
    esquerda da imagem e o positivo da direita; a altura positiva sobe. Os
    padrões do docker (26,6° e 26,7°) reproduzem a ``LUZ_PADRAO``.
    """
    az = math.radians(azimute)
    al = math.radians(altura)
    return (
        math.sin(az) * math.cos(al),
        -math.cos(az) * math.cos(al),
        math.sin(al),
    )


# Lentes oferecidas na perspectiva (mm, sensor cheio de 36 mm). Sem lente, a
# projeção é ortográfica (o padrão do visualizador).
SENSOR_MM = 36.0
LENTES = (14.0, 28.0, 35.0)


def distancia_da_lente(escala, largura, lente_mm, sensor_mm=SENSOR_MM):
    """Distância da câmera (unidades do modelo) para a lente pedida.

    A calibração deixa o plano central do modelo com a mesma escala da
    projeção ortográfica: a lente muda só a convergência (14 mm dramática,
    35 mm suave) e o zoom continua mandando no enquadramento.
    """
    if escala <= 0 or lente_mm <= 0 or largura <= 0:
        return 0.0
    return float(largura) * float(lente_mm) / (float(sensor_mm) * float(escala))


def fator_perspectiva(profundidade, distancia):
    """Escala de um ponto a ``profundidade`` relativa ao plano central.

    ``1.0`` no plano central (coincide com a projeção ortográfica); maior que
    um para o que está mais perto da câmera e menor para o que está mais
    longe. Sem distância (ou ortográfica), devolve 1.
    """
    if distancia <= 0:
        return 1.0
    return distancia / (distancia + profundidade)


def identidade():
    return [
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


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
        r00,
        r01,
        r02,
        -(r00 * tx + r01 * ty + r02 * tz),
        r10,
        r11,
        r12,
        -(r10 * tx + r11 * ty + r12 * tz),
        r20,
        r21,
        r22,
        -(r20 * tx + r21 * ty + r22 * tz),
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def rotacao_x(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        cosseno,
        -seno,
        0.0,
        0.0,
        seno,
        cosseno,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def rotacao_y(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        cosseno,
        0.0,
        seno,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        -seno,
        0.0,
        cosseno,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def rotacao_z(graus):
    radianos = math.radians(graus)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    return [
        cosseno,
        -seno,
        0.0,
        0.0,
        seno,
        cosseno,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
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


def serializar_pose(nome, ossos):
    """Monta o documento de uma pose (formato ``hq_tools.pose3d``).

    Arredonda os valores para duas casas (como os exportadores) e ordena os
    ossos: o arquivo do usuário fica no mesmo formato do kit.
    """
    return {
        "formato": POSE_FORMATO,
        "versao": POSE_VERSAO,
        "nome": str(nome),
        "ossos": {
            nome_osso: {
                chave: round(float(valor), 2)
                for chave, valor in sorted(valores.items())
            }
            for nome_osso, valores in sorted(ossos.items())
        },
    }


def salvar_pose(caminho, nome, ossos):
    """Grava a pose em JSON, atômico (temporário + replace)."""
    dados = serializar_pose(nome, ossos)
    temporario = "{0}.tmp".format(caminho)
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(temporario, caminho)
    return dados


def slug_de_pose(nome):
    """Nome de arquivo seguro para a pose (sem acento, minúsculo, com hifens)."""
    texto = unicodedata.normalize("NFKD", str(nome))
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    texto = re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-").lower()
    return texto or "pose"


LADO_DIREITA = "direita"
LADO_ESQUERDA = "esquerda"
LADO_AMBAS = "ambas"
LADOS = (LADO_DIREITA, LADO_ESQUERDA, LADO_AMBAS)


def espelhar(valores):
    """Troca a pose de lado: ``.r`` vira ``.l`` (e vice-versa), ``girar`` negado.

    Os valores são semânticos: ``dobrar`` e ``abrir`` já são simétricos por
    construção (o mapa de eixos é escolhido por lado), então só o giro em
    torno do eixo do osso troca de sinal no espelho. As poses de mão são
    autorais para a mão direita; esta função as leva para a esquerda.
    """
    resultado = {}
    for osso, junta in (valores or {}).items():
        if osso.endswith(".r"):
            nome = osso[:-2] + ".l"
        elif osso.endswith(".l"):
            nome = osso[:-2] + ".r"
        else:
            nome = osso
        copia = dict(junta)
        if "girar" in copia:
            copia["girar"] = -float(copia["girar"])
        resultado[nome] = copia
    return resultado


def pose_maos_por_lado(valores, lado):
    """Pose de mão no lado pedido: direita, espelhada ou nas duas mãos.

    O seletor manda: os valores de mão esquerda que venham no arquivo são
    descartados antes de aplicar o lado. As poses antigas (migradas do Idle)
    guardavam os dois lados, e sem esta normalização o seletor não teria o que
    mudar (direita, esquerda e ambas saíam iguais).
    """
    direita = {
        osso: dict(junta)
        for osso, junta in (valores or {}).items()
        if not osso.endswith(".l")
    }
    if lado == LADO_ESQUERDA:
        return espelhar(direita)
    if lado == LADO_AMBAS:
        resultado = {osso: dict(junta) for osso, junta in direita.items()}
        resultado.update(espelhar(direita))
        return resultado
    return direita


def combinar_poses(corpo, mao_direita, mao_esquerda):
    """Corpo + mãos (cada mão por cima, a esquerda espelhada).

    As poses de corpo não têm ossos de mão: sem esta combinação os dedos
    ficam no repouso. Cada mão é independente (uma pode vir vazia) e a
    esquerda recebe a versão espelhada da pose autoral da direita.
    """
    resultado = {osso: dict(valores) for osso, valores in (corpo or {}).items()}
    for valores, lado in (
        (mao_direita, LADO_DIREITA),
        (mao_esquerda, LADO_ESQUERDA),
    ):
        for osso, junta in pose_maos_por_lado(valores, lado).items():
            resultado[osso] = dict(junta)
    return resultado


EIXOS = {"x": 0, "y": 1, "z": 2}

PREFIXOS_MAO = ("hand", "index", "middle", "pinky", "ring", "thumb")


def osso_de_mao(nome):
    """True para os ossos de mão (pulso e dedos), com ou sem lado."""
    return str(nome).split(".")[0].startswith(PREFIXOS_MAO)


def substituir_corpo(semantica, corpo):
    """Troca só a parte do corpo, preservando as mãos (e seus ajustes).

    Diferente do :func:`combinar_poses`, que remonta tudo: aqui os ossos de
    mão que já estavam na semântica ficam como estão (inclusive valores
    ajustados nos sliders) e só a parte do corpo é substituída.
    """
    resultado = {
        osso: dict(valores)
        for osso, valores in (semantica or {}).items()
        if osso_de_mao(osso)
    }
    for osso, valores in (corpo or {}).items():
        resultado[osso] = dict(valores)
    return resultado


def substituir_mao(semantica, mao, lado):
    """Troca só a mão pedida, preservando corpo e a outra mão.

    Remove os ossos de mão daquele lado (o que a pose nova não trouxer volta
    ao repouso) e aplica a pose espelhada quando o lado é a esquerda.
    """
    sufixo = ".r" if lado == LADO_DIREITA else ".l"
    resultado = {
        osso: dict(valores)
        for osso, valores in (semantica or {}).items()
        if not (osso_de_mao(osso) and osso.endswith(sufixo))
    }
    for osso, valores in pose_maos_por_lado(mao, lado).items():
        resultado[osso] = dict(valores)
    return resultado


def semantica_do_corpo(semantica):
    """Só os ossos do corpo (fora mãos e dedos), para a pose do usuário."""
    return {
        osso: dict(valores)
        for osso, valores in semantica.items()
        if not osso_de_mao(osso)
    }


REFERENCIA_DEDOS_GRAUS = 82.0


def dedos_por_graus(referencia, lado, graus, graus_referencia=REFERENCIA_DEDOS_GRAUS):
    """Valores dos dedos interpolando a pose de referência (0..graus_referencia).

    ``referencia`` é o mapa de ossos da pose "fechada" (autoral da direita);
    a esquerda sai do espelho dela. Devolve ``{osso: {chave: valor}}`` pronto
    para entrar na semântica (0° = repouso/aberta, a referência em
    ``graus_referencia`` = punho).
    """
    base = referencia if lado == LADO_DIREITA else espelhar(referencia)
    fator = float(graus) / float(graus_referencia)
    return {
        osso: {
            chave: round(float(valor) * fator, 2) for chave, valor in valores.items()
        }
        for osso, valores in base.items()
    }


def graus_dos_dedos(
    referencia, ossos, semantica, graus_referencia=REFERENCIA_DEDOS_GRAUS
):
    """O caminho inverso: o valor do slider a partir da semântica atual.

    Usa o primeiro osso que existe na referência (o polegar é composto, então
    a razão do primeiro osso resolve os três).
    """
    base = referencia if (ossos and ossos[0].endswith(".r")) else espelhar(referencia)
    for osso in ossos:
        if osso in base and "abrir" in base[osso]:
            marco = base[osso]["abrir"]
            if abs(marco) > 1e-6:
                atual = semantica.get(osso, {}).get("abrir", 0.0)
                return int(round(atual * graus_referencia / marco))
            return 0
    return 0


def semantica_da_mao(semantica, lado):
    """Só os ossos de uma mão (pulso e dedos), para salvar a pose de mão.

    A pose salva sai sempre na convenção autoral (mão direita): a esquerda é
    espelhada com :func:`espelhar` na hora de gravar.
    """
    sufixo = ".r" if lado == LADO_DIREITA else ".l"
    return {
        osso: dict(valores)
        for osso, valores in semantica.items()
        if osso_de_mao(osso) and osso.endswith(sufixo)
    }


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
        return _normalizar((matriz[indice], matriz[4 + indice], matriz[8 + indice]))

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
            cruzamento[0] * alvo[0] + cruzamento[1] * alvo[1] + cruzamento[2] * alvo[2]
        )
        return 1 if produto > 0 else -1

    frente = (0.0, -1.0, 0.0)
    lado = (1.0, 0.0, 0.0) if osso["nome"].endswith(".l") else (-1.0, 0.0, 0.0)
    return {
        "dobrar": (dobrar[0], sinal(dobrar, frente)),
        "abrir": (abrir[0], sinal(abrir, lado)),
        "girar": ("y", 1),
    }


# Prévias de pose (ícones do seletor do docker e miniatura da pose do
# usuário), num lugar só porque o script da galeria e o docker desenham a
# mesma imagem. Calibradas por ``scripts/calibrar-galeria-poses3d.py``: o
# corpo fecha o quadro na vista padrão; as mãos usam um close na direita (o
# docker espelha para a esquerda) com o braço levantado ao lado, para a mão
# sair da silhueta do corpo e o fundo ficar limpo.
PREVIA_LARGURA, PREVIA_ALTURA = 120, 160
PREVIA_CAMERA_CORPO = {
    "yaw": 0.0,
    "pitch": -10.0,
    "zoom": 1.708,
    "pan_x": 1.8,
    "pan_y": -0.3,
}
PREVIA_CAMERA_MAOS = {
    "yaw": -15.0,
    "pitch": -10.0,
    "zoom": 11.142,
    "pan_x": 356.7,
    "pan_y": 362.5,
}
PREVIA_ABRIR_MAO = 70.0


def render_previa(
    modelo, semantica, parte, largura=PREVIA_LARGURA, altura=PREVIA_ALTURA
):
    """SVG da prévia de pose (``parte`` = "corpo" ou "maos").

    Nas mãos, o braço direito sai para o lado antes de renderizar (a mão fica
    fora da silhueta do corpo). Devolve o SVG, como :meth:`Modelo.renderizar`.
    """
    camera = PREVIA_CAMERA_CORPO if parte == "corpo" else PREVIA_CAMERA_MAOS
    if parte == "maos":
        semantica = {osso: dict(valores) for osso, valores in semantica.items()}
        semantica.setdefault("arm_stretch.r", {})["abrir"] = PREVIA_ABRIR_MAO
    posados = modelo.vertices_em_pose(modelo.aplicar_semantica(semantica))
    return modelo.renderizar(
        yaw=camera["yaw"],
        pitch=camera["pitch"],
        zoom=camera["zoom"],
        pan_x=camera["pan_x"],
        pan_y=camera["pan_y"],
        largura=largura,
        altura=altura,
        posados=posados,
    )


def _hex_para_rgb(cor):
    cor = cor.lstrip("#")
    return (int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16))


@functools.lru_cache(maxsize=4096)
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
        # A triangulação (leque) não muda com a pose nem com a câmera; fica
        # pronta para os três consumidores (chapado, toon e sombreado), em vez
        # de refeita a cada quadro.
        self.triangulos = [self._triangular(face) for face in self.faces]
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
                    matriz[0] * vertice[0]
                    + matriz[1] * vertice[1]
                    + matriz[2] * vertice[2]
                    + matriz[3]
                )
                y += peso * (
                    matriz[4] * vertice[0]
                    + matriz[5] * vertice[1]
                    + matriz[6] * vertice[2]
                    + matriz[7]
                )
                z += peso * (
                    matriz[8] * vertice[0]
                    + matriz[9] * vertice[1]
                    + matriz[10] * vertice[2]
                    + matriz[11]
                )
            resultado.append((x, y, z))
        return resultado

    @staticmethod
    def _triangular(face):
        """Leque de triângulos: o culling e o painter ficam estáveis com quads
        não planares, que é o caso de todas as faces do modelo exportado."""
        if len(face) <= 3:
            return [face]
        return [
            (face[0], face[indice], face[indice + 1])
            for indice in range(1, len(face) - 1)
        ]

    def _camera(self, yaw, pitch, zoom, largura, altura, pan_x, pan_y, lente=None):
        """(visão, centro, escala, distância): distância é None na ortográfica."""
        visao = multiplicar(rotacao_x(pitch), rotacao_z(yaw))
        centro = aplicar_ponto(visao, self.centro())
        escala = min(largura, altura) / max(self.diagonal(), 1e-6) * 0.85 * zoom
        distancia = None
        if lente:
            distancia = distancia_da_lente(escala, largura, lente)
        return visao, centro, escala, distancia

    def _projetar(
        self, na_camera, centro, escala, distancia, largura, altura, pan_x, pan_y
    ):
        """Pontos de tela a partir das coordenadas de câmera.

        Com lente, o fator de perspectiva cresce para o que está perto; para o
        conjunto não estourar o quadro como na ortográfica (um pé que chega
        perto da câmera, por exemplo), um ajuste único encolhe o resultado até
        caber no mesmo espaço da projeção ortográfica.
        """
        fatores = [1.0] * len(na_camera)
        ajuste = 1.0
        if distancia:
            fatores = [
                fator_perspectiva(y - centro[1], distancia) for _, y, _ in na_camera
            ]
            ortogonal_x = max(
                (abs(x - centro[0]) for x, _, _ in na_camera), default=0.0
            )
            ortogonal_y = max(
                (abs(z - centro[2]) for _, _, z in na_camera), default=0.0
            )
            projetado_x = max(
                (abs((x - centro[0]) * f) for (x, _, _), f in zip(na_camera, fatores)),
                default=0.0,
            )
            projetado_y = max(
                (abs((z - centro[2]) * f) for (_, _, z), f in zip(na_camera, fatores)),
                default=0.0,
            )
            for ortogonal, projetado in (
                (ortogonal_x, projetado_x),
                (ortogonal_y, projetado_y),
            ):
                if projetado > ortogonal > 0:
                    ajuste = min(ajuste, ortogonal / projetado)
        return [
            (
                largura / 2.0 + (x - centro[0]) * escala * f * ajuste + pan_x,
                altura / 2.0 - (z - centro[2]) * escala * f * ajuste + pan_y,
                y,
            )
            for (x, y, z), f in zip(na_camera, fatores)
        ]

    def vertices_em_tela(
        self,
        rotacoes=None,
        yaw=0.0,
        pitch=-10.0,
        zoom=1.0,
        largura=700,
        altura=700,
        pan_x=0.0,
        pan_y=0.0,
        posados=None,
        lente=None,
    ):
        """Projeta os vértices posados: (x, y na tela, profundidade)."""
        visao, centro, escala, distancia = self._camera(
            yaw, pitch, zoom, largura, altura, pan_x, pan_y, lente=lente
        )
        if posados is None:
            posados = self.vertices_em_pose(rotacoes)
        na_camera = [aplicar_ponto(visao, vertice) for vertice in posados]
        return self._projetar(
            na_camera, centro, escala, distancia, largura, altura, pan_x, pan_y
        )

    def renderizar(
        self,
        rotacoes=None,
        yaw=0.0,
        pitch=-10.0,
        zoom=1.0,
        largura=700,
        altura=700,
        pan_x=0.0,
        pan_y=0.0,
        cor=None,
        fundo=None,
        luz=LUZ_PADRAO,
        cull=False,
        posados=None,
        estilo="sombreado",
        lente=None,
    ):
        """Devolve o SVG do modelo posado.

        ``estilo="sombreado"`` (padrão) usa painter's algorithm e sombreamento
        por face. ``estilo="chapado"`` desenha a silhueta: todas as faces numa
        cor só, num único ``path``, sem ordenar nem sombrear; é mais barato de
        gerar e de rasterizar. ``estilo="toon"`` usa dois tons chapados de
        alto contraste: as faces viradas para a luz num tom, as em sombra num
        tom escuro do mesmo matiz (``luz`` decide a divisão).
        """
        visao, centro, escala, distancia = self._camera(
            yaw, pitch, zoom, largura, altura, pan_x, pan_y, lente=lente
        )
        if posados is None:
            posados = self.vertices_em_pose(rotacoes)
        na_camera = [aplicar_ponto(visao, vertice) for vertice in posados]
        tela = self._projetar(
            na_camera, centro, escala, distancia, largura, altura, pan_x, pan_y
        )
        luz_normalizada = _normalizar(luz)
        base = _hex_para_rgb(cor or self.cor_padrao)

        partes = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
            'viewBox="0 0 {0} {1}">'.format(largura, altura)
        ]
        if fundo:
            partes.append(
                '<rect width="{0}" height="{1}" fill="{2}"/>'.format(
                    largura, altura, fundo
                )
            )

        if estilo == "chapado":
            cor_solida = _rgb_para_hex(_hex_para_rgb(cor or self.cor_padrao))
            caminho = []
            for triangulos in self.triangulos:
                for triangulo in triangulos:
                    a, b, c = (tela[indice] for indice in triangulo)
                    area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
                    if area < 0:
                        b, c = c, b
                    caminho.append(
                        f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}"
                        f"L{c[0]:.1f} {c[1]:.1f}Z"
                    )
            partes.append(
                '<path d="{0}" fill="{1}"/>'.format("".join(caminho), cor_solida)
            )
            partes.append("</svg>")
            return "".join(partes)

        desenhaveis = []
        for triangulos in self.triangulos:
            for triangulo in triangulos:
                p0, p1, p2 = (
                    na_camera[triangulo[0]],
                    na_camera[triangulo[1]],
                    na_camera[triangulo[2]],
                )
                aresta1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                aresta2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                normal = _normalizar(
                    (
                        aresta1[1] * aresta2[2] - aresta1[2] * aresta2[1],
                        aresta1[2] * aresta2[0] - aresta1[0] * aresta2[2],
                        aresta1[0] * aresta2[1] - aresta1[1] * aresta2[0],
                    )
                )
                if cull and normal[1] >= -1e-9:
                    continue
                produto = (
                    normal[0] * luz_normalizada[0]
                    + normal[1] * luz_normalizada[1]
                    + normal[2] * luz_normalizada[2]
                )
                if estilo == "toon":
                    # Dois tons de alto contraste: o lado virado para a luz
                    # fica claro e o resto escurece (sem ``abs``: a divisão
                    # depende do lado da face).
                    brilho = 1.0 if produto >= LIMITE_TOON else 0.30
                else:
                    brilho = 0.35 + 0.65 * abs(produto)
                profundidade = (p0[1] + p1[1] + p2[1]) / 3.0
                desenhaveis.append((profundidade, triangulo, brilho))

        desenhaveis.sort(key=lambda item: item[0], reverse=True)
        for _, face, brilho in desenhaveis:
            rgb = tuple(canal * brilho for canal in base)
            pontos_svg = " ".join(
                f"{tela[indice][0]:.1f},{tela[indice][1]:.1f}" for indice in face
            )
            cor_face = _rgb_para_hex(rgb)
            partes.append(
                f'<polygon points="{pontos_svg}" fill="{cor_face}" '
                f'stroke="{cor_face}" stroke-width="0.4"/>'
            )
        partes.append("</svg>")
        return "".join(partes)
