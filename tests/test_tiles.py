"""Testes dos tiles do kit (fora do Krita)."""

import os
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


if __name__ == "__main__":
    unittest.main()