"""Núcleo dos conjuntos de linhas de perspectiva (puro, sem Krita).

Cada linha é um caminho com exatamente dois nós, um em cada ponta: a reta é
``M`` + ``L`` e a curvilínea é ``M`` + ``A`` (dois pontos de ancoragem e as
alças do arco). Tudo é ``<path>`` porque é o que o importador de SVG do Krita
converte em forma vetorial editável; ``<line>`` não tem garantia de virar
forma.

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
    """Reta entre dois nós (``M`` + ``L``): um caminho de dois pontos."""
    return (
        '<path d="M {0:.1f} {1:.1f} L {2:.1f} {3:.1f}" fill="none" '
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


def frontal(largura, altura, vp_x_fator=0.5):
    """Um ponto: tudo converge para o VP; verticais e horizontais ficam retas."""
    cx = largura * vp_x_fator
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


def frontal_deslocado_esquerda(largura, altura):
    """Um ponto com o VP no terço esquerdo (composição assimétrica)."""
    return frontal(largura, altura, vp_x_fator=1.0 / 3.0)


def frontal_deslocado_direita(largura, altura):
    """Um ponto com o VP no terço direito (composição assimétrica)."""
    return frontal(largura, altura, vp_x_fator=2.0 / 3.0)


def _dois_ou_tres_pontos(largura, altura, hy_fator, vp3_fator=None,
                         vp1_fator=-0.60, vp2_fator=1.60):
    """Dois pontos (``vp3_fator`` None) ou três pontos, com o 3º VP deslocado.

    ``vp1_fator``/``vp2_fator`` são as posições dos VPs em relação à largura
    (os padrões deixam os dois fora do quadro, a distâncias iguais).
    """
    cx = largura / 2.0
    hy = altura * hy_fator
    vp1 = (vp1_fator * largura, hy)
    vp2 = (vp2_fator * largura, hy)
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


def quina_proxima(largura, altura):
    """Dois pontos assimétrico: VP esquerdo perto (parede curta), direito longe."""
    return _dois_ou_tres_pontos(
        largura, altura, 0.5, vp1_fator=-0.10, vp2_fator=2.60
    )


def passaro_nivel_3(largura, altura):
    """Vista de pássaro extrema: horizonte no topo e 3º VP dentro do quadro."""
    return _dois_ou_tres_pontos(largura, altura, 0.05, vp3_fator=0.50)


def verme_nivel_3(largura, altura):
    """Vista de verme extrema: horizonte no fundo e 3º VP dentro do quadro."""
    return _dois_ou_tres_pontos(largura, altura, 0.95, vp3_fator=-0.50)


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


def _rotacionar_ponto(ponto, angulo, largura, altura):
    """Ponto girado em torno do centro do quadro (graus, sentido horário)."""
    cx, cy = largura / 2.0, altura / 2.0
    radianos = math.radians(angulo)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    dx, dy = ponto[0] - cx, ponto[1] - cy
    return (cx + dx * cosseno - dy * seno, cy + dx * seno + dy * cosseno)


def inclinada(largura, altura, angulo=12.0):
    """Dois pontos girado: o "horizonte torto" (câmera inclinada).

    Os VPs e as referências giram antes do recorte, então as três famílias
    saem inclinadas e o quadro continua preenchido de borda a borda.
    """
    cx = largura / 2.0
    hy = altura / 2.0

    def girar(ponto):
        return _rotacionar_ponto(ponto, angulo, largura, altura)

    vp1 = girar((-0.60 * largura, hy))
    vp2 = girar((largura + 0.60 * largura, hy))
    elementos = []
    referencias = [
        girar((cx, indice * altura / 12.0)) for indice in range(13) if indice != 6
    ]
    _guias_retas(elementos, vp1, referencias, largura, altura, LARANJA)
    _guias_retas(elementos, vp2, referencias, largura, altura, CINZA)
    for indice in range(1, 10):
        x = indice * largura / 10.0
        recorte = recortar_reta(girar((x, 0)), girar((x, altura)), largura, altura)
        if recorte is not None:
            (x1, y1), (x2, y2) = recorte
            elementos.append(linha(x1, y1, x2, y2, AZUL))
    recorte = recortar_reta(girar((0, hy)), girar((largura, hy)), largura, altura)
    if recorte is not None:
        (x1, y1), (x2, y2) = recorte
        elementos.append(linha(x1, y1, x2, y2, CINZA, ESPESSURA_EIXO))
    return elementos


def _trecho_na_faixa(ponto_a, ponto_b, y_min, y_max):
    """Trecho da reta por A e B dentro da faixa horizontal (só interpolação)."""
    (x1, y1), (x2, y2) = ponto_a, ponto_b
    if abs(y2 - y1) < 1e-9:
        if y_min - 1e-6 <= y1 <= y_max + 1e-6:
            return (ponto_a, ponto_b)
        return None
    t_min = (y_min - y1) / float(y2 - y1)
    t_max = (y_max - y1) / float(y2 - y1)
    t0, t1 = sorted((t_min, t_max))
    t0, t1 = max(0.0, t0), min(1.0, t1)
    if t0 >= t1:
        return None

    def ponto_em(t):
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    return (ponto_em(t0), ponto_em(t1))


def grade_de_chao(largura, altura):
    """Grade de chão em um ponto, para posicionar figuras no espaço.

    Horizonte a 35% da altura; as travessas seguem o espaçamento real da
    perspectiva (y = horizonte + altura do piso / profundidade), então o
    piso parece um piso, não listras iguais.
    """
    cx = largura / 2.0
    hy = altura * 0.35
    piso = altura - hy
    elementos = []
    # Travessas: da segunda em diante (a primeira seria a própria borda do
    # quadro); para quando a faixa fica mais fina que 5 px.
    profundidade = 2
    while True:
        passo = piso * (1.0 / profundidade - 1.0 / (profundidade + 1.0))
        if passo < 5.0:
            break
        y = hy + piso / float(profundidade)
        elementos.append(linha(0, y, largura, y, CINZA))
        profundidade += 1
    # Profundidade: do VP pelas divisões da borda inferior (cantos incluídos).
    for indice in range(0, 27):
        x = indice * largura / 26.0
        trecho = _trecho_na_faixa((cx, hy), (x, altura), hy, altura)
        if trecho is None:
            continue
        (x1, y1), (x2, y2) = trecho
        elementos.append(linha(x1, y1, x2, y2, LARANJA))
    elementos.append(linha(0, hy, largura, hy, CINZA, ESPESSURA_EIXO))
    return elementos


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
    ("10-frontal-deslocado-esq.svg", "Frontal · deslocado (esq.)", frontal_deslocado_esquerda,
     "Um ponto com o VP no terço esquerdo (composição assimétrica): laranja = profundidade; azul = verticais; cinza = horizontais e horizonte"),
    ("11-frontal-deslocado-dir.svg", "Frontal · deslocado (dir.)", frontal_deslocado_direita,
     "Um ponto com o VP no terço direito (composição assimétrica): laranja = profundidade; azul = verticais; cinza = horizontais e horizonte"),
    ("12-quina-proxima.svg", "Quina próxima", quina_proxima,
     "Dois pontos assimétrico: VP esquerdo perto (parede curta e íngreme) e direito longe (parede longa); laranja = VP esquerdo; cinza = VP direito; azul = verticais"),
    ("13-passaro-extremo.svg", "Pássaro · extremo", passaro_nivel_3,
     "Vista de pássaro extrema: horizonte a 5% da altura e 3º VP dentro do quadro (convergência forte)"),
    ("14-verme-extremo.svg", "Verme · extremo", verme_nivel_3,
     "Vista de verme extrema: horizonte a 95% da altura e 3º VP dentro do quadro (convergência forte)"),
    ("15-horizonte-inclinado.svg", "Horizonte inclinado", inclinada,
     "Horizonte torto (câmera inclinada): o conjunto de dois pontos girado 12°; mesmas cores, todas as famílias inclinadas"),
    ("16-grade-de-chao.svg", "Grade de chão", grade_de_chao,
     "Grade de chão em um ponto, para posicionar figuras: laranja = profundidade; cinza = travessas em espaçamento de perspectiva; horizonte a 35%"),
)


def por_arquivo(nome_arquivo):
    for arquivo, titulo, construtor, legenda in PRESETS:
        if arquivo == nome_arquivo:
            return titulo, construtor, legenda
    raise KeyError("preset desconhecido: {0}".format(nome_arquivo))


def montar_svg(nome, elementos, largura, altura, legenda, deslocamento=None):
    """SVG completo; ``deslocamento`` move o conjunto (usado na inserção)."""
    corpo = list(elementos)
    if deslocamento:
        dx, dy = deslocamento
        if dx or dy:
            corpo = (
                ['<g transform="translate({0:.1f} {1:.1f})">'.format(dx, dy)]
                + corpo
                + ["</g>"]
            )
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
            'viewBox="0 0 {0} {1}">'.format(largura, altura),
            "<!-- HQ Tools: {0} | {1} | gerado por scripts/gerar-perspectivas.py -->".format(
                nome, legenda
            ),
            *corpo,
            "</svg>",
            "",
        ]
    )


def gerar(nome_arquivo, largura=900, altura=1200, deslocamento=None):
    """Texto do SVG de um preset, na proporção pedida (o docker usa a da seleção)."""
    _, construtor, legenda = por_arquivo(nome_arquivo)
    return montar_svg(
        nome_arquivo,
        construtor(largura, altura),
        largura,
        altura,
        legenda,
        deslocamento=deslocamento,
    )


def gerar_todos(destino, largura=900, altura=1200):
    os.makedirs(destino, exist_ok=True)
    gerados = []
    for arquivo, _, _, _ in PRESETS:
        caminho = os.path.join(destino, arquivo)
        with open(caminho, "w", encoding="utf-8") as saida:
            saida.write(gerar(arquivo, largura, altura))
        gerados.append(caminho)
    return gerados
