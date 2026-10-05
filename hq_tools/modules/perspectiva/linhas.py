"""Núcleo dos conjuntos de linhas de perspectiva (puro, sem Krita).

Cada linha do SVG tem exatamente dois nós, um em cada ponta: as retas são
``<line>`` e as curvilíneas são ``<path>`` com um único ``M`` e um único ``A``
(dois pontos de ancoragem e as alças do arco), para o desenho continuar
editável quando importado como vetor no Krita.

Convenção de cores (uma família por cor, legenda no comentário de cada
arquivo):

- azul: família vertical (ou a família que converge para o 3º ponto de fuga);
- laranja: família de profundidade (VP esquerdo; nas curvilíneas, os eixos
  retos e a família do centro);
- cinza: família do VP direito, horizontais de apoio e horizonte.

A pesquisa e o catálogo estão em ``docs/PERSPECTIVAS.md``. Os SVGs prontos
ficam em ``hq_tools/resources/perspectivas/`` e são gerados por
``scripts/gerar-perspectivas.py`` (o docker gera na proporção da seleção).
"""

import math
import os

AZUL = "#2f6fd0"
LARANJA = "#e8843c"
CINZA = "#b0b4ba"

ESPESSURA = 1.2
ESPESSURA_EIXO = 2.0


def linha(x1, y1, x2, y2, cor, espessura=ESPESSURA):
    return (
        '<line x1="{0:.1f}" y1="{1:.1f}" x2="{2:.1f}" y2="{3:.1f}" '
        'stroke="{4}" stroke-width="{5:.1f}"/>'
    ).format(x1, y1, x2, y2, cor, espessura)


def arco(x1, y1, x2, y2, raio, cor, sweep=0, espessura=ESPESSURA):
    """Arco de círculo entre dois nós (``M`` + ``A``, sem nó intermediário)."""
    return (
        '<path d="M {0:.1f} {1:.1f} A {4:.1f} {4:.1f} 0 0 {5} {2:.1f} {3:.1f}" '
        'fill="none" stroke="{6}" stroke-width="{7:.1f}"/>'
    ).format(x1, y1, x2, y2, raio, sweep, cor, espessura)


def recortar_reta(ponto_a, ponto_b, largura, altura):
    """Os dois pontos em que a reta infinita por A e B cruza a borda do quadro.

    Serve para cada guia reta sair de borda a borda com dois nós, mesmo quando
    o ponto de fuga está fora do quadro.
    """
    x1, y1 = ponto_a
    x2, y2 = ponto_b
    dx = x2 - x1
    dy = y2 - y1
    pontos = []
    if abs(dx) > 1e-9:
        for x in (0.0, float(largura)):
            y = y1 + (x - x1) / dx * dy
            if -1e-6 <= y <= altura + 1e-6:
                pontos.append((x, min(max(y, 0.0), float(altura))))
    if abs(dy) > 1e-9:
        for y in (0.0, float(altura)):
            x = x1 + (y - y1) / dy * dx
            if -1e-6 <= x <= largura + 1e-6:
                pontos.append((min(max(x, 0.0), float(largura)), y))
    unicos = []
    for ponto in pontos:
        if all(
            abs(ponto[0] - outro[0]) > 1e-6 or abs(ponto[1] - outro[1]) > 1e-6
            for outro in unicos
        ):
            unicos.append(ponto)
    if len(unicos) < 2:
        return None
    melhor = None
    for indice in range(len(unicos)):
        for outro in range(indice + 1, len(unicos)):
            distancia = (unicos[indice][0] - unicos[outro][0]) ** 2 + (
                unicos[indice][1] - unicos[outro][1]
            ) ** 2
            if melhor is None or distancia > melhor[0]:
                melhor = (distancia, unicos[indice], unicos[outro])
    return melhor[1], melhor[2]


def _guias_retas(elementos, origem, referencias, largura, altura, cor):
    for referencia in referencias:
        recorte = recortar_reta(origem, referencia, largura, altura)
        if recorte is None:
            continue
        (x1, y1), (x2, y2) = recorte
        elementos.append(linha(x1, y1, x2, y2, cor))


