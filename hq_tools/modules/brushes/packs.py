"""Packs de pincéis da comunidade (kit curado), sem dependência do Krita.

Cada pack é uma subpasta de ``resources/brushes/<pack>/`` com os arquivos
originais do autor organizados por tipo (``paintoppresets``, ``brushes``,
``patterns``, ``palettes``), um ``LICENSE.txt`` e um ``FONTE.md``. A
instalação copia os arquivos para as pastas de recursos do usuário do Krita,
que são carregadas na inicialização do programa.
"""

import os
import re
import shutil

TIPOS = ("paintoppresets", "brushes", "patterns", "palettes")
FONTE_NOME = "FONTE.md"
LICENCA_NOME = "LICENSE.txt"


def listar_packs(brushes_dir):
    """Devolve ``{nome do pack: caminho}`` para as subpastas com FONTE.md."""
    resultado = {}
    if not os.path.isdir(brushes_dir):
        return resultado
    for nome in sorted(os.listdir(brushes_dir)):
        caminho = os.path.join(brushes_dir, nome)
        if os.path.isdir(caminho) and os.path.isfile(os.path.join(caminho, FONTE_NOME)):
            resultado[nome] = caminho
    return resultado


def pack_info(pack_dir):
    """Lê o FONTE.md como dicionário (linhas ``Chave: valor``)."""
    info = {"nome": os.path.basename(pack_dir)}
    caminho = os.path.join(pack_dir, FONTE_NOME)
    if not os.path.isfile(caminho):
        return info
    try:
        with open(caminho, "r", encoding="utf-8") as handle:
            for linha in handle:
                linha = linha.strip()
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    chave = chave.strip().lstrip("-").strip()
                    info[chave.lower()] = valor.strip()
    except OSError:
        pass
    return info


def pack_license(pack_dir):
    """Texto da licença do pack (LICENSE.txt), ou mensagem padrão."""
    caminho = os.path.join(pack_dir, LICENCA_NOME)
    if not os.path.isfile(caminho):
        return "Sem arquivo de licença neste pack."
    try:
        with open(caminho, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return "Não foi possível ler a licença."


def arquivos_por_tipo(pack_dir):
    """Devolve ``{tipo: [caminhos absolutos]}`` dos arquivos do pack."""
    resultado = {}
    for tipo in TIPOS:
        pasta = os.path.join(pack_dir, tipo)
        if not os.path.isdir(pasta):
            continue
        arquivos = []
        for nome in sorted(os.listdir(pasta)):
            caminho = os.path.join(pasta, nome)
            if os.path.isfile(caminho) and not nome.startswith("."):
                arquivos.append(caminho)
        if arquivos:
            resultado[tipo] = arquivos
    return resultado


def preset_names(pack_dir):
    """Nomes (sem extensão) dos presets do pack (paintoppresets)."""
    pasta = os.path.join(pack_dir, "paintoppresets")
    if not os.path.isdir(pasta):
        return []
    nomes = []
    for nome in sorted(os.listdir(pasta)):
        if nome.lower().endswith((".kpp", ".myb")):
            nomes.append(os.path.splitext(nome)[0])
    return nomes


def _preset_chunk_xml(caminho):
    """Extrai o XML do chunk tEXt 'preset' de um .kpp (PNG com anotação)."""
    try:
        with open(caminho, "rb") as handle:
            dados = handle.read()
    except OSError:
        return None
    offset = 8
    while offset + 8 <= len(dados):
        tamanho = int.from_bytes(dados[offset:offset + 4], "big")
        tipo = dados[offset + 4:offset + 8].decode("latin1", "replace")
        if tipo == "tEXt":
            texto = dados[offset + 8:offset + 8 + tamanho]
            if texto.startswith(b"preset\0"):
                return texto[len(b"preset\0"):].decode("utf-8", "replace")
        if tipo == "IEND":
            break
        offset += 12 + tamanho
    return None


def _preset_internal_name(caminho):
    """Nome interno do preset (do XML dentro do .kpp), ou None."""
    xml = _preset_chunk_xml(caminho)
    if not xml:
        return None
    match = re.search(r'<param name="name" value="([^"]*)"', xml)
    if match:
        return match.group(1)
    return None


def preset_aliases(pack_dir):
    """Aliases por preset: ``(nome do arquivo, nome interno)``.

    O Krita lista os presets pelo nome interno (que pode diferir do nome do
    arquivo); este par permite casar os dois no ``resources("preset")``.
    """
    pasta = os.path.join(pack_dir, "paintoppresets")
    if not os.path.isdir(pasta):
        return []
    aliases = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.lower().endswith((".kpp", ".myb")):
            continue
        nome_arquivo = os.path.splitext(nome)[0]
        interno = _preset_internal_name(os.path.join(pasta, nome))
        aliases.append((nome_arquivo, interno or nome_arquivo))
    return aliases


def instalar_pack(pack_dir, destinos):
    """Copia os arquivos do pack para as pastas de recursos do usuário.

    ``destinos`` é ``{tipo: pasta_destino}``; devolve o total copiado.
    """
    total = 0
    for tipo, arquivos in arquivos_por_tipo(pack_dir).items():
        destino = destinos.get(tipo)
        if not destino:
            continue
        os.makedirs(destino, exist_ok=True)
        for caminho in arquivos:
            try:
                shutil.copy2(caminho, os.path.join(destino, os.path.basename(caminho)))
                total += 1
            except OSError:
                continue
    return total


def pack_instalado(pack_dir, destinos):
    """True se qualquer arquivo do pack já existe nas pastas de destino."""
    for tipo, arquivos in arquivos_por_tipo(pack_dir).items():
        destino = destinos.get(tipo)
        if not destino or not os.path.isdir(destino):
            continue
        for caminho in arquivos:
            if os.path.exists(os.path.join(destino, os.path.basename(caminho))):
                return True
    return False