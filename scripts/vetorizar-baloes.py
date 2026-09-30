#!/usr/bin/env python3
"""Vetoriza um balão de uma referência raster (PNG) para SVG.

Fluxo: recorte -> limiar (Otsu) -> interior do balão (preenchimento) ->
contorno (Moore) -> simplificação (RDP) -> curvas (Catmull-Rom -> bezier) ->
SVG com dois grupos: ``balao`` e ``cauda`` (cada um com preenchimento branco
e traço preto aberto). O traço não fecha no pescoço, então a cauda pode ser
movida sem deixar linha interna. Sem texto: o interior é ignorado.

Uso:
    python3 vetorizar-baloes.py IMAGEM X Y L A SAIDA.svg [--margem 22]
        [--tamanho-pt 150] [--epsilon 0.8] [--debug] [--corte I,J]

Requer PIL e numpy.
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def otsu(arr):
    hist, _ = np.histogram(arr, bins=256, range=(0, 255))
    total = arr.size
    soma = np.dot(np.arange(256), hist)
    wB = np.cumsum(hist).astype(float)
    wF = total - wB
    somaB = np.cumsum(np.arange(256) * hist).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        mB = somaB / wB
        mF = (soma - somaB) / wF
        var = wB * wF * (mB - mF) ** 2
    var[np.isnan(var)] = 0
    return int(np.argmax(var))


def cross2(a, b):
    """Produto vetorial 2D (z)."""
    return a[0] * b[1] - a[1] * b[0]


def componentes_claros(escuro):
    """Rotula todos os componentes claros do recorte (preenchimento em numpy)."""
    claro = ~escuro
    h, w = claro.shape
    visto = np.zeros_like(claro)
    comps = []
    for y0 in range(h):
        for x0 in range(w):
            if not claro[y0, x0] or visto[y0, x0]:
                continue
            mask = np.zeros_like(claro)
            mask[y0, x0] = True
            visto[y0, x0] = True
            pilha = [(x0, y0)]
            while pilha:
                x, y = pilha.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and claro[ny, nx] and not mask[ny, nx]:
                        mask[ny, nx] = True
                        visto[ny, nx] = True
                        pilha.append((nx, ny))
            comps.append(mask)
    return comps


def interior_mask(escuro, semente, juntar_adjacentes=True):
    """Componente claro da semente; junta componentes pequenos encostados.

    A cauda de um balão às vezes fica com o interior separado (pescoço
    estreito): nesse caso o componente pequeno vizinho é somado ao principal.
    """
    comps = componentes_claros(escuro)
    principal = None
    for c in comps:
        if c[semente[1], semente[0]]:
            principal = c
            break
    if principal is None:
        return np.zeros_like(escuro, dtype=bool)
    if not juntar_adjacentes:
        return principal
    ys, xs = np.nonzero(principal)
    x0, y0 = xs.min() - 16, ys.min() - 16
    x1, y1 = xs.max() + 16, ys.max() + 16
    area = int(principal.sum())
    for c in comps:
        if c is principal:
            continue
        ys2, xs2 = np.nonzero(c)
        if len(xs2) == 0 or len(xs2) > 0.5 * area:
            continue
        if xs2.min() >= x0 and ys2.min() >= y0 and xs2.max() <= x1 and ys2.max() <= y1:
            principal = principal | c
    return principal


def dilatar(mask, vezes=1):
    for _ in range(vezes):
        anterior = mask
        mask = anterior.copy()
        mask[1:, :] |= anterior[:-1, :]
        mask[:-1, :] |= anterior[1:, :]
        mask[:, 1:] |= anterior[:, :-1]
        mask[:, :-1] |= anterior[:, 1:]
    return mask


def erodir(mask):
    erode = mask.copy()
    erode[1:, :] &= mask[:-1, :]
    erode[:-1, :] &= mask[1:, :]
    erode[:, 1:] &= mask[:, :-1]
    erode[:, :-1] &= mask[:, 1:]
    return erode


def espessura_estimada(escuro, interno):
    """Espessura do traço: tinta num anel de 10 px / perímetro do interior.

    Funciona em referências de fundo claro. Em fundo escuro (a tinta se
    confunde com o fundo) devolve o padrão de 5 px; o ``--traco-px`` permite
    fixar o valor na mão.
    """
    anel = dilatar(interno, 10) & ~interno
    tinta = escuro & anel
    perimetro = np.count_nonzero(interno & ~erodir(interno))
    estimativa = np.count_nonzero(tinta) / max(1, perimetro)
    if not (2.0 <= estimativa <= 12.0):
        return 5.0
    return estimativa


def contorno_moore(mask):
    """Contorno externo do mask (Moore-neighbor), em ordem."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("máscara vazia")
    inicio = (int(xs[np.argmin(ys * 100000 + xs)]), int(ys[np.argmin(ys * 100000 + xs)]))
    direcoes = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    h, w = mask.shape
    atual = inicio
    anterior = 0
    pontos = []
    limite = 4 * int(mask.sum()) + 100
    for _ in range(limite):
        pontos.append(atual)
        achou = False
        for k in range(8):
            d = (anterior + k) % 8
            dx, dy = direcoes[d]
            nx, ny = atual[0] + dx, atual[1] + dy
            if 0 <= nx < w and 0 <= ny < h and mask[ny, nx]:
                atual = (nx, ny)
                anterior = (d + 5) % 8
                achou = True
                break
        if not achou:
            break
        if atual == inicio and len(pontos) > 4:
            break
    return pontos


