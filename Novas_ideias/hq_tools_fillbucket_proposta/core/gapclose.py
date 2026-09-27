"""
core/gapclose.py

Fechamento de pequenas falhas na linha de arte e preenchimento por região
fechada ("enclose and fill"). Núcleo puro: só numpy, sem `krita`, testável
com `python3 -m unittest` fora do Krita, seguindo a convenção do projeto
(core sem import de krita; a integração fica em modules/fillbucket/docker.py).

Uso típico (dentro do módulo de docker, com dados já extraídos do Krita):

    ink = luminance_mask(rgba, threshold=200)
    parede = close_gaps(ink, radius=2)       # tinta dilatada, só p/ conter
    labels, n = label_regions(parede)         # regiões separadas pela parede
    area = region_mask(labels, seed_x, seed_y) & ~ink   # exclui a tinta real
    novo_rgba = fill_region(rgba, area, cor_rgba=(255, 0, 0, 255))

Limitação conhecida: o raio de `close_gaps` une qualquer falha de até
~2*radius pixels de largura para fins de CONTENÇÃO do flood fill —
inclusive falhas que o desenhista deixou de propósito (ex.: uma
"respiração" entre duas formas próximas). Por isso o raio deve ser
pequeno (1-3 px em 300 dpi) e ajustável pelo usuário por documento/DPI,
não fixo. Além disso, os pixels da própria falha ficam sem pintar (uma
costura fina do tamanho da falha) — ver o docstring de `close_gaps`.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "luminance_mask",
    "dilate",
    "erode",
    "close_gaps",
    "label_regions",
    "region_mask",
    "fill_region",
]


def luminance_mask(rgba: np.ndarray, threshold: int = 200) -> np.ndarray:
    """Devolve máscara booleana (H, W) de pixels "de tinta" (escuros).

    `rgba` é um array (H, W, 4) uint8, na ordem R, G, B, A (converta antes
    se o Krita devolver BGRA — ver nota em docker.py). Pixels totalmente
    transparentes (A == 0) nunca contam como tinta, mesmo se escuros.
    """
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("esperado array (H, W, 4)")
    luminancia = (
        0.299 * rgba[:, :, 0].astype(np.float32)
        + 0.587 * rgba[:, :, 1].astype(np.float32)
        + 0.114 * rgba[:, :, 2].astype(np.float32)
    )
    opaco = rgba[:, :, 3] > 0
    return opaco & (luminancia < threshold)


def _shift(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Desloca `mask` por (dy, dx), preenchendo a borda com False."""
    out = np.zeros_like(mask)
    h, w = mask.shape
    ys, ye = max(0, dy), h + min(0, dy)
    xs, xe = max(0, dx), w + min(0, dx)
    ys2, ye2 = max(0, -dy), h + min(0, -dy)
    xs2, xe2 = max(0, -dx), w + min(0, -dx)
    out[ys:ye, xs:xe] = mask[ys2:ye2, xs2:xe2]
    return out


def _passo_cruz(mask: np.ndarray) -> np.ndarray:
    """Um passo de dilatação com elemento em cruz (4-conectado)."""
    return (
        mask
        | _shift(mask, 1, 0)
        | _shift(mask, -1, 0)
        | _shift(mask, 0, 1)
        | _shift(mask, 0, -1)
    )


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    """Dilata `mask` por `radius` passos em cruz (aproxima um disco pequeno).

    Para raios pequenos (1-4 px), a diferença entre disco e "diamante"
    4-conectado é irrelevante para fechar falhas de traço; para raios
    maiores isso deixaria de valer.
    """
    out = mask
    for _ in range(radius):
        out = _passo_cruz(out)
    return out


def erode(mask: np.ndarray, radius: int) -> np.ndarray:
    """Erode `mask` por `radius` passos (dilata o complemento e inverte)."""
    return ~dilate(~mask, radius)


