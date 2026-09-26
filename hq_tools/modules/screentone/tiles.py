"""Geração dos padrões e texturas do kit (sem dependências externas).

Tiles PNG RGBA gerados por código, todos próprios do projeto (MIT). O PNG é
montado na mão (IHDR/IDAT/IEND com zlib), então roda em qualquer Python, sem
PIL. Usados como padrões do Krita (fundo, textura de pincel e telas do
Halftone no modo "tom com padrão").
"""

import math
import os
import struct
import zlib

_SEMENTE = 20260926


def _hash2(x, y, s=0):
    """Hash determinístico 16 bits para ruído por pixel."""
    valor = (x * 73856093) ^ (y * 19349663) ^ ((s + _SEMENTE) * 83492791)
    return valor & 0xFFFF


def _semente_prng(seed):
    estado = [seed + _SEMENTE]

    def proximo():
        estado[0] = (estado[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return estado[0]

    return proximo


def _png_rgba(largura, altura, pixels):
    """Monta um PNG RGBA 8 bits a partir de bytes (w*h*4)."""
    dados = bytearray(b"\x89PNG\r\n\x1a\n")

    def chunk(tipo, payload):
        parte = struct.pack(">I", len(payload)) + tipo + payload
        return parte + struct.pack(">I", zlib.crc32(tipo + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", largura, altura, 8, 6, 0, 0, 0)
    dados += chunk(b"IHDR", ihdr)
    linhas = bytearray()
    for y in range(altura):
        linhas.append(0)
        inicio = y * largura * 4
        linhas += pixels[inicio:inicio + largura * 4]
    dados += chunk(b"IDAT", zlib.compress(bytes(linhas)))
    dados += chunk(b"IEND", b"")
    return bytes(dados)


def _montar(largura, altura, cor_fn):
    """Gera os bytes do PNG avaliando cor_fn(x, y) -> (r, g, b, a)."""
    pixels = bytearray(largura * altura * 4)
    indice = 0
    for y in range(altura):
        for x in range(largura):
            r, g, b, a = cor_fn(x, y)
            pixels[indice:indice + 4] = bytes((r, g, b, a))
            indice += 4
    return _png_rgba(largura, altura, pixels)


def _branco(x, y, s=0):
    return (255, 255, 255, 255)


def papel_liso(x, y):
    variacao = (_hash2(x, y, 1) % 13) - 6
    v = max(0, min(255, 246 + variacao))
    return (v, v, v, 255)


def papel_gramatura(x, y):
    v = 250
    prng = _semente_prng(11)
    for _ in range(14):
        cx = prng() % 256
        cy = prng() % 256
        raio = 6 + prng() % 12
        dx = x - cx
        dy = y - cy
        if dx * dx + dy * dy <= raio * raio:
            v += 8
    v += (_hash2(x, y, 2) % 7) - 3
    v = max(0, min(255, v))
    return (v, v, v, 255)


def papel_trama(x, y):
    v = 249
    if ((x + y * 2) % 24) < 1:
        v -= 7
    v += (_hash2(x, y, 3) % 7) - 3
    return (v, v, v, 255)


def aguado(x, y):
    prng = _semente_prng(21)
    for _ in range(8):
        cx = prng() % 256
        cy = prng() % 256
        raio = 24 + prng() % 46
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        if dist <= raio:
            t = max(0.0, 1.0 - dist / raio)
            alpha = int(50 + 60 * t)
            r = int(255 - (255 - 198) * t)
            g = int(255 - (255 - 214) * t)
            b = int(255 - (255 - 232) * t)
            return (r, g, b, min(255, alpha))
    return _branco(x, y)


def ret_estrelas(x, y):
    celula = 16
    cx = (x // celula) * celula + celula // 2
    cy = (y // celula) * celula + celula // 2
    dx = x - cx
    dy = y - cy
    dist = math.hypot(dx, dy)
    if dist < 1.0 or dist > 7.0:
        return _branco(x, y)
    angulo = math.atan2(dy, dx)
    raio_proximo = (round(angulo / (math.pi / 3)) % 6) * (math.pi / 3)
    dif = abs(angulo - raio_proximo)
    if dif > math.pi:
        dif = 2 * math.pi - dif
    if dif * dist < 1.6:
        return (20, 20, 20, 255)
    return _branco(x, y)


def ret_coracoes(x, y):
    celula = 16
    cx = (x // celula) * celula + celula // 2
    cy = (y // celula) * celula + celula // 2
    nx = (x - cx) / 8.0
    ny = (y - cy) / 8.0
    valor = (nx * nx + ny * ny - 1.0) ** 3 - nx * nx * (ny ** 3)
    if valor <= 0.0:
        return (20, 20, 20, 255)
    return _branco(x, y)


def ret_ruido(x, y):
    if _hash2(x, y, 5) > 32767:
        return (20, 20, 20, 255)
    return _branco(x, y)


def trama_manga(x, y):
    celula = 16
    cx = (x // celula) * celula + celula // 2
    cy = (y // celula) * celula + celula // 2
    if (y // celula) % 2:
        cx += 4
    dx = x - cx
    dy = y - cy
    if dx * dx + dy * dy <= 6.25:
        return (20, 20, 20, 255)
    return _branco(x, y)


def hachura_45(x, y):
    if ((x + y) % 16) < 3:
        return (20, 20, 20, 255)
    return _branco(x, y)


def hachura_135(x, y):
    if ((x - y) % 16 + 16) % 16 < 3:
        return (20, 20, 20, 255)
    return _branco(x, y)


def granulado_nanquim(x, y):
    if _hash2(x, y, 7) % 11 == 0:
        return (25, 25, 25, 255)
    return _branco(x, y)


TILES = (
    ("papel-liso", 256, papel_liso),
    ("papel-gramatura", 256, papel_gramatura),
    ("papel-trama", 256, papel_trama),
    ("aguado", 256, aguado),
    ("ret-estrelas", 128, ret_estrelas),
    ("ret-coracoes", 128, ret_coracoes),
    ("ret-ruido", 128, ret_ruido),
    ("trama-manga", 128, trama_manga),
    ("hachura-45", 128, hachura_45),
    ("hachura-135", 128, hachura_135),
    ("granulado-nanquim", 128, granulado_nanquim),
)


def gerar_tile(nome, lado=128):
    """Gera os bytes PNG de um tile pelo nome."""
    for tile_nome, tamanho, cor_fn in TILES:
        if tile_nome == nome:
            return _montar(tamanho, tamanho, cor_fn)
    raise ValueError("tile desconhecido: {0}".format(nome))


def gerar_todos(destino):
    """Gera todos os tiles do kit na pasta de destino; devolve os caminhos."""
    os.makedirs(destino, exist_ok=True)
    gerados = []
    for nome, _, _ in TILES:
        caminho = os.path.join(destino, "{0}.png".format(nome))
        with open(caminho, "wb") as handle:
            handle.write(gerar_tile(nome))
        gerados.append(caminho)
    return gerados