def frontal(largura, altura):
    """Um ponto: tudo converge para o VP central; verticais e horizontais ficam retas."""
    cx = largura / 2.0
    hy = altura / 2.0
    elementos = []
    for indice in range(1, 10):
        x = indice * largura / 10.0
        elementos.append(linha(x, 0, x, altura, AZUL))
    for indice in range(1, 10):
        y = indice * altura / 10.0
        elementos.append(linha(0, y, largura, y, CINZA))
    for indice in range(24):
        angulo = 2.0 * math.pi * indice / 24.0 + math.pi / 24.0
        alvo = (
            cx + math.cos(angulo) * 10.0 * largura,
            hy + math.sin(angulo) * 10.0 * altura,
        )
        recorte = recortar_reta((cx, hy), alvo, largura, altura)
        if recorte is not None:
            (x1, y1), (x2, y2) = recorte
            elementos.append(linha(x1, y1, x2, y2, LARANJA))
    elementos.append(linha(0, hy, largura, hy, CINZA, ESPESSURA_EIXO))
    return elementos


def _dois_ou_tres_pontos(largura, altura, hy_fator, vp3_fator=None):
    """Dois pontos (``vp3_fator`` None) ou três pontos, com o 3º VP deslocado."""
    cx = largura / 2.0
    hy = altura * hy_fator
    vp1 = (-0.60 * largura, hy)
    vp2 = (largura + 0.60 * largura, hy)
    elementos = []
    referencias_verticais = [(cx, indice * altura / 12.0) for indice in range(13)]
    referencias_verticais = [
        ponto for ponto in referencias_verticais if abs(ponto[1] - hy) > 1e-6
    ]
    _guias_retas(elementos, vp1, referencias_verticais, largura, altura, LARANJA)
    _guias_retas(elementos, vp2, referencias_verticais, largura, altura, CINZA)
    if vp3_fator is None:
        for indice in range(1, 10):
            x = indice * largura / 10.0
            elementos.append(linha(x, 0, x, altura, AZUL))
    else:
        vp3 = (cx, hy + altura * vp3_fator)
        referencias_horizontais = [(indice * largura / 12.0, hy) for indice in range(13)]
        _guias_retas(elementos, vp3, referencias_horizontais, largura, altura, AZUL)
    elementos.append(linha(0, hy, largura, hy, CINZA, ESPESSURA_EIXO))
    return elementos


def dois_pontos(largura, altura):
    return _dois_ou_tres_pontos(largura, altura, 0.5)


def tres_pontos(largura, altura):
    """Três pontos neutro: horizonte no meio e 3º VP moderado abaixo."""
    return _dois_ou_tres_pontos(largura, altura, 0.5, vp3_fator=1.6)


def passaro_nivel_1(largura, altura):
    return _dois_ou_tres_pontos(largura, altura, 0.30, vp3_fator=1.4)


def passaro_nivel_2(largura, altura):
    return _dois_ou_tres_pontos(largura, altura, 0.15, vp3_fator=0.9)


def verme_nivel_1(largura, altura):
    return _dois_ou_tres_pontos(largura, altura, 0.70, vp3_fator=-1.4)


def verme_nivel_2(largura, altura):
    return _dois_ou_tres_pontos(largura, altura, 0.85, vp3_fator=-0.9)


def _curvilinea(largura, altura, centro, divisoes=8):
    """Quatro pontos (arcos entre pares de VPs) e, com ``centro``, cinco pontos."""
    cx = largura / 2.0
    cy = altura / 2.0
    raio_visao = 0.75 * max(largura, altura)
    esquerda = (cx - raio_visao, cy)
    direita = (cx + raio_visao, cy)
    zenite = (cx, cy - raio_visao)
    nadir = (cx, cy + raio_visao)
    elementos = []
    for indice in range(1, divisoes + 1):
        d = raio_visao * indice / divisoes
        k = (raio_visao * raio_visao - d * d) / (2.0 * d)
        r = math.hypot(k, raio_visao)
        # Bojo esquerdo (cruza o horizonte em cx - d) e direito (cx + d).
        elementos.append(
            arco(zenite[0], zenite[1], nadir[0], nadir[1], r, AZUL, sweep=0)
        )
        elementos.append(
            arco(zenite[0], zenite[1], nadir[0], nadir[1], r, AZUL, sweep=1)
        )
    for indice in range(1, divisoes + 1):
        d = raio_visao * indice / divisoes
        k = (raio_visao * raio_visao - d * d) / (2.0 * d)
        r = math.hypot(k, raio_visao)
        # Bojo de cima (cruza a vertical central em cy - d) e de baixo (cy + d).
        elementos.append(
            arco(esquerda[0], esquerda[1], direita[0], direita[1], r, CINZA, sweep=1)
        )
        elementos.append(
            arco(esquerda[0], esquerda[1], direita[0], direita[1], r, CINZA, sweep=0)
        )
    elementos.append(
        linha(esquerda[0], esquerda[1], direita[0], direita[1], LARANJA, ESPESSURA_EIXO)
    )
    elementos.append(
        linha(zenite[0], zenite[1], nadir[0], nadir[1], LARANJA, ESPESSURA_EIXO)
    )
    if centro:
        for indice in range(16):
            angulo = 2.0 * math.pi * indice / 16.0 + math.pi / 16.0
            alvo = (
                cx + math.cos(angulo) * 10.0 * largura,
                cy + math.sin(angulo) * 10.0 * altura,
            )
            recorte = recortar_reta((cx, cy), alvo, largura, altura)
            if recorte is not None:
                (x1, y1), (x2, y2) = recorte
                elementos.append(linha(x1, y1, x2, y2, LARANJA))
    return elementos


