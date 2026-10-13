"""Testes da sincronização de amostras (``hq_tools.core.amostras``).

Cobre as regras que importam para o usuário: amostras novas chegam mesmo com
a pasta já usada, edições dele são preservadas, amostra apagada não volta e o
marcador registra o que foi sincronizado.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

try:  # do repositório (unittest discover, pytest ou arquivo direto)
    from hq_tools.core import amostras
except ImportError:  # rodando de dentro de tests/: python3 test_amostras.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hq_tools.core import amostras


def escrever(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as handle:
        handle.write(conteudo)


class TestSincronizar(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="amostras-teste-")
        self.addCleanup(shutil.rmtree, self.raiz, True)
        self.pasta = os.path.join(self.raiz, "pasta")
        self.origem = os.path.join(self.raiz, "origem")
        os.makedirs(self.pasta)
        os.makedirs(self.origem)
        escrever(os.path.join(self.origem, "Ono_01_.svg"), "<svg>v1</svg>")
        escrever(os.path.join(self.origem, "Ono_02_.svg"), "<svg>dois</svg>")
        escrever(os.path.join(self.origem, "LEIAME.txt"), "nao e amostra")

    def ler(self, nome):
        with open(os.path.join(self.pasta, nome), encoding="utf-8") as handle:
            return handle.read()

    def test_pasta_vazia_recebe_todas_as_amostras(self):
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual(["Ono_01_.svg", "Ono_02_.svg"], resultado["copiadas"])
        self.assertEqual("<svg>v1</svg>", self.ler("Ono_01_.svg"))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "LEIAME.txt")))

    def test_segunda_chamada_nao_faz_nada(self):
        amostras.sincronizar(self.pasta, [self.origem])
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual([], resultado["copiadas"])
        self.assertEqual([], resultado["atualizadas"])

    def test_amostra_nova_chega_em_pasta_ja_usada(self):
        amostras.sincronizar(self.pasta, [self.origem])
        escrever(os.path.join(self.origem, "Ono_03_.svg"), "<svg>tres</svg>")
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual(["Ono_03_.svg"], resultado["copiadas"])
        self.assertEqual("<svg>tres</svg>", self.ler("Ono_03_.svg"))

    def test_edicao_do_usuario_e_preservada(self):
        amostras.sincronizar(self.pasta, [self.origem])
        escrever(os.path.join(self.pasta, "Ono_01_.svg"), "<svg>meu ajuste</svg>")
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual(["Ono_01_.svg"], resultado["preservadas"])
        self.assertEqual("<svg>meu ajuste</svg>", self.ler("Ono_01_.svg"))

    def test_amostra_apagada_nao_volta(self):
        amostras.sincronizar(self.pasta, [self.origem])
        os.remove(os.path.join(self.pasta, "Ono_02_.svg"))
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual([], resultado["copiadas"])
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "Ono_02_.svg")))

    def test_amostra_que_mudou_no_plugin_e_atualizada(self):
        amostras.sincronizar(self.pasta, [self.origem])
        escrever(os.path.join(self.origem, "Ono_01_.svg"), "<svg>v2</svg>")
        resultado = amostras.sincronizar(self.pasta, [self.origem])
        self.assertEqual(["Ono_01_.svg"], resultado["atualizadas"])
        self.assertEqual("<svg>v2</svg>", self.ler("Ono_01_.svg"))

    def test_origem_inexistente_e_tolerada(self):
        resultado = amostras.sincronizar(
            self.pasta, [os.path.join(self.raiz, "nao-existe"), self.origem]
        )
        self.assertEqual(["Ono_01_.svg", "Ono_02_.svg"], resultado["copiadas"])

    def test_marcador_registra_o_que_foi_sincronizado(self):
        amostras.sincronizar(self.pasta, [self.origem])
        with open(
            os.path.join(self.pasta, amostras.MARCADOR), encoding="utf-8"
        ) as handle:
            marcador = json.load(handle)
        self.assertEqual({"Ono_01_.svg", "Ono_02_.svg"}, set(marcador))


if __name__ == "__main__":
    unittest.main()