def close_gaps(ink_mask: np.ndarray, radius: int) -> np.ndarray:
    """Máscara de "parede" usada só para CONTER o flood fill através de
    falhas finas — não é um fechamento morfológico clássico.

    Testei primeiro dilatar-e-depois-erodir (o fechamento morfológico de
    livro-texto) e ele NÃO funciona aqui: numa linha de 1 pixel de
    espessura, a erosão desfaz exatamente a ponte que a dilatação criou,
    porque o elemento em cruz não sobra o suficiente na vertical para
    sobreviver à erosão (confirmei isso com um teste que falhava). Por
    isso esta função apenas dilata a tinta por `radius` e devolve isso
    como "parede" para o `label_regions`; ela NÃO deve ser usada como a
    tinta final visível. A área de pintura de fato exclui a tinta
    original (`ink_mask`), não esta parede — ver `region_mask`/`fill_region`.

    `radius` é a metade da largura máxima de falha que se pretende
    conter, em pixels do documento (não em pontos/DPI — converta antes).
    Efeito colateral: os próprios pixels da falha ficam fora de qualquer
    região (viram "parede"), então não são pintados — sobra uma costura
    fina do tamanho da falha sem cor. Aceitável para falhas de 1-3 px;
    se isso incomodar, seria preciso um passo extra de "vazar tinta para
    dentro da falha", fora do escopo desta primeira versão.
    """
    if radius <= 0:
        return ink_mask.copy()
    return dilate(ink_mask, radius)


def label_regions(wall_mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Rotula as regiões conectadas do FUNDO (fora de `wall_mask`).

    `wall_mask` normalmente é o resultado de `close_gaps` (tinta original
    dilatada), não a tinta original crua — ver `close_gaps` para o motivo.
    Retorna (labels, n): `labels` é um array int32 (H, W) com 0 nas
    posições de parede e um rótulo >= 1 por região de fundo conectada
    (4-conectividade); `n` é o número de regiões.

    BFS iterativo em numpy puro (sem scipy), porque o Python embutido do
    AppImage do Krita não garante scipy instalado — mesma cautela do
    resto do plugin com dependências externas.
    """
    h, w = wall_mask.shape
    livre = ~wall_mask
    labels = np.zeros((h, w), dtype=np.int32)
    rotulo_atual = 0

    ys, xs = np.nonzero(livre)
    visitado_idx = 0
    pendente = np.zeros(h * w, dtype=np.int64)

    for i in range(ys.shape[0]):
        y0, x0 = int(ys[i]), int(xs[i])
        if labels[y0, x0] != 0 or not livre[y0, x0]:
            continue
        rotulo_atual += 1
        topo = 0
        pendente[topo] = y0 * w + x0
        topo += 1
        labels[y0, x0] = rotulo_atual
        while topo > 0:
            topo -= 1
            idx = pendente[topo]
            y, x = int(idx // w), int(idx % w)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and livre[ny, nx] and labels[ny, nx] == 0:
                    labels[ny, nx] = rotulo_atual
                    pendente[topo] = ny * w + nx
                    topo += 1

    return labels, rotulo_atual


def region_mask(labels: np.ndarray, seed_x: int, seed_y: int) -> np.ndarray:
    """Máscara booleana da região de `labels` que contém (seed_x, seed_y).

    `seed_y, seed_x` são coordenadas de pixel no documento (linha, coluna).
    Levanta ValueError se o ponto cair em cima de tinta (rótulo 0) — nesse
    caso o docker deve avisar o usuário a clicar dentro da área a colorir,
    não em cima da linha.
    """
    rotulo = labels[seed_y, seed_x]
    if rotulo == 0:
        raise ValueError("ponto clicado está sobre tinta, não sobre uma área fechada")
    return labels == rotulo


def fill_region(
    rgba: np.ndarray, area: np.ndarray, cor_rgba: tuple[int, int, int, int]
) -> np.ndarray:
    """Devolve uma cópia de `rgba` com `area` pintada em `cor_rgba`.

    Não modifica `rgba` no lugar. No docker, isso normalmente vira uma
    camada nova (não a lineart), para manter o preenchimento não
    destrutivo — mesma filosofia do módulo de retículas do projeto.
    """
    out = rgba.copy()
    out[area] = np.array(cor_rgba, dtype=np.uint8)
    return out