def rdp(pontos, epsilon):
    if len(pontos) < 3:
        return pontos
    a, b = np.array(pontos[0], float), np.array(pontos[-1], float)
    ab = b - a
    norma = np.linalg.norm(ab)
    if norma == 0:
        dist = [np.linalg.norm(np.array(p, float) - a) for p in pontos]
    else:
        dist = [abs(cross2(ab, np.array(p, float) - a)) / norma for p in pontos]
    indice = int(np.argmax(dist))
    if dist[indice] > epsilon:
        esquerda = rdp(pontos[:indice + 1], epsilon)
        direita = rdp(pontos[indice:], epsilon)
        return esquerda[:-1] + direita
    return [pontos[0], pontos[-1]]


def simplificar_fechado(pontos, epsilon):
    if len(pontos) < 4:
        return pontos
    arr = np.array(pontos, float)
    i1 = int(np.argmax(np.linalg.norm(arr - arr[0], axis=1)))
    i2 = int(np.argmax(np.linalg.norm(arr - arr[i1], axis=1)))
    a, b = sorted((i1, i2))
    p1 = rdp(pontos[a:b + 1], epsilon)
    p2 = rdp(pontos[b:] + pontos[:a + 1], epsilon)
    return p1[:-1] + p2[:-1]


def hull(pontos):
    pts = sorted(set(pontos))
    if len(pts) <= 2:
        return pts

    def meia(seq):
        saida = []
        for p in seq:
            while len(saida) >= 2:
                (x1, y1), (x2, y2) = saida[-2], saida[-1]
                if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) <= 0:
                    saida.pop()
                else:
                    break
            saida.append(p)
        return saida

    return meia(pts)[:-1] + meia(pts[::-1])[:-1]


def corte_radial(pontos):
    """Acha o pescoço pela ponta: o ponto mais longe do centro é a ponta da
    cauda; voltando pelo contorno, o pescoço é o mínimo local de distância."""
    arr = np.array(pontos, float)
    n = len(arr)
    centro = arr.mean(axis=0)
    d = np.linalg.norm(arr - centro, axis=1)
    ponta = int(np.argmax(d))

    def lado(passo):
        i = ponta
        passos = 0
        while passos < n // 2:
            j = (i + passo) % n
            if d[j] > d[i]:
                return i
            i = j
            passos += 1
        return i

    a, b = lado(1), lado(-1)
    if a > b:
        a, b = b, a
    return a, b


def defeitos(pontos, casco):
    casco_arr = np.array(casco, float)
    distancias = []
    for p in pontos:
        p = np.array(p, float)
        melhor = min(
            abs(cross2(casco_arr[(i + 1) % len(casco_arr)] - casco_arr[i], p - casco_arr[i]))
            / max(1e-9, np.linalg.norm(casco_arr[(i + 1) % len(casco_arr)] - casco_arr[i]))
            for i in range(len(casco_arr))
        )
        distancias.append(melhor)
    return np.array(distancias)


