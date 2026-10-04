"""Máscara de transparência dos painéis (núcleo puro, sem Krita).

Gera os bytes de uma máscara 8 bits (255 = visível) a partir dos retângulos em
fração usados na geração das páginas. O gerador cria a máscara como filho do
grupo "Arte": pintar nas camadas do grupo fica limitado aos painéis; esconder
a máscara no docker de camadas libera a página inteira, que é o fluxo clássico
de quadrinhos.
"""


def retangulo_em_pixels(painel, largura, altura):
    """Converte um painel em fração (x, y, w, h) para pixels, com recorte."""
    x, y, w, h = painel
    x0 = max(0, min(largura, int(round(x * largura))))
    y0 = max(0, min(altura, int(round(y * altura))))
    x1 = max(0, min(largura, int(round((x + w) * largura))))
    y1 = max(0, min(altura, int(round((y + h) * altura))))
    return x0, y0, max(0, x1 - x0), max(0, y1 - y0)


def mascara_dos_paineis(paineis, largura, altura):
    """Bytes da máscara (largura x altura, 8 bits): 255 dentro dos painéis."""
    dados = bytearray(largura * altura)
    for painel in paineis:
        x, y, w, h = retangulo_em_pixels(painel, largura, altura)
        if w <= 0 or h <= 0:
            continue
        linha = b"\xff" * w
        for linha_y in range(y, y + h):
            inicio = linha_y * largura + x
            dados[inicio:inicio + w] = linha
    return bytes(dados)
