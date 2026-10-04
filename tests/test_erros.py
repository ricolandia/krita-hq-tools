"""Testes da escrita de diagnóstico tolerante a stderr ausente.

No Krita do Windows (GUI sem console) ``sys.stderr`` é ``None``; a regra
estática garante que nenhum módulo de runtime volte a escrever direto nele.
"""

import io
import os
import sys
import unittest

from hq_tools.core import erros

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACOTE = os.path.join(RAIZ, "hq_tools")


class TestEscreverErro(unittest.TestCase):
    def test_stderr_none_nao_quebra(self):
        original = sys.stderr
        sys.stderr = None
        try:
            erros.escrever_erro("teste")
            erros.escrever_erro("teste", flush=True)
        finally:
            sys.stderr = original

    def test_escreve_quando_existe(self):
        buffer = io.StringIO()
        original = sys.stderr
        sys.stderr = buffer
        try:
            erros.escrever_erro("mensagem")
        finally:
            sys.stderr = original
        self.assertEqual(buffer.getvalue(), "mensagem")

    def test_flush_quando_pedido(self):
        buffer = io.StringIO()
        original = sys.stderr
        sys.stderr = buffer
        try:
            erros.escrever_erro("x", flush=True)
        finally:
            sys.stderr = original
        self.assertEqual(buffer.getvalue(), "x")


class TestSemStderrCru(unittest.TestCase):
    def test_runtime_nao_usa_sys_stderr_direto(self):
        problemas = []
        for raiz, dirs, nomes in os.walk(PACOTE):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in nomes:
                if not nome.endswith(".py") or nome == "erros.py":
                    continue
                caminho = os.path.join(raiz, nome)
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    if "sys.stderr" in arquivo.read():
                        problemas.append(caminho)
        self.assertEqual(problemas, [])


if __name__ == "__main__":
    unittest.main()