def suavizar(pontos, janela):
    """Média móvel circular: tira o serrilhado, mantém as ondas maiores."""
    if janela <= 1 or len(pontos) < janela:
        return pontos
    raio = janela // 2
    n = len(pontos)
    arr = np.array(pontos, float)
    saida = []
    for i in range(n):
        indices = [(i + k) % n for k in range(-raio, raio + 1)]
        media = arr[indices].mean(axis=0)
        saida.append((float(media[0]), float(media[1])))
    return saida


def despur(pontos, minimo=3.0, desvio=1.2):
    """Remove espículas: ponto com vizinhos curtos e fora da linha deles."""
    saida = list(pontos)
    for _ in range(2):
        n = len(saida)
        if n < 5:
            break
        nova = []
        for i in range(n):
            p = np.array(saida[i], float)
            ant = np.array(saida[(i - 1) % n], float)
            prox = np.array(saida[(i + 1) % n], float)
            if np.linalg.norm(p - ant) < minimo and np.linalg.norm(p - prox) < minimo:
                linha = prox - ant
                norma = np.linalg.norm(linha)
                if norma > 0 and abs(cross2(linha, p - ant)) / norma > desvio:
                    continue
            nova.append(saida[i])
        if len(nova) == n:
            break
        saida = nova
    return saida


def _controles(p0, p1, p2, p3):
    limite = np.linalg.norm(p2 - p1) / 3.0
    c1 = p1 + (p2 - p0) / 6.0
    c2 = p2 - (p3 - p1) / 6.0
    d1 = np.linalg.norm(c1 - p1)
    if d1 > limite > 0:
        c1 = p1 + (c1 - p1) * (limite / d1)
    d2 = np.linalg.norm(c2 - p2)
    if d2 > limite > 0:
        c2 = p2 + (c2 - p2) * (limite / d2)
    return c1, c2


def path_fechado(pontos, escala, linhas=False, fechar=True):
    """Path pelos pontos; com ``fechar=False`` sai aberto (sem traço na base).

    A cauda usa ``fechar=False``: o preenchimento continua fechando sozinho,
    mas a linha de base não é traçada, para o autor unir a cauda ao balão no
    Krita. Com ``linhas=True`` sai em polilinha (segmentos retos).
    """
    n = len(pontos)
    if n < 3:
        return ""
    partes = ["M {:.2f} {:.2f}".format(pontos[0][0] * escala, pontos[0][1] * escala)]
    for i in range(n if fechar else n - 1):
        p2 = pontos[(i + 1) % n]
        if linhas:
            partes.append("L {:.2f} {:.2f}".format(p2[0] * escala, p2[1] * escala))
            continue
        p0 = np.array(pontos[(i - 1) % n], float)
        p1 = np.array(pontos[i], float)
        p2v = np.array(p2, float)
        p3 = np.array(pontos[(i + 2) % n], float)
        if i == n - 1:
            partes.append("L {:.2f} {:.2f}".format(p2v[0] * escala, p2v[1] * escala))
            continue
        c1, c2 = _controles(p0, p1, p2v, p3)
        partes.append("C {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}".format(
            c1[0] * escala, c1[1] * escala, c2[0] * escala, c2[1] * escala, p2v[0] * escala, p2v[1] * escala))
    if fechar:
        partes.append("Z")
    return " ".join(partes)


