"""Resolução do preview do 3D parado.

O preview pode crescer muito quando o docker ocupa a tela inteira. O custo do
render em SVG cresce com a área, então o render parado é limitado a 720 px no
maior lado e ampliado para o tamanho do preview. Durante o gesto o docker usa
um caminho rápido com ``QPainter``, que não passa por SVG.
"""

# Maior lado do render em SVG quando o preview está parado.
LIMITE_PARADO = 720


def resolucao_do_render(largura, altura, limite=LIMITE_PARADO):
    """Tamanho do render, preservando a proporção.

    Devolve ``(largura, altura)`` sem redução quando o maior lado já cabe no
    limite; caso contrário, encolhe os dois lados pelo mesmo fator.
    """
    largura = max(1, int(largura))
    altura = max(1, int(altura))
    limite = max(1, int(limite))
    maior = max(largura, altura)
    if maior <= limite:
        return largura, altura
    fator = limite / float(maior)
    return max(1, int(round(largura * fator))), max(1, int(round(altura * fator)))
