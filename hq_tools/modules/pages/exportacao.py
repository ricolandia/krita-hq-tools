"""Núcleo da exportação de páginas (puro, sem Krita).

O diálogo do gerenciador monta as opções; estas funções decidem o plano de
cada página (nome do arquivo, atalho do ``mergedimage`` ou reamostragem) e
preparam o destino. Quem executa é o docker (extrai os bytes ou abre a cópia,
escala e exporta).

Decisões de 17/10 (`docs/EXPORTACAO.md`): v1 em RGB, PNG/JPG, 72–300 dpi. O
atalho do ``mergedimage`` vale quando a resolução pedida é a da página — é
pixel a pixel idêntico ao export e ~80x mais rápido (69 ms contra 5,5 s por
página A4). CMYK e PDF ficaram fora (sem perfis instalados; o filtro de PDF
não cria o arquivo).
"""

import os

RESOLUCOES = (72, 96, 150, 300)
FORMATOS = ("png", "jpg")


def nome_de_saida(nome_pagina, formato):
    """Nome do arquivo exportado: o da página com a extensão trocada."""
    base = os.path.splitext(os.path.basename(nome_pagina))[0]
    return "{0}.{1}".format(base, formato)


def precisa_reamostrar(dpi_pagina, dpi_pedido):
    """True quando a resolução pedida difere da resolução da página."""
    try:
        return abs(float(dpi_pagina) - float(dpi_pedido)) > 0.01
    except (TypeError, ValueError):
        return True


def usar_atalho(formato, dpi_pagina, dpi_pedido):
    """O ``mergedimage`` do .kra só vale para PNG/JPG na resolução nativa."""
    return formato in FORMATOS and not precisa_reamostrar(dpi_pagina, dpi_pedido)


def dimensoes_reamostradas(largura, altura, dpi_pagina, dpi_pedido):
    """Tamanho em pixels da cópia reamostrada (arredondado; mínimo 1)."""
    fator = float(dpi_pedido) / float(dpi_pagina or dpi_pedido)
    return max(1, int(round(largura * fator))), max(1, int(round(altura * fator)))


def preparar_destino(pasta):
    """Cria a pasta de destino; devolve ``None`` ou a mensagem de erro."""
    if not pasta:
        return "pasta de destino vazia"
    try:
        os.makedirs(pasta, exist_ok=True)
    except OSError as erro:
        return str(erro)
    if not os.path.isdir(pasta):
        return "não é uma pasta: {0}".format(pasta)
    return None