def path_aberto(pontos, escala):
    """Path aberto (só traço): curvas entre os pontos, pontas com controle simples."""
    n = len(pontos)
    if n < 2:
        return ""
    partes = ["M {:.2f} {:.2f}".format(pontos[0][0] * escala, pontos[0][1] * escala)]
    for i in range(n - 1):
        p0 = np.array(pontos[max(0, i - 1)], float)
        p1 = np.array(pontos[i], float)
        p2 = np.array(pontos[i + 1], float)
        p3 = np.array(pontos[min(n - 1, i + 2)], float)
        c1, c2 = _controles(p0, p1, p2, p3)
        partes.append("C {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}".format(
            c1[0] * escala, c1[1] * escala, c2[0] * escala, c2[1] * escala, p2[0] * escala, p2[1] * escala))
    return " ".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imagem")
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("largura", type=int)
    ap.add_argument("altura", type=int)
    ap.add_argument("saida")
    ap.add_argument("--margem", type=int, default=22)
    ap.add_argument("--tamanho-pt", type=float, default=150.0)
    ap.add_argument("--epsilon", type=float, default=0.8)
    ap.add_argument("--suavizar", type=int, default=0,
                    help="janela da média móvel no contorno (0 = sem suavizar; 5-9 tira o tremido)")
    ap.add_argument("--linhas", action="store_true",
                    help="saída em polilinha (preserva o tremido exato)")
    ap.add_argument("--traco-px", type=float, default=0.0,
                    help="espessura do traço em pixels da referência (0 = estimar)")
    ap.add_argument("--base-interna", type=float, default=12.0,
                    help="quanto a base da cauda entra no corpo (px)")
    ap.add_argument("--alargar-base", type=float, default=0.0,
                    help="quanto alargar a base da cauda (px)")
    ap.add_argument("--corte", default="")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.imagem):
        sys.stderr.write(
            "não encontrei a prancha {0} (o caminho é relativo ao script?).\n".format(
                args.imagem
            )
        )
        return 1
    img = Image.open(args.imagem).convert("L")
    caixa = (
        max(0, args.x - args.margem),
        max(0, args.y - args.margem),
        min(img.width, args.x + args.largura + args.margem),
        min(img.height, args.y + args.altura + args.margem),
    )
    recorte = np.array(img.crop(caixa))
    if recorte.size == 0:
        sys.stderr.write(
            "o recorte {0},{1},{2},{3} ficou fora da prancha ({4}x{5}).\n".format(
                args.x, args.y, args.largura, args.altura, img.width, img.height
            )
        )
        return 1
    limiar = otsu(recorte)
    escuro = recorte < limiar

    sx = args.x + args.largura // 2 - caixa[0]
    sy = args.y + args.altura // 2 - caixa[1]
    if escuro[min(sy, recorte.shape[0] - 1), min(sx, recorte.shape[1] - 1)]:
        for raio in range(1, 40):
            achou = False
            for dy in range(-raio, raio + 1):
                for dx in range(-raio, raio + 1):
                    yy, xx = sy + dy, sx + dx
                    if 0 <= yy < recorte.shape[0] and 0 <= xx < recorte.shape[1] and not escuro[yy, xx]:
                        sx, sy, achou = xx, yy, True
                        break
                if achou:
                    break
            if achou:
                break
    interno = interior_mask(escuro, (sx, sy))
    espessura = args.traco_px if args.traco_px > 0 else espessura_estimada(escuro, interno)

    contorno = contorno_moore(interno)
    simplificado = simplificar_fechado(contorno, args.epsilon)
    bruto = despur(simplificado)
    if args.suavizar > 1:
        simplificado = suavizar(bruto, args.suavizar)
    else:
        simplificado = bruto
    if len(simplificado) < 8:
        simplificado = contorno[:: max(1, len(contorno) // 120)]

    casco = hull(simplificado)
    dist = defeitos(simplificado, casco)
    n = len(simplificado)
    if args.corte:
        valores = [float(v) for v in args.corte.split(",")]
        if len(valores) == 2:
            i, j = int(valores[0]), int(valores[1])
        elif len(valores) == 4:
            # coordenadas do pescoço: acha os vértices mais próximos
            def mais_proximo(x, y):
                return int(np.argmin([np.hypot(p[0] - x, p[1] - y) for p in simplificado]))
            i = mais_proximo(valores[0], valores[1])
            j = mais_proximo(valores[2], valores[3])
        else:
            raise SystemExit("--corte espera I,J ou X1,Y1,X2,Y2")
    else:
        a, b = corte_radial(simplificado)
        arco = b - a
        pta = np.array(simplificado[a], float)
        ptb = np.array(simplificado[b], float)
        arr = np.array(simplificado, float)
        diag = float(np.linalg.norm(arr.max(axis=0) - arr.min(axis=0)))
        if 2 < arco <= 0.45 * n and np.linalg.norm(pta - ptb) <= 0.5 * diag:
            i, j = a, b
        else:
            # fallback: maiores defeitos de convexidade
            ordem = np.argsort(dist)[::-1]
            candidatos = []
            for idx in ordem:
                if all(min(abs(idx - c), n - abs(idx - c)) > 6 for c in candidatos):
                    candidatos.append(int(idx))
                if len(candidatos) == 2:
                    break
            i, j = sorted(candidatos)

    def fatia(seq, a, b):
        if a <= b:
            return seq[a:b + 1]
        return seq[a:] + seq[:b + 1]

    # A cauda sai do contorno sem suavizar: a média móvel arredonda as pontas e
    # o pescoço, que é justamente o que dá o formato do balão. Só dá para
    # usar o mesmo índice nos dois quando o despur não removeu ponto; quando
    # removeu, os índices não batem e a cauda sai suavizada (o caso raro, e
    # sinal de que vale passar --corte na mão).
    if len(bruto) == len(simplificado):
        cauda = fatia(bruto, i, j)
    else:
        cauda = fatia(simplificado, i, j)
    corpo = fatia(simplificado, j, i)

    # base da cauda empurrada para dentro do corpo (fica coberta pelo corpo,
    # como na biblioteca oficial de balões do Krita); corpo = silhueta inteira
    if args.base_interna > 0 and len(cauda) >= 3 and len(corpo) >= 3:
        centro = np.mean(np.array(corpo, float), axis=0)
        n1 = np.array(cauda[0], float)
        n2 = np.array(cauda[-1], float)
        meio = (n1 + n2) / 2.0
        para_dentro = centro - meio
        norma = np.linalg.norm(para_dentro)
        if norma > 0:
            para_dentro = para_dentro / norma
        n1p = n1 + para_dentro * args.base_interna
        n2p = n2 + para_dentro * args.base_interna
        if args.alargar_base > 0:
            ao_longo = n2 - n1
            norma2 = np.linalg.norm(ao_longo)
            if norma2 > 0:
                ao_longo = ao_longo / norma2
                n1p = n1p - ao_longo * args.alargar_base
                n2p = n2p + ao_longo * args.alargar_base
        cauda = cauda + [(float(n2p[0]), float(n2p[1])), (float(n1p[0]), float(n1p[1]))]

    todos = list(corpo) + list(cauda)
    xs = [p[0] for p in todos]
    ys = [p[1] for p in todos]
    margem_px = espessura / 2.0 + 2.0
    largura = max(xs) - min(xs) + 2 * margem_px
    altura = max(ys) - min(ys) + 2 * margem_px
    escala = args.tamanho_pt / max(1, max(largura, altura))
    offset_x = min(xs) - margem_px
    offset_y = min(ys) - margem_px

    def deslocar(pts):
        return [(p[0] - offset_x, p[1] - offset_y) for p in pts]

    corpo = deslocar(corpo)
    cauda = deslocar(cauda)
    largura_pt = largura * escala
    altura_pt = altura * escala
    traco = max(1.0, espessura * escala)

    if args.debug:
        print("recorte:", caixa, "limiar:", limiar, "espessura_px: %.2f" % espessura)
        print("contorno:", len(contorno), "simplificado:", len(simplificado))
        print("corte em:", i, simplificado[i], "e", j, simplificado[j])
        print("corpo:", len(corpo), "pontos; cauda:", len(cauda), "pontos")
        print("tamanho pt: %.1f x %.1f | traco pt: %.2f" % (largura_pt, altura_pt, traco))

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0:.2f}pt" height="{1:.2f}pt" viewBox="0 0 {0:.2f} {1:.2f}">'.format(largura_pt, altura_pt),
        '  <g id="cauda">',
        '    <path d="{0}" fill="#ffffff" stroke="#000000" stroke-width="{1:.2f}" stroke-linejoin="round" stroke-linecap="round"/>'.format(
            path_fechado(cauda, escala, args.linhas, fechar=False), traco),
        '  </g>',
        '  <g id="balao">',
        '    <path d="{0}" fill="#ffffff" stroke="#000000" stroke-width="{1:.2f}" stroke-linejoin="round"/>'.format(
            path_fechado(corpo, escala, args.linhas), traco),
        '  </g>',
        '</svg>',
    ]
    with open(args.saida, "w", encoding="utf-8") as handle:
        handle.write("\n".join(svg) + "\n")
    print("SVG salvo:", args.saida)


if __name__ == "__main__":
    sys.exit(main())
