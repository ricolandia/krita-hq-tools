"""Testes dos tiles do kit (fora do Krita)."""

import os
import pathlib
import struct
import tempfile
import unittest
import zlib

from hq_tools.modules.screentone import tiles


def _decodificar(png):
    """Decodifica o PNG mínimo e devolve (largura, altura, bytes RGBA)."""
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    largura = altura = None
    idat = b""
    while offset + 8 <= len(png):
        tamanho = int.from_bytes(png[offset:offset + 4], "big")
        tipo = png[offset + 4:offset + 8]
        payload = png[offset + 8:offset + 8 + tamanho]
        if tipo == b"IHDR":
            largura, altura, depth, cor, _, _, _ = struct.unpack(">IIBBBBB", payload)
            self_ = None
            assert depth == 8 and cor == 6
        elif tipo == b"IDAT":
            idat += payload
        elif tipo == b"IEND":
            break
        offset += 12 + tamanho
    dados = zlib.decompress(idat)
    return largura, altura, dados


class TestTiles(unittest.TestCase):
    def test_todos_os_tiles_sao_png_validos(self):
        for nome, lado, _ in tiles.TILES:
            png = tiles.gerar_tile(nome)
            largura, altura, dados = _decodificar(png)
            self.assertEqual((largura, altura), (lado, lado), nome)
            # zlib guarda 1 byte de filtro por scanline
            self.assertEqual(len(dados), lado * lado * 4 + lado, nome)

    def test_determinismo(self):
        primeiro = tiles.gerar_tile("papel-liso")
        segundo = tiles.gerar_tile("papel-liso")
        self.assertEqual(primeiro, segundo)

    def test_gerar_todos_cria_arquivos(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminhos = tiles.gerar_todos(pasta)
            self.assertEqual(len(caminhos), len(tiles.TILES))
            for caminho in caminhos:
                self.assertTrue(os.path.isfile(caminho))

    def test_tile_desconhecido(self):
        with self.assertRaises(ValueError):
            tiles.gerar_tile("nao-existe")

    def test_tiles_nao_sao_unicos_por_acaso(self):
        """Tiles diferentes produzem bytes diferentes (sem colisão boba)."""
        bytes_por_nome = {nome: tiles.gerar_tile(nome) for nome, _, _ in tiles.TILES}
        self.assertEqual(len(set(bytes_por_nome.values())), len(tiles.TILES))


class TestTilesDoKit(unittest.TestCase):
    """Os PNGs embarcados em resources/patterns têm que refletir o gerador.

    Mexer numa função de tile sem regerar os arquivos deixa o kit servindo a
    versão antiga: o autor instala o padrão e ele sai diferente do que o
    código gera.
    """

    KIT = pathlib.Path(__file__).resolve().parent.parent / "hq_tools" / "resources" / "patterns"

    def test_kit_tem_um_png_por_tile_do_catalogo(self):
        no_kit = sorted(p.name for p in self.KIT.glob("*.png"))
        do_catalogo = sorted(nome + ".png" for nome, _, _ in tiles.TILES)
        self.assertEqual(do_catalogo, no_kit)

    def test_pngs_do_kit_batem_com_o_gerador(self):
        for nome, _, _ in tiles.TILES:
            with self.subTest(tile=nome):
                caminho = self.KIT / (nome + ".png")
                self.assertTrue(caminho.is_file(), "faltou {0}".format(caminho.name))
                self.assertEqual(
                    tiles.gerar_tile(nome),
                    caminho.read_bytes(),
                    "{0}.png está defasado; rode tiles.gerar_todos em "
                    "hq_tools/resources/patterns".format(nome),
                )

    def test_nenhum_png_orfao_no_kit(self):
        do_catalogo = {nome + ".png" for nome, _, _ in tiles.TILES}
        orfaos = sorted(p.name for p in self.KIT.glob("*.png") if p.name not in do_catalogo)
        self.assertEqual([], orfaos, "PNG no kit sem tile correspondente no catálogo")


if __name__ == "__main__":
    unittest.main()