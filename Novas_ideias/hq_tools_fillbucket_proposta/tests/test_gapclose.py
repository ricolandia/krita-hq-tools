"""Testes do núcleo puro de fechamento de gaps (sem Krita)."""
import unittest

import numpy as np

from core.gapclose import (
    close_gaps,
    dilate,
    erode,
    fill_region,
    label_regions,
    luminance_mask,
    region_mask,
)


MARGEM = 6  # espaço ao redor do quadrado para existir um pixel "exterior" real


def quadrado_com_falha(lado: int, falha_px: int) -> np.ndarray:
    """Um quadrado oco (contorno preto) de `lado` x `lado`, desenhado com
    margem em branco ao redor (para existir um "exterior" de verdade), com
    uma falha de `falha_px` pixels no meio do lado de cima."""
    canvas = lado + 2 * MARGEM
    rgba = np.full((canvas, canvas, 4), 255, dtype=np.uint8)
    rgba[:, :, 3] = 255
    b0, b1 = MARGEM, MARGEM + lado - 1
    rgba[b0, b0:b1 + 1, :3] = 0
    rgba[b1, b0:b1 + 1, :3] = 0
    rgba[b0:b1 + 1, b0, :3] = 0
    rgba[b0:b1 + 1, b1, :3] = 0
    if falha_px > 0:
        meio = b0 + lado // 2
        ini = meio - falha_px // 2
        rgba[b0, ini : ini + falha_px, :3] = 255  # buraco na borda de cima
    return rgba


class TesteDilateErode(unittest.TestCase):
    def test_dilate_cresce_um_pixel_em_cruz(self):
        m = np.zeros((5, 5), dtype=bool)
        m[2, 2] = True
        d = dilate(m, 1)
        esperado = {(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)}
        self.assertEqual(set(map(tuple, np.argwhere(d))), esperado)

    def test_erode_desfaz_dilate_em_forma_convexa(self):
        m = np.zeros((7, 7), dtype=bool)
        m[3, 3] = True
        self.assertTrue(np.array_equal(erode(dilate(m, 2), 2), m))


class TesteCloseGaps(unittest.TestCase):
    def test_falha_pequena_fecha_com_raio_suficiente(self):
        rgba = quadrado_com_falha(lado=20, falha_px=2)
        ink = luminance_mask(rgba)
        fechado = close_gaps(ink, radius=2)
        labels, n = label_regions(fechado)
        # interior: centro do quadrado. exterior: canto do canvas, fora
        # da margem, garantidamente fora do quadrado.
        interior = labels[MARGEM + 10, MARGEM + 10]
        exterior = labels[0, 0]
        self.assertNotEqual(interior, 0)
        self.assertNotEqual(exterior, 0)
        self.assertNotEqual(interior, exterior)

    def test_falha_pequena_nao_fecha_sem_raio(self):
        rgba = quadrado_com_falha(lado=20, falha_px=2)
        ink = luminance_mask(rgba)
        sem_fechar = close_gaps(ink, radius=0)
        labels, n = label_regions(sem_fechar)
        # sem fechar a falha, interior e exterior devem ser a MESMA região
        # (dá pra "vazar" pela falha de 2px)
        interior = labels[MARGEM + 10, MARGEM + 10]
        exterior = labels[0, 0]
        self.assertEqual(interior, exterior)

    def test_falha_grande_nao_fecha_com_raio_pequeno(self):
        rgba = quadrado_com_falha(lado=20, falha_px=6)
        ink = luminance_mask(rgba)
        fechado = close_gaps(ink, radius=1)
        labels, n = label_regions(fechado)
        interior = labels[MARGEM + 10, MARGEM + 10]
        exterior = labels[0, 0]
        self.assertEqual(
            interior, exterior,
            "raio pequeno não deveria fechar uma falha de 6px; se este "
            "teste falhar, ajuste os parâmetros do teste, não o algoritmo",
        )


class TesteFillRegion(unittest.TestCase):
    def test_preenche_so_a_regiao_do_seed(self):
        rgba = quadrado_com_falha(lado=20, falha_px=0)  # sem falha
        ink = luminance_mask(rgba)
        parede = close_gaps(ink, radius=1)
        labels, _ = label_regions(parede)
        p = MARGEM + 10
        # a área final de pintura sempre exclui a tinta original — ver o
        # docstring do módulo (region_mask sozinho já exclui a "parede"
        # dilatada, que é um pouco maior que a tinta real; aqui isso não
        # faz diferença porque o ponto testado está bem longe da borda).
        area = region_mask(labels, seed_x=p, seed_y=p) & ~ink
        pintado = fill_region(rgba, area, (255, 0, 0, 255))
        self.assertTrue(np.all(pintado[p, p] == [255, 0, 0, 255]))
        # fora do quadrado não deve ter sido pintado
        self.assertTrue(np.all(pintado[0, 0] == rgba[0, 0]))
        # a própria linha do contorno não deve ter sido pintada
        self.assertTrue(np.all(pintado[MARGEM, MARGEM + 10] == rgba[MARGEM, MARGEM + 10]))

    def test_seed_em_cima_da_tinta_levanta_erro(self):
        rgba = quadrado_com_falha(lado=20, falha_px=0)
        ink = luminance_mask(rgba)
        labels, _ = label_regions(ink)
        with self.assertRaises(ValueError):
            # (MARGEM, MARGEM) é o canto superior-esquerdo do contorno do
            # quadrado, ou seja, tinta de verdade — (0,0) seria só margem
            # branca e não serve para este teste.
            region_mask(labels, seed_x=MARGEM, seed_y=MARGEM)


if __name__ == "__main__":
    unittest.main()
