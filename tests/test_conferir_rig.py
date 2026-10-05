"""Testes da conferência de rig (scripts/conferir-rig3d.py)."""

import importlib.util
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "conferir-rig3d.py"


def carregar_script():
    spec = importlib.util.spec_from_file_location("conferir_rig3d", str(SCRIPT))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


conferir = carregar_script()


def modelo(ossos):
    return {"ossos": ossos, "vertices": [], "faces": []}


IDENTIDADE = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class TestCompararRig(unittest.TestCase):
    def test_igual_nao_aponta_nada(self):
        ossos = [
            {"nome": "root.x", "pai": None, "matriz": IDENTIDADE},
            {"nome": "head.x", "pai": 0, "matriz": IDENTIDADE},
        ]
        faltando, extras, pais, mapas, _ = conferir.comparar(
            modelo(ossos), modelo(ossos)
        )
        self.assertEqual((faltando, extras, pais, mapas), ([], [], [], []))

    def test_osso_faltando(self):
        referencia = modelo([{"nome": "root.x", "pai": None, "matriz": IDENTIDADE}])
        candidato = modelo([])
        faltando, extras, _, _, _ = conferir.comparar(referencia, candidato)
        self.assertEqual(faltando, ["root.x"])
        self.assertEqual(extras, [])

    def test_pai_diferente(self):
        referencia = modelo([
            {"nome": "root.x", "pai": None, "matriz": IDENTIDADE},
            {"nome": "head.x", "pai": 0, "matriz": IDENTIDADE},
        ])
        candidato = modelo([
            {"nome": "root.x", "pai": None, "matriz": IDENTIDADE},
            {"nome": "head.x", "pai": None, "matriz": IDENTIDADE},
        ])
        _, _, pais, _, _ = conferir.comparar(referencia, candidato)
        self.assertEqual(pais, ["head.x"])

    def test_orientacao_invertida_muda_o_mapeamento(self):
        referencia = modelo([
            {"nome": "arm.l", "pai": None, "matriz": IDENTIDADE},
        ])
        # Inverte o eixo Z da matriz (coluna 2, elemento 10): o sinal de
        # "abrir" troca e o mapeamento semântico tem de acusar.
        invertida = list(IDENTIDADE)
        invertida[10] = -1.0
        candidato = modelo([
            {"nome": "arm.l", "pai": None, "matriz": invertida},
        ])
        _, _, _, mapas, delta = conferir.comparar(referencia, candidato)
        self.assertEqual(len(mapas), 1)
        self.assertEqual(mapas[0][0], "arm.l")
        self.assertGreater(delta, 0.5)


if __name__ == "__main__":
    unittest.main()
