"""Testes da camada de widgets (``core/ui.py``) e da regra dos dockers.

Duas coisas diferentes são verificadas aqui:

1. **Contrato dos helpers** — o botão sempre ganha tooltip, o rótulo de estado
   sempre quebra linha e não reserva largura, o ícone cai no fallback. Roda com o
   Qt falso de ``tests/qt_falso.py``: como não há PyQt na máquina de CI (nem na
   de desenvolvimento), o que dá para provar é o que o helper *pediu* ao widget, e
   é exatamente a parte que estava espalhada e divergindo.

2. **Regra dos dockers**, por análise estática: nenhum ``QPushButton`` criado
   direto (tem que passar por :func:`ui.botao`) e nenhuma altura fixa (quebra a
   conformidade com o tema). Sem essa trava, o próximo botão nasce sem tooltip de
   novo, que é exatamente como os 52 botões ficaram.
"""

import ast
import pathlib
import unittest

from hq_tools.core import ui

REPO = pathlib.Path(__file__).resolve().parent.parent
MODULES = REPO / "hq_tools" / "modules"


class Sinal:
    """Sinal falso: ``widget.clicked.connect(slot)`` vira uma chamada anotada.

    Precisa existir porque ``clicked.connect`` é o caminho que ``ui.botao`` usa
    para prender o slot, e sem ele o teste não provaria nada do que importa.
    """

    def __init__(self, nome, registro):
        self._nome = nome
        self._registro = registro

    def __call__(self, *argumentos, **opcoes):
        self._registro.append((self._nome, argumentos, opcoes))
        return self

    def __getattr__(self, metodo):
        def ligar(*argumentos, **opcoes):
            self._registro.append((metodo, argumentos, opcoes))
            return self

        return ligar


class Gravador:
    """Widget falso que anota o que o helper pediu que ele fizesse."""

    def __init__(self, nome, argumentos, registro):
        self.classe = nome
        self.argumentos = argumentos
        self.registro = registro
        registro.append(("criar", nome, argumentos))

    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        return Sinal(nome, self.registro)

    def __repr__(self):  # pragma: no cover - só para mensagem de falha
        return "<{0} falso>".format(self.classe)


class QtGravado:
    """Substitui ``ui.QtWidgets`` e devolve um widget que anota cada chamada."""

    def __init__(self):
        self.registro = []

    def __getattr__(self, nome):
        def criar(*argumentos):
            return Gravador(nome, argumentos, self.registro)

        return criar

    def chamadas(self, metodo):
        return [item for item in self.registro if item[0] == metodo]

    def criados(self, classe):
        return [item for item in self.registro if item[:2] == ("criar", classe)]


class TestContrato(unittest.TestCase):
    def setUp(self):
        self.qt = QtGravado()
        self.qt_anterior = ui.QtWidgets
        ui.QtWidgets = self.qt

    def tearDown(self):
        ui.QtWidgets = self.qt_anterior

    def test_botao_sempre_tem_dica(self):
        ui.botao("Aplicar", "Cria a camada de preenchimento.")
        dicas = self.qt.chamadas("setToolTip")
        self.assertEqual(1, len(dicas), "o botão precisa de exatamente uma dica")
        self.assertEqual(("Cria a camada de preenchimento.",), dicas[0][1])

    def test_botao_conecta_o_slot_e_mantem_o_rotulo(self):
        alvo = lambda: None  # noqa: E731 - só para ver se foi conectado
        widget = ui.botao("Atualizar", "Relê os presets.", slot=alvo, icone_chave="atualizar")
        self.assertEqual("Atualizar", widget.argumentos[0])
        self.assertEqual((alvo,), self.qt.chamadas("connect")[0][1])
        self.assertEqual(1, len(self.qt.chamadas("setIcon")))

    def test_botao_sem_slot_nao_conecta(self):
        ui.botao("Ver licença", "Abre a licença do pack.")
        self.assertEqual([], self.qt.chamadas("connect"))

    def test_dica_e_argumento_obrigatorio(self):
        # Se algum dia `dica` ganhar valor padrão, a trava some em silêncio.
        import inspect

        assinatura = inspect.signature(ui.botao)
        self.assertEqual(
            inspect.Parameter.empty,
            assinatura.parameters["dica"].default,
            "a dica do botão tem que ser obrigatória na assinatura",
        )

    def test_rotulo_quebra_linha(self):
        widget = ui.rotulo("Clique no cartão para ativar o pincel.")
        self.assertEqual((True,), self.qt.chamadas("setWordWrap")[0][1])
        self.assertEqual("QLabel", widget.classe)

    def test_rotulo_info_quebra_linha_e_nao_reserva_largura(self):
        # Rótulo de estado: sem o wrap e sem zerar a largura mínima, um aviso de
        # 90 caracteres estufa o docker em vez de quebrar a linha.
        ui.rotulo_info("Célula: 4.32 px a 300 dpi (máx. 85.7 lpi) — reduzida ao aplicar")
        self.assertEqual((True,), self.qt.chamadas("setWordWrap")[0][1])
        larguras = self.qt.chamadas("setMinimumWidth")
        self.assertEqual(1, len(larguras), "a largura mínima precisa ser zerada")
        self.assertEqual((0,), larguras[0][1])

    def test_separador_usa_a_linha_do_tema(self):
        ui.separador()
        self.assertEqual(1, len(self.qt.criados("QFrame")))

    def test_espacamento_aplica_margem_e_gap(self):
        layout = Gravador("QLayout", (), self.qt.registro)
        devolvido = ui.espacamento(layout)
        self.assertIs(layout, devolvido, "o layout tem que voltar, para encadear")
        self.assertEqual(
            [(ui.MARGEM,) * 4], [chamada[1] for chamada in self.qt.chamadas("setContentsMargins")]
        )
        self.assertEqual([(ui.GAP,)], [chamada[1] for chamada in self.qt.chamadas("setSpacing")])

    def test_painel_devolve_widget_e_layout(self):
        widget, layout = ui.painel()
        self.assertEqual(["QWidget", "QVBoxLayout"], [c[1] for c in self.qt.criados("QWidget") + self.qt.criados("QVBoxLayout")])