def curvilinea_4_pontos(largura, altura):
    return _curvilinea(largura, altura, centro=False)


def curvilinea_5_pontos(largura, altura):
    return _curvilinea(largura, altura, centro=True)


PRESETS = (
    ("01-frontal.svg", "Frontal (1 ponto)", frontal,
     "Um ponto: laranja = profundidade; azul = verticais; cinza = horizontais e horizonte"),
    ("02-dois-pontos.svg", "Dois pontos", dois_pontos,
     "Dois pontos: laranja = VP esquerdo; cinza = VP direito; azul = verticais"),
    ("03-tres-pontos.svg", "Três pontos", tres_pontos,
     "Três pontos: laranja = VP esquerdo; cinza = VP direito; azul = verticais (3º VP)"),
    ("04-passaro-nivel-1.svg", "Pássaro · nível 1", passaro_nivel_1,
     "Vista de pássaro suave: horizonte a 30% da altura, 3º VP abaixo"),
    ("05-passaro-nivel-2.svg", "Pássaro · nível 2", passaro_nivel_2,
     "Vista de pássaro forte: horizonte a 15% da altura, 3º VP abaixo"),
    ("06-verme-nivel-1.svg", "Verme · nível 1", verme_nivel_1,
     "Vista de verme suave: horizonte a 70% da altura, 3º VP acima"),
    ("07-verme-nivel-2.svg", "Verme · nível 2", verme_nivel_2,
     "Vista de verme forte: horizonte a 85% da altura, 3º VP acima"),
    ("08-curvilinea-4-pontos.svg", "Curvilínea · 4 pontos", curvilinea_4_pontos,
     "Curvilínea 4 pontos: azul = arcos verticais; cinza = arcos horizontais; laranja = eixos retos"),
    ("09-curvilinea-5-pontos.svg", "Curvilínea · 5 pontos", curvilinea_5_pontos,
     "Curvilínea 5 pontos: como a de 4, mais a família reta do VP central (laranja)"),
)


def por_arquivo(nome_arquivo):
    for arquivo, titulo, construtor, legenda in PRESETS:
        if arquivo == nome_arquivo:
            return titulo, construtor, legenda
    raise KeyError("preset desconhecido: {0}".format(nome_arquivo))


def montar_svg(nome, elementos, largura, altura, legenda):
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
            'viewBox="0 0 {0} {1}">'.format(largura, altura),
            "<!-- HQ Tools: {0} | {1} | gerado por scripts/gerar-perspectivas.py -->".format(
                nome, legenda
            ),
            *elementos,
            "</svg>",
            "",
        ]
    )


def gerar(nome_arquivo, largura=900, altura=1200):
    """Texto do SVG de um preset, na proporção pedida (o docker usa a da seleção)."""
    _, construtor, legenda = por_arquivo(nome_arquivo)
    return montar_svg(nome_arquivo, construtor(largura, altura), largura, altura, legenda)


def gerar_todos(destino, largura=900, altura=1200):
    os.makedirs(destino, exist_ok=True)
    gerados = []
    for arquivo, _, _, _ in PRESETS:
        caminho = os.path.join(destino, arquivo)
        with open(caminho, "w", encoding="utf-8") as saida:
            saida.write(gerar(arquivo, largura, altura))
        gerados.append(caminho)
    return gerados
