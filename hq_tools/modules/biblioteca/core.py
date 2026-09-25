"""Núcleo da biblioteca do projeto (sem dependência do Krita).

A biblioteca é uma pasta com três subpastas (balões, painéis, onomatopeias).
Cada recurso é um arquivo SVG salvo pelo autor, pronto para ser inserido nos
painéis como camada vetorial.
"""

import os
import re
import tempfile
import time
import unicodedata

TIPOS = (
    ("balao", "Balões", "baloes"),
    ("painel", "Painéis", "paineis"),
    ("onomatopeia", "Onomatopeias", "onomatopeias"),
)

TIPO_CHAVE = {chave: rotulo for chave, rotulo, pasta in TIPOS}
TIPO_PASTA = {chave: pasta for chave, rotulo, pasta in TIPOS}

TAMANHO_CM = 15.0
DPI_PADRAO = 300


def pasta_do_tipo(base, tipo):
    """Garante e devolve a subpasta do tipo dentro da biblioteca."""
    if tipo not in TIPO_PASTA:
        raise ValueError("Tipo desconhecido: {0}".format(tipo))
    folder = os.path.join(base, TIPO_PASTA[tipo])
    os.makedirs(folder, exist_ok=True)
    return folder


def slugify(nome):
    """Nome de arquivo seguro a partir de um texto livre (sem acentos)."""
    texto = unicodedata.normalize("NFKD", str(nome))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return texto or "recurso"


def nome_padrao(tipo):
    return "{0}-{1}".format(tipo, time.strftime("%Y%m%d-%H%M%S"))


def caminho_livre(folder, nome):
    """Caminho de arquivo .svg sem colisão (acrescenta sufixo numérico)."""
    base = slugify(nome)
    candidato = os.path.join(folder, "{0}.svg".format(base))
    indice = 2
    while os.path.exists(candidato):
        candidato = os.path.join(folder, "{0}-{1}.svg".format(base, indice))
        indice += 1
    return candidato


def salvar_recurso(svg_text, base, tipo, nome):
    """Salva o SVG na biblioteca e devolve o caminho criado."""
    folder = pasta_do_tipo(base, tipo)
    path = caminho_livre(folder, nome)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=folder, delete=False
    )
    try:
        with handle:
            handle.write(svg_text)
        os.replace(handle.name, path)
    except OSError:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
    return path


def listar_recursos(base, tipo):
    """Lista (nome sem extensão, caminho) dos SVGs da subpasta do tipo."""
    folder = pasta_do_tipo(base, tipo)
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    resultado = []
    for name in names:
        if name.lower().endswith(".svg"):
            resultado.append((os.path.splitext(name)[0], os.path.join(folder, name)))
    return resultado


def tamanho_novo_documento(cm=TAMANHO_CM, dpi=DPI_PADRAO):
    """Lado do documento quadrado (em pixels) para criar um recurso."""
    return int(round(float(cm) * float(dpi) / 2.54))