class TestIcones(unittest.TestCase):
    def setUp(self):
        self.vistos = []
        self.anterior = ui.standard_icon
        ui.standard_icon = lambda nome: self.vistos.append(nome) or nome

    def tearDown(self):
        ui.standard_icon = self.anterior

    def test_chave_conhecida_usa_o_nome_do_tema(self):
        self.assertEqual("SP_DirOpenIcon", ui.icone("pasta"))
        self.assertEqual(["SP_DirOpenIcon"], self.vistos)

    def test_chave_desconhecida_cai_no_fallback(self):
        # Ícone faltando é só feio; botão que não abre é pior que ícone feio.
        self.assertEqual(ui.ICONE_FALLBACK, ui.icone("seta_magica"))
        self.assertEqual("SP_FileIcon", self.vistos[0])

    def test_nomes_sao_padronizaveis(self):
        for chave, nome in ui.ICONES.items():
            self.assertTrue(chave.islower(), "chave de ícone em minúsculas: " + chave)
            self.assertEqual(chave, chave.strip(), "chave sem espaço nas bordas: " + chave)
            self.assertTrue(nome.startswith("SP_"), nome + " não é um QStyle.StandardPixmap")


def _chamadas_de_widget(arvore, nome_metodo):
    """Nomes de método Qt chamados no arquivo (ex.: ``widgets.setToolTip``)."""
    achados = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call) or not isinstance(no.func, ast.Attribute):
            continue
        if no.func.attr == nome_metodo:
            achados.append(no.lineno)
    return achados


def _criacoes_de_widget(arvore, classe):
    """Linhas onde ``QPushButton`` é construído direto."""
    achados = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        func = no.func
        nome = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if nome == classe:
            achados.append(no.lineno)
    return achados


def _dockers():
    return sorted(p for p in MODULES.rglob("*.py") if "docker" in p.name)


class TestRegraDosDockers(unittest.TestCase):
    """O que impede os botões e as alturas fixas de voltarem."""

    def _arquivos(self):
        return _dockers()

    def test_existe_pelo_menos_um_docker(self):
        # Se o glob parar de achar os dockers, o teste vira uma comparação com
        # lista vazia e passa sem verificar nada.
        caminhos = self._arquivos()
        self.assertGreaterEqual(len(caminhos), 7)
        for caminho in caminhos:
            self.assertTrue(caminho.is_file())

    def test_nenhum_botao_criado_direto(self):
        problemas = []
        for caminho in self._arquivos():
            arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
            for linha in _criacoes_de_widget(arvore, "QPushButton"):
                problemas.append("{0}:{1}: QPushButton direto; use ui.botao()".format(caminho.name, linha))
        self.assertEqual([], problemas, "\n".join(problemas))

    def test_nenhuma_altura_fixa(self):
        # setFixedHeight/setFixedWidth brigam com o tema escolhido e com o alto
        # dpi; era o que travava a altura dos botões de cor.
        problemas = []
        for caminho in self._arquivos():
            arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
            for metodo in ("setFixedHeight", "setFixedWidth"):
                for linha in _chamadas_de_widget(arvore, metodo):
                    problemas.append(
                        "{0}:{1}: {2}(); deixe o tema decidir o tamanho".format(caminho.name, linha, metodo)
                    )
        self.assertEqual([], problemas, "\n".join(problemas))


class TestSemImportsQuebrados(unittest.TestCase):
    def test_ui_importa_apenas_o_compat(self):
        # ui.py tem que continuar importável sem o Krita, para os testes.
        fonte = (REPO / "hq_tools" / "core" / "ui.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        importados = set()
        for no in ast.walk(arvore):
            if isinstance(no, ast.ImportFrom):
                importados.update(alias.name for alias in no.names)
            elif isinstance(no, ast.Import):
                importados.update(alias.name for alias in no.names)
        for nome in importados:
            self.assertFalse(
                nome.startswith("krita"),
                "ui.py não pode depender do Krita: " + nome,
            )


if __name__ == "__main__":
    unittest.main()