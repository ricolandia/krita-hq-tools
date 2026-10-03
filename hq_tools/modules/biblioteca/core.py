"""Núcleo da biblioteca do projeto (sem dependência do Krita).

A biblioteca é uma pasta com três subpastas (balões, painéis, onomatopeias).
Cada recurso é um arquivo SVG salvo pelo autor, pronto para ser inserido nos
painéis como camada vetorial.
"""

import os
import re
import shutil
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


def caminho_livre(folder, nome, extensao=".svg"):
    """Caminho de arquivo sem colisão (acrescenta sufixo numérico)."""
    base = slugify(nome)
    candidato = os.path.join(folder, "{0}{1}".format(base, extensao))
    indice = 2
    while os.path.exists(candidato):
        candidato = os.path.join(folder, "{0}-{1}{2}".format(base, indice, extensao))
        indice += 1
    return candidato


def salvar_bytes(dados, base, tipo, nome, extensao=".svg"):
    """Salva bytes (SVG ou PNG) na biblioteca e devolve o caminho criado."""
    folder = pasta_do_tipo(base, tipo)
    path = caminho_livre(folder, nome, extensao)
    handle = tempfile.NamedTemporaryFile("wb", dir=folder, delete=False)
    try:
        with handle:
            handle.write(dados)
        os.replace(handle.name, path)
    except OSError:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
    return path


def salvar_recurso(svg_text, base, tipo, nome):
    """Salva o SVG na biblioteca e devolve o caminho criado."""
    return salvar_bytes(svg_text.encode("utf-8"), base, tipo, nome, ".svg")


def listar_recursos(base, tipo):
    """Lista (nome sem extensão, caminho) dos recursos da subpasta do tipo."""
    folder = pasta_do_tipo(base, tipo)
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    resultado = []
    for name in names:
        if name.lower().endswith((".svg", ".png")):
            resultado.append((os.path.splitext(name)[0], os.path.join(folder, name)))
    return resultado


def renomear_recurso(path, novo_nome):
    """Renomeia o arquivo do recurso, preservando a extensão.

    Devolve o novo caminho. Se o nome normalizado for o mesmo, devolve o
    caminho original sem tocar no arquivo; se já houver outro recurso com o
    nome pedido, levanta ``FileExistsError`` (nada é sobrescrito).
    """
    folder = os.path.dirname(path)
    extensao = os.path.splitext(path)[1].lower()
    destino = os.path.join(folder, "{0}{1}".format(slugify(novo_nome), extensao))
    if os.path.abspath(destino) == os.path.abspath(path):
        return path
    if os.path.exists(destino):
        raise FileExistsError(
            "Já existe um recurso chamado {0}.".format(os.path.basename(destino))
        )
    os.rename(path, destino)
    return destino


def duplicar_recurso(path, novo_nome=None):
    """Copia o recurso na mesma pasta e devolve o caminho da cópia.

    Sem ``novo_nome``, usa o nome atual com o sufixo ``-copia`` (e número, se
    precisar). Com ``novo_nome``, recusa sobrescrever um recurso existente.
    """
    folder = os.path.dirname(path)
    extensao = os.path.splitext(path)[1]
    if novo_nome:
        destino = os.path.join(folder, "{0}{1}".format(slugify(novo_nome), extensao))
        if os.path.exists(destino):
            raise FileExistsError(
                "Já existe um recurso chamado {0}.".format(os.path.basename(destino))
            )
    else:
        base = os.path.splitext(os.path.basename(path))[0]
        destino = caminho_livre(folder, "{0}-copia".format(base), extensao)
    shutil.copy2(path, destino)
    return destino


def apagar_recurso(path):
    """Apaga o arquivo do recurso (a confirmação é responsabilidade da interface).

    Só aceita SVG ou PNG, para um caminho errado não levar outro arquivo junto.
    """
    if os.path.splitext(path)[1].lower() not in (".svg", ".png"):
        raise ValueError("O arquivo não é um recurso (SVG ou PNG).")
    os.remove(path)


def tamanho_novo_documento(cm=TAMANHO_CM, dpi=DPI_PADRAO):
    """Lado do documento quadrado (em pixels) para criar um recurso."""
    return int(round(float(cm) * float(dpi) / 2.54))