"""Conversão de coordenadas do canvas para pixels do documento (puro, sem Krita).

O preview flutuante do visualizador 3D vive em coordenadas do widget (o
viewport do canvas). Para "assar" a referência no documento, o retângulo
precisa virar pixels da imagem. A conta usa o ponto da imagem que está no
centro do widget (``Canvas.preferredCenter()``), o zoom efetivo, a rotação, o
espelhamento e, quando o centro preferido não existe, o deslocamento (pan) das
barras de rolagem.
"""

import math


def deslocamento_da_barra(minimo, maximo, valor):
    """Deslocamento (em px do widget) de uma barra de rolagem, relativo ao centro.

    A barra centrada devolve 0; rolada para o fim, um valor negativo. É a
    mesma conta que os exemplos da comunidade usam para mapear o canvas.
    """
    meio = (minimo + maximo) / 2.0
    return -(valor - meio)


def widget_para_imagem(ponto, centro_widget, centro_imagem, zoom,
                       rotacao=0.0, pan=(0.0, 0.0), espelhado=False):
    """Converte um ponto do widget para pixels da imagem."""
    dx = ponto[0] - centro_widget[0] - pan[0]
    dy = ponto[1] - centro_widget[1] - pan[1]
    if espelhado:
        dx = -dx
    radianos = math.radians(-rotacao)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    girado_x = dx * cosseno - dy * seno
    girado_y = dx * seno + dy * cosseno
    return (
        centro_imagem[0] + girado_x / zoom,
        centro_imagem[1] + girado_y / zoom,
    )


def imagem_para_widget(ponto, centro_widget, centro_imagem, zoom,
                       rotacao=0.0, pan=(0.0, 0.0), espelhado=False):
    """Converte um ponto em pixels da imagem para coordenadas do widget.

    Inversa de :func:`widget_para_imagem`; serve para posicionar a janela
    flutuante sobre a seleção (que vem em pixels da imagem).
    """
    dx = (ponto[0] - centro_imagem[0]) * zoom
    dy = (ponto[1] - centro_imagem[1]) * zoom
    radianos = math.radians(rotacao)
    cosseno, seno = math.cos(radianos), math.sin(radianos)
    girado_x = dx * cosseno - dy * seno
    girado_y = dx * seno + dy * cosseno
    if espelhado:
        girado_x = -girado_x
    return (
        centro_widget[0] + girado_x + pan[0],
        centro_widget[1] + girado_y + pan[1],
    )


def retangulo_para_widget(retangulo, centro_widget, centro_imagem, zoom,
                          rotacao=0.0, pan=(0.0, 0.0), espelhado=False):
    """Retângulo em pixels da imagem para o widget (caixa envolvente)."""
    x, y, w, h = retangulo
    cantos = (
        imagem_para_widget((x, y), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        imagem_para_widget((x + w, y), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        imagem_para_widget((x, y + h), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        imagem_para_widget((x + w, y + h), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
    )
    xs = [canto[0] for canto in cantos]
    ys = [canto[1] for canto in cantos]
    x0 = int(math.floor(min(xs)))
    y0 = int(math.floor(min(ys)))
    x1 = int(math.ceil(max(xs)))
    y1 = int(math.ceil(max(ys)))
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def retangulo_para_imagem(retangulo, centro_widget, centro_imagem, zoom,
                          rotacao=0.0, pan=(0.0, 0.0), espelhado=False):
    """Retângulo (x, y, w, h) do widget em pixels da imagem (x, y, w, h).

    Com rotação, devolve a caixa envolvente dos quatro cantos (a camada é
    alinhada aos eixos); sem rotação, o resultado é exato.
    """
    x, y, w, h = retangulo
    cantos = (
        widget_para_imagem((x, y), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        widget_para_imagem((x + w, y), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        widget_para_imagem((x, y + h), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
        widget_para_imagem((x + w, y + h), centro_widget, centro_imagem, zoom, rotacao, pan, espelhado),
    )
    xs = [canto[0] for canto in cantos]
    ys = [canto[1] for canto in cantos]
    x0 = int(math.floor(min(xs)))
    y0 = int(math.floor(min(ys)))
    x1 = int(math.ceil(max(xs)))
    y1 = int(math.ceil(max(ys)))
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def centro_da_vista(centro_widget, centro_imagem, zoom,
                    rotacao=0.0, pan=(0.0, 0.0), espelhado=False):
    """Ponto da imagem que está no centro do widget (o que está na tela).

    Serve para a inserção "onde você está olhando": o ponto devolvido é o
    centro da vista atual, com pan, zoom, rotação e espelho aplicados.
    """
    return widget_para_imagem(
        centro_widget, centro_widget, centro_imagem, zoom, rotacao, pan, espelhado
    )


def encaixe_central(caixa, largura, altura, ampliar=False):
    """(x, y, escala) para a imagem caber centrada na caixa.

    ``caixa`` é ``(x, y, largura, altura)``; sem ``ampliar``, a escala nunca
    passa de 1 (a imagem só reduz), como pedido na inserção de balões,
    onomatopeias e recursos da biblioteca.
    """
    x, y, largura_caixa, altura_caixa = caixa
    if largura <= 0 or altura <= 0 or largura_caixa <= 0 or altura_caixa <= 0:
        return (x, y, 1.0)
    escala = min(float(largura_caixa) / largura, float(altura_caixa) / altura)
    if not ampliar:
        escala = min(1.0, escala)
    return (
        x + (largura_caixa - largura * escala) / 2.0,
        y + (altura_caixa - altura * escala) / 2.0,
        escala,
    )


def intersecao_com_documento(retangulo, largura, altura):
    """Parte visível do retângulo dentro do documento (pode ser vazia)."""
    x, y, w, h = retangulo
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(largura, x + w)
    y1 = min(altura, y + h)
    visivel_w = max(0, x1 - x0)
    visivel_h = max(0, y1 - y0)
    if visivel_w == 0 or visivel_h == 0:
        return x0, y0, 0, 0
    return x0, y0, visivel_w, visivel_h
