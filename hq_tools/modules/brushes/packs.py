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
import zlib

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


def _texto_do_chunk(tipo, dados):
    """Texto de um chunk de texto do PNG (tEXt, zTXt ou iTXt)."""
    try:
        if tipo == "tEXt":
            return dados.decode("utf-8", "replace")
        if tipo == "zTXt":
            corte = dados.find(b"\0")
            if corte < 0 or corte + 2 > len(dados):
                return None
            return zlib.decompress(dados[corte + 2:]).decode("utf-8", "replace")
        if tipo == "iTXt":
            partes = dados.split(b"\0", 5)
            if len(partes) < 6:
                return None
            if partes[1] == b"\x01":
                return zlib.decompress(partes[5]).decode("utf-8", "replace")
            return partes[5].decode("utf-8", "replace")
    except (ValueError, UnicodeDecodeError, zlib.error):
        return None
    return None


def _preset_chunk_xml(caminho):
    """Extrai o XML do chunk 'preset' de um .kpp (PNG com anotação).

    O Krita grava o XML em ``tEXt`` na maioria dos presets, mas usa ``zTXt``
    (comprimido) em alguns (3 do pack do Deevad) e ``iTXt`` é aceito por
    outros geradores. O auditor de packs já lia os três; aqui faltava, e o
    preset ficava sem nome interno (o fallback pelo nome do arquivo salvava
    só quando os dois coincidem).
    """
    try:
        with open(caminho, "rb") as handle:
            dados = handle.read()
    except OSError:
        return None
    if dados[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    offset = 8
    while offset + 8 <= len(dados):
        tamanho = int.from_bytes(dados[offset:offset + 4], "big")
        tipo = dados[offset + 4:offset + 8].decode("latin1", "replace")
        if tipo == "IEND":
            break
        if tipo in ("tEXt", "zTXt", "iTXt"):
            conteudo = dados[offset + 8:offset + 8 + tamanho]
            if conteudo.startswith(b"preset\0"):
                texto = _texto_do_chunk(tipo, conteudo)
                if texto:
                    return texto
        offset += 12 + tamanho
    return None


def _preset_internal_name(caminho):
    """Nome interno do preset (atributo da raiz <Preset> do XML), ou None."""
    xml = _preset_chunk_xml(caminho)
    if not xml:
        return None
    match = re.search(r'<Preset\b[^>]*\bname="([^"]*)"', xml, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


_ALIASES_CACHE = {}


def _pasta_mtime(pasta):
    melhor = 0.0
    try:
        for nome in os.listdir(pasta):
            caminho = os.path.join(pasta, nome)
            try:
                melhor = max(melhor, os.path.getmtime(caminho))
            except OSError:
                pass
    except OSError:
        pass
    return melhor


def preset_aliases(pack_dir):
    """Aliases por preset: ``(nome do arquivo, nome interno)``.

    O Krita lista os presets pelo nome interno (atributo da raiz ``<Preset>``,
    que pode diferir do nome do arquivo); este par permite casar os dois no
    ``resources("preset")``. Cacheado por mtime da pasta de presets.
    """
    pasta = os.path.join(pack_dir, "paintoppresets")
    if not os.path.isdir(pasta):
        return []
    chave = (pack_dir, _pasta_mtime(pasta))
    if chave in _ALIASES_CACHE:
        return _ALIASES_CACHE[chave]
    aliases = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.lower().endswith((".kpp", ".myb")):
            continue
        nome_arquivo = os.path.splitext(nome)[0]
        interno = _preset_internal_name(os.path.join(pasta, nome))
        aliases.append((nome_arquivo, interno or nome_arquivo))
    _ALIASES_CACHE[chave] = aliases
    return aliases


def _backup_de_preservado(destino_arquivo):
    """Guarda uma cópia do preset do usuário que seria sobrescrito.

    Os packs trazem presets com o mesmo nome dos que o usuário pode ter
    editado. A cópia vai para ``<nome>.hqtools-backup`` para não haver duas
    cópias do mesmo preset na pasta de recursos (o Krita leria as duas).
    Devolve o caminho da cópia, ou None se não deu para fazer.
    """
    backup = destino_arquivo + ".hqtools-backup"
    try:
        if os.path.isfile(backup):
            os.unlink(backup)
        shutil.copy2(destino_arquivo, backup)
    except OSError:
        return None
    return backup


def instalar_pack(pack_dir, destinos, relatorio=None):
    """Copia os arquivos do pack para as pastas de recursos do usuário.

    ``destinos`` é ``{tipo: pasta_destino}``; devolve o total copiado.
    ``relatorio``, se fornecido, recebe uma linha por arquivo preservado ou que
    falhou, para o docker poder avisar o autor em vez de engolir em silêncio.
    """
    total = 0
    for tipo, arquivos in arquivos_por_tipo(pack_dir).items():
        destino = destinos.get(tipo)
        if not destino:
            continue
        os.makedirs(destino, exist_ok=True)
        for caminho in arquivos:
            alvo = os.path.join(destino, os.path.basename(caminho))
            try:
                if os.path.isfile(alvo) and not _mesmos_bytes(caminho, alvo):
                    backup = _backup_de_preservado(alvo)
                    if backup is None:
                        # Sem cópia de segurança possível, o preset editado
                        # pelo autor tem prioridade.
                        if relatorio is not None:
                            relatorio.append(
                                "mantido o seu preset (não foi possível fazer "
                                "cópia de segurança): {0}".format(
                                    os.path.basename(alvo)
                                )
                            )
                        continue
                    if relatorio is not None:
                        relatorio.append(
                            "seu preset foi substituído; cópia em {0}".format(
                                os.path.basename(backup)
                            )
                        )
                elif os.path.isfile(alvo):
                    # Idêntico: instalar de novo só gastaria I/O.
                    continue
                shutil.copy2(caminho, alvo)
                total += 1
            except OSError as error:
                if relatorio is not None:
                    relatorio.append(
                        "falha ao instalar {0}: {1}".format(
                            os.path.basename(alvo), error
                        )
                    )
                continue
    return total


def _mesmos_bytes(um, outro):
    try:
        if os.path.getsize(um) != os.path.getsize(outro):
            return False
        with open(um, "rb") as a, open(outro, "rb") as b:
            return a.read() == b.read()
    except OSError:
        return False


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