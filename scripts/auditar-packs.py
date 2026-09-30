#!/usr/bin/env python3
"""Auditoria dos packs de pincéis do kit.

Um preset (.kpp) é um PNG com o XML do preset dentro de um chunk de texto. O
XML cita arquivos do próprio pack pelo nome (``filename="..."`` no
``brush_definition`` e ``requiredBrushFile``). Se o arquivo citado não estiver
no pack, o preset instala, mas o pincel não aparece: o Krita cai no pincel
padrão e o autor perde tempo achando que o preset veio quebrado.

Este script acha essas referências órfãs, sem depender do Krita.

Uso:
    python3 scripts/auditar-packs.py            # relatório
    python3 scripts/auditar-packs.py --estrito  # sai com 1 se houver órfã
"""

from __future__ import annotations

import argparse
import pathlib
import re
import struct
import sys
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
BRUSHES_DIR = REPO / "hq_tools" / "resources" / "brushes"

# Extensões que o Krita resolve a partir da pasta brushes/ do usuário.
EXTENSOES = (".gbr", ".gih", ".png", ".svg", ".abr", ".cur", ".wa")


def texto_do_chunk(dados: bytes, tipo: bytes) -> str:
    """Devolve o texto de um chunk tEXt/zTXt/iTXt."""
    if tipo == b"tEXt":
        _, _, valor = dados.partition(b"\x00")
        return valor.decode("utf-8", "replace")
    if tipo == b"zTXt":
        _, _, resto = dados.partition(b"\x00")
        if not resto:
            return ""
        # Metadados comprimidos terminam em \x00 antes do zlib.
        _, sep, comprimido = resto.partition(b"\x00")
        if not sep:
            return ""
        try:
            return zlib.decompress(comprimido).decode("utf-8", "replace")
        except zlib.error:
            return ""
    if tipo == b"iTXt":
        partes = dados.split(b"\x00", 4)
        if len(partes) < 5:
            return ""
        bruto = partes[4]
        if bruto[:1] == b"\x01":  # comprimido
            try:
                bruto = zlib.decompress(bruto[1:])
            except zlib.error:
                return ""
        return bruto.decode("utf-8", "replace")
    return ""


def xml_do_preset(caminho: pathlib.Path) -> str:
    """Extrai o XML do preset de um .kpp (que é um PNG)."""
    dados = caminho.read_bytes()
    if dados[:8] != b"\x89PNG\r\n\x1a\n":
        return ""
    pos = 8
    while pos + 8 <= len(dados):
        tamanho = struct.unpack(">I", dados[pos:pos + 4])[0]
        tipo = dados[pos + 4:pos + 8]
        if tipo in (b"tEXt", b"zTXt", b"iTXt"):
            texto = texto_do_chunk(dados[pos + 8:pos + 8 + tamanho], tipo)
            if texto.lstrip().startswith("<Preset"):
                return texto
        pos += 12 + tamanho
        if tipo == b"IEND":
            break
    return ""


def valor_do_param(xml: str, nome: str) -> str:
    """Lê um <param name="..."> do preset, com ou sem CDATA."""
    achado = re.search(
        r'name="%s"[^>]*>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</param>' % re.escape(nome),
        xml,
        re.S,
    )
    return achado.group(1).strip() if achado else ""


def arquivos_do_pack(pack_dir: pathlib.Path) -> set:
    """Nomes (em minúsculas) de todos os arquivos de recurso do pack."""
    nomes = set()
    for pasta in ("paintoppresets", "brushes", "patterns", "palettes"):
        origem = pack_dir / pasta
        if origem.is_dir():
            nomes.update(p.name.lower() for p in origem.iterdir() if p.is_file())
    return nomes


def presets_do_pack(pack_dir: pathlib.Path) -> list:
    pasta = pack_dir / "paintoppresets"
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() == ".kpp")


def auditar(pack_dir: pathlib.Path):
    """Devolve (órfãs, embutidos, especiais, sem_xml)."""
    disponiveis = arquivos_do_pack(pack_dir)
    orfas = {}
    embutidos = []
    especiais = []
    sem_xml = []
    for preset in presets_do_pack(pack_dir):
        xml = xml_do_preset(preset)
        if not xml:
            sem_xml.append(preset.name)
            continue
        citados = set()
        defi = valor_do_param(xml, "brush_definition")
        if defi:
            citados.update(re.findall(r'filename="([^"]+)"', defi))
        cited_req = valor_do_param(xml, "requiredBrushFile")
        if cited_req:
            citados.add(cited_req)
        paintop = ""
        achado = re.search(r'<Preset[^>]*paintopid="([^"]*)"', xml)
        if achado:
            paintop = achado.group(1)
        if not citados:
            # Duas coisas legítimas caem aqui: preset com o pincel inteiro
            # embutido no próprio arquivo (não depende de recurso nenhum) e
            # paintop de ferramenta (deform, experiment, duplicate), que
            # trabalha sobre o pincel já selecionado.
            if paintop in ("", "paintbrush", "colorsmudge"):
                embutidos.append(preset.name)
            else:
                especiais.append("{0} ({1})".format(preset.name, paintop))
        for nome in citados:
            if not nome.lower().endswith(EXTENSOES):
                continue
            if nome.lower() not in disponiveis:
                orfas.setdefault(nome, []).append(preset.name)
    return orfas, embutidos, especiais, sem_xml


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--estrito", action="store_true",
                    help="sai com 1 se houver referência órfã")
    ap.add_argument("--detalhe", action="store_true",
                    help="lista os presets com o pincel embutido no próprio arquivo")
    args = ap.parse_args(argv)

    if not BRUSHES_DIR.is_dir():
        print("sem packs em {0}".format(BRUSHES_DIR))
        return 0

    total_presets = 0
    total_orfas = 0
    for pack in sorted(p for p in BRUSHES_DIR.iterdir() if p.is_dir()):
        orfas, embutidos, especiais, sem_xml = auditar(pack)
        presets = presets_do_pack(pack)
        total_presets += len(presets)
        total_orfas += len(orfas)

        print("== {0} ({1} presets) ==".format(pack.name, len(presets)))
        if sem_xml:
            print("  ALERTA sem XML legível: {0}".format(", ".join(sem_xml)))
        if args.detalhe and embutidos:
            print("  pincel embutido no próprio preset ({0}): {1}".format(
                len(embutidos), ", ".join(embutidos)))
        if especiais:
            print("  paintop de ferramenta, sem pincel próprio: {0}".format(
                ", ".join(especiais)))
        if orfas:
            print("  referência órfã (o preset instala, o pincel não vem):")
            for nome, quem in sorted(orfas.items()):
                print("    {0} <- {1}".format(nome, ", ".join(sorted(set(quem)))))
        else:
            print("  todas as referências resolvem dentro do pack")

    print("\ntotal: {0} presets, {1} arquivo(s) citado(s) sem destino".format(
        total_presets, total_orfas))
    if total_orfas and args.estrito:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
