"""Núcleo do moodboard (quadro de referências), sem dependência do Krita.

O quadro é um documento largo com uma grade de células; cada referência é um
JPG comprimido na pasta ``moodboard/`` do projeto, inserido como camada de
arquivo (linkada, para o ``.kra`` ficar leve) e posicionado por uma máscara de
transformação com escala e translação.

O formato da máscara foi validado no PoC de 06/10/2026 (Krita 5.3.4): a escala
vai em ``scaleX``/``scaleY`` com o centro original em (0, 0), e o deslocamento
em ``transformedCenter``; a matriz ``flattenedPerspectiveTransform`` sozinha é
ignorada no modo livre.
"""

import json
import os

from ..biblioteca.core import caminho_livre, slugify

CELULA = 640
ESPACO = 48
MARGEM = 48
COLUNAS = 8
LINHAS_MINIMAS = 4
LARGURA = MARGEM * 2 + COLUNAS * CELULA + (COLUNAS - 1) * ESPACO
ALTURA = MARGEM * 2 + LINHAS_MINIMAS * CELULA + (LINHAS_MINIMAS - 1) * ESPACO

MAX_LADO = 1600
QUALIDADE = 85

EXTENSOES = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
PASTA = "moodboard"
ARQUIVO_QUADRO = "moodboard.kra"
ARQUIVO_LAYOUT = "moodboard.json"


def posicao(indice):
    """Canto superior esquerdo da célula do índice (grade de COLUNAS colunas)."""
    coluna = indice % COLUNAS
    linha = indice // COLUNAS
    return (
        MARGEM + coluna * (CELULA + ESPACO),
        MARGEM + linha * (CELULA + ESPACO),
    )


def encaixe(largura, altura):
    """Escala (no máximo 1) para a imagem caber na célula, sem distorcer."""
    if largura <= 0 or altura <= 0:
        return 1.0
    return min(1.0, float(CELULA) / largura, float(CELULA) / altura)


def destino(indice, largura, altura):
    """Posição e escala da referência na célula: centrada, sem ampliar."""
    escala = encaixe(largura, altura)
    x_celula, y_celula = posicao(indice)
    return (
        x_celula + (CELULA - largura * escala) / 2.0,
        y_celula + (CELULA - altura * escala) / 2.0,
        escala,
    )


def altura_necessaria(total):
    """Altura do quadro para ``total`` referências (cresce em linhas)."""
    linhas = max(LINHAS_MINIMAS, (total + COLUNAS - 1) // COLUNAS)
    return MARGEM * 2 + linhas * CELULA + (linhas - 1) * ESPACO


def encaixe_em(x, y, largura_caixa, altura_caixa, largura, altura):
    """Posição e escala para a imagem caber centrada numa caixa (a seleção)."""
    if largura <= 0 or altura <= 0 or largura_caixa <= 0 or altura_caixa <= 0:
        return (x, y, 1.0)
    escala = min(float(largura_caixa) / largura, float(altura_caixa) / altura)
    return (
        x + (largura_caixa - largura * escala) / 2.0,
        y + (altura_caixa - altura * escala) / 2.0,
        escala,
    )


def xml_transform(escala, dx, dy):
    """XML da máscara de transformação (formato validado no PoC)."""
    return (
        '<transform_params>'
        '<main id="tooltransformparams"/>'
        '<data mode="0"><free_transform>'
        '<transformedCenter type="pointf" x="{dx:.3f}" y="{dy:.3f}"/>'
        '<originalCenter type="pointf" x="0" y="0"/>'
        '<rotationCenterOffset type="pointf" x="0" y="0"/>'
        '<transformAroundRotationCenter value="0" type="value"/>'
        '<aX value="0" type="value"/><aY value="0" type="value"/><aZ value="0" type="value"/>'
        '<cameraPos z="1024" type="vector3d" x="0" y="0"/>'
        '<scaleX value="{escala:.6f}" type="value"/>'
        '<scaleY value="{escala:.6f}" type="value"/>'
        '<shearX value="0" type="value"/><shearY value="0" type="value"/>'
        '<keepAspectRatio value="0" type="value"/>'
        '<flattenedPerspectiveTransform m11="1" m12="0" m13="0" m21="0" m22="1" '
        'm23="0" m31="0" m32="0" m33="1" type="transform"/>'
        '<filterId value="Bicubic" type="value"/>'
        '</free_transform></data></transform_params>'
    ).format(escala=escala, dx=dx, dy=dy)


def nome_arquivo(nome):
    """Nome seguro (slug) com extensão .jpg para a referência comprimida."""
    return slugify(os.path.splitext(os.path.basename(nome))[0]) + ".jpg"


def caminho_referencia(pasta, nome):
    """Caminho livre na pasta para a referência comprimida (sufixo se colidir)."""
    return caminho_livre(pasta, os.path.splitext(os.path.basename(nome))[0], ".jpg")


def listar_referencias(pasta):
    """(nome sem extensão, caminho) das referências da pasta, em ordem."""
    try:
        nomes = sorted(os.listdir(pasta))
    except OSError:
        return []
    resultado = []
    for nome in nomes:
        if nome.lower().endswith(EXTENSOES):
            resultado.append((os.path.splitext(nome)[0], os.path.join(pasta, nome)))
    return resultado


def apagar_referencia(path):
    """Apaga o arquivo da referência (só extensões de imagem entram aqui)."""
    if os.path.splitext(path)[1].lower() not in EXTENSOES:
        raise ValueError("O arquivo não é uma referência de imagem.")
    os.remove(path)


def item_de_layout(arquivo, x, y, escala, largura, altura, camada=""):
    """Item do layout do quadro (posição da referência e id da camada)."""
    return {
        "arquivo": arquivo,
        "x": round(float(x), 3),
        "y": round(float(y), 3),
        "escala": round(float(escala), 6),
        "largura": int(largura),
        "altura": int(altura),
        "camada": str(camada or ""),
    }


def layout_path(pasta):
    return os.path.join(pasta, ARQUIVO_LAYOUT)


def carregar_layout(pasta):
    """Itens do layout do quadro; ignora os que perderam o arquivo."""
    try:
        with open(layout_path(pasta), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return []
    itens = dados.get("itens") if isinstance(dados, dict) else None
    if not isinstance(itens, list):
        return []
    validos = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        nome = item.get("arquivo")
        if not isinstance(nome, str) or not nome:
            continue
        if os.path.exists(os.path.join(pasta, nome)):
            validos.append(item)
    return validos


def salvar_layout(pasta, itens):
    """Grava o layout do quadro de forma atômica."""
    caminho = layout_path(pasta)
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump({"itens": list(itens)}, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)
