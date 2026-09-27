"""Checagem estática: nomes globais usados sem definição (fora do Krita).

Pega o caso clássico de constante usada sem import (o DIALOG_YES do docker de
retículas derrubava o Krita ao excluir um preset). Não importa os módulos do
plugin, só analisa o código com ``symtable``, então roda em qualquer Python.
"""

import builtins
import os
import symtable
import unittest

PLUGIN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hq_tools"
)

# Nomes implícitos do interpretador.
IGNORADOS = {
    "__annotations__",
    "__builtins__",
    "__class__",
    "__doc__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


def _nomes_do_topo(tabela):
    """Nomes definidos ou importados no escopo de módulo."""
    nomes = set()
    for simbolo in tabela.get_symbols():
        if (
            simbolo.is_imported()
            or simbolo.is_assigned()
            or simbolo.is_namespace()
            or simbolo.is_parameter()
        ):
            nomes.add(simbolo.get_name())
    return nomes


def _checar(caminho):
    """Devolve a lista de referências globais sem definição no arquivo."""
    with open(caminho, "r", encoding="utf-8") as handle:
        fonte = handle.read()
    tabela = symtable.symtable(fonte, caminho, "exec")
    definidos = _nomes_do_topo(tabela) | set(dir(builtins))
    problemas = []

    def visitar(tabela_atual):
        for filho in tabela_atual.get_children():
            for simbolo in filho.get_symbols():
                nome = simbolo.get_name()
                if nome in IGNORADOS:
                    continue
                if not simbolo.is_referenced():
                    continue
                if (
                    simbolo.is_assigned()
                    or simbolo.is_imported()
                    or simbolo.is_namespace()
                    or simbolo.is_parameter()
                    or simbolo.is_free()
                    or simbolo.is_local()
                ):
                    continue
                if nome not in definidos:
                    problemas.append(
                        "{0}: {1} usa '{2}' sem definição".format(
                            caminho, filho.get_lineno(), nome
                        )
                    )
            visitar(filho)

    for simbolo in tabela.get_symbols():
        nome = simbolo.get_name()
        if nome in IGNORADOS:
            continue
        if (
            simbolo.is_referenced()
            and nome not in definidos
        ):
            problemas.append(
                "{0}: escopo de módulo usa '{1}' sem definição".format(
                    caminho, nome
                )
            )
    visitar(tabela)
    return problemas


class TestNomesGlobais(unittest.TestCase):
    def test_sem_nomes_indefinidos(self):
        problemas = []
        for base, diretorios, arquivos in os.walk(PLUGIN_DIR):
            diretorios[:] = [d for d in diretorios if d != "__pycache__"]
            for nome in sorted(arquivos):
                if nome.endswith(".py"):
                    problemas.extend(_checar(os.path.join(base, nome)))
        self.assertEqual(problemas, [], "\n".join(problemas))


if __name__ == "__main__":
    unittest.main()