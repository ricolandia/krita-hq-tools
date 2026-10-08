"""Docker "produção": checklist do roteiro com estados e meta semanal.

Cole o roteiro (a mesma sintaxe que gera páginas, com o personagem opcional na
fala) e use Ctrl+Enter: cada página vira um nó com os painéis do layout e cada
painel guarda o estado de produção (esboço, arte, final) e as falas. O texto
fica em ``roteiro.txt`` e o progresso em ``producao.json``, na pasta do
projeto; duplo clique abre a ``pagina_NNN.kra`` e o checklist sai em Markdown.
"""

import os
import time

from krita import DockWidget, Krita

from ...core import i18n
from ...core import krita_helpers as helpers
from ...core import registro, ui
from ...core.compat import (
    ANTIALIASING,
    CONTEXT_MENU,
    CONTROL_MODIFIER,
    KEY_ENTER,
    KEY_RETURN,
    USER_ROLE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from ...core.paths import PRODUCAO_DIR
from . import core as prod

LINHAS_SINTAXE = (
    i18n.t("Uma página por bloco; palavras-chave sem acento e sem maiúsculas."),
    i18n.t("pagina 1: começa uma página (nova página é criada sozinha)."),
    i18n.t("formato A4: A4, A5, A3, tirinha, americano, tankobon ou quadrado (padrão A4)."),
    i18n.t("dpi 300: de 72 a 1200 (padrão 300)."),
    i18n.t("layout grade2x2: quadro, splash, duplo-h, duplo-v, tira3, tira4, gradeRxC (ex.: grade3x3) ou LxC (ex.: 3x2), até 6 em cada eixo (padrão grade2x2)."),
    i18n.t("direcao rtl: leitura ocidental (ltr, padrão) ou mangá (rtl)."),
    i18n.t("margem 5% e sarjeta 2%: fração ou porcentagem (padrões 5% e 2%)."),
    i18n.t("fala p1: texto (fala do painel 1)."),
    i18n.t("fala p1 joao: texto (fala do painel 1 dita pelo Joao; o personagem é opcional)."),
    i18n.t("narracao p1: texto (narração do painel 1; 'legenda' também vale)."),
    i18n.t("plano p1: close (tipo de plano do painel; texto livre, ex.: geral, médio, close)."),
    i18n.t("A fala aponta para o painel N do layout (a grade define quantos painéis a página tem)."),
)

EXEMPLO = i18n.t(
    "pagina 1\n"
    "layout grade2x2\n"
    "plano p1: geral\n"
    "narracao p1: Era uma vez...\n"
    "fala p1 joao: Voce viu aquilo?\n"
    "fala p4 maria: Ultima fala."
)

CORES = {"esboco": "#8a8a8a", "arte": "#c07f1f", "final": "#2e8b57"}


class _CaixaRoteiro(QtWidgets.QPlainTextEdit):
    """Caixa do roteiro: Ctrl+Enter monta o checklist (Enter quebra linha)."""

    def __init__(self, ao_montar, pai=None):
        super().__init__(pai)
        self.ao_montar = ao_montar

    def keyPressEvent(self, evento):
        if (
            evento.key() in (KEY_RETURN, KEY_ENTER)
            and evento.modifiers() & CONTROL_MODIFIER
        ):
            self.ao_montar()
            return
        super().keyPressEvent(evento)


class _BarraEstados(QtWidgets.QWidget):
    """Barra de progresso em três segmentos: final, arte e esboço."""

    def __init__(self, pai=None):
        super().__init__(pai)
        self._contagem = {"final": 0, "arte": 0, "esboco": 0, "total": 0}
        self.setMinimumHeight(16)

    def set_contagem(self, contagem):
        self._contagem = dict(contagem)
        self.update()

    def paintEvent(self, evento):
        pintor = QtGui.QPainter(self)
        pintor.setRenderHint(ANTIALIASING, True)
        largura = float(self.width())
        altura = float(self.height())
        raio = 4.0
        caminho = QtGui.QPainterPath()
        caminho.addRoundedRect(QtCore.QRectF(0, 0, largura, altura), raio, raio)
        pintor.setClipPath(caminho)
        # fundo neutro: legível no tema claro e no escuro
        pintor.setPen(QtGui.QColor(0, 0, 0, 0))
        pintor.setBrush(QtGui.QColor(128, 128, 128, 60))
        pintor.drawRect(QtCore.QRectF(0, 0, largura, altura))
        total = max(0, int(self._contagem.get("total", 0)))
        if total > 0:
            x = 0.0
            for estado in ("final", "arte", "esboco"):
                fatia = largura * self._contagem.get(estado, 0) / float(total)
                if fatia <= 0:
                    continue
                pintor.setBrush(QtGui.QColor(CORES[estado]))
                pintor.drawRect(QtCore.QRectF(x, 0, fatia, altura))
                x += fatia
        pintor.setClipping(False)
        pintor.setBrush(QtGui.QColor(0, 0, 0, 0))
        pintor.setPen(QtGui.QPen(QtGui.QColor(128, 128, 128, 120), 1))
        pintor.drawRoundedRect(
            QtCore.QRectF(0.5, 0.5, largura - 1.0, altura - 1.0), raio, raio
        )
        pintor.end()


class ProducaoDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: produção'))
        registro.registrar("producao", self)
        self.config = Config()
        self.checklist = []
        self._carregando = False
        self._pagina_pendente = None
        self._icones_estado = {}
        # Auto-save do roteiro: grava sozinho depois da última tecla e no
        # fechamento da doca (o "Montar checklist" continua salvando também).
        self._timer_roteiro = QtCore.QTimer(self)
        self._timer_roteiro.setSingleShot(True)
        self._timer_roteiro.setInterval(1500)
        self._timer_roteiro.timeout.connect(self._salvar_roteiro_automatico)
        # Timetracking manual: a sessão vive em memória (monotonic) e o
        # acumulado vai para tempos.json na pausa e a cada minuto rodando.
        self.tempos = {"total": 0, "por_pagina": {}}
        self._sessao_inicio = None
        self._sessao_pagina = None
        self._sessao_pasta = None
        self._ultimo_save = None
        self._timer_tempo = QtCore.QTimer(self)
        self._timer_tempo.setInterval(1000)
        self._timer_tempo.timeout.connect(self._tick_tempo)
        self._build_ui()
        try:
            self.widget().destroyed.connect(self._salvar_ao_fechar)
        except (AttributeError, TypeError):
            pass
        self.recarregar()

    def canvasChanged(self, canvas):
        pass

    # ------------------------------------------------------------------ pasta

    def folder(self):
        """Pasta do projeto (onde ficam as páginas .kra)."""
        escolhida = self.config.get("producao.folder")
        if escolhida:
            return escolhida
        projeto = self.config.get("pages.last_folder")
        if projeto and os.path.isdir(projeto):
            return projeto
        return PRODUCAO_DIR

    def pasta_dados(self):
        """Onde ficam roteiro.txt, producao.json e checklist.md.

        No projeto, na subpasta ``producao/`` (criada junto com o projeto);
        sem projeto, na pasta padrão do plugin.
        """
        if self._pasta_padrao():
            return PRODUCAO_DIR
        return os.path.join(self.folder(), prod.PASTA)

    def _pasta_padrao(self):
        """True quando não há projeto nem escolha explícita (pasta do plugin)."""
        if self.config.get("producao.folder"):
            return False
        projeto = self.config.get("pages.last_folder")
        return not (projeto and os.path.isdir(projeto))

    def pick_folder(self):
        pasta = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(),
            i18n.t('Pasta do projeto'),
            self.folder() or os.path.expanduser("~"),
        )
        if pasta:
            self.config.set("producao.folder", pasta)
            self.recarregar()

    def open_folder(self):
        pasta = self.folder()
        if not pasta:
            helpers.show_message(i18n.t('Escolha a pasta do projeto.'))
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(pasta))

    # -------------------------------------------------------------------- UI

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        group_projeto = widgets.QGroupBox(i18n.t('Projeto'))
        projeto_layout = ui.espacamento(
            widgets.QVBoxLayout(group_projeto), margem=0, espaco=ui.GAP
        )
        linha_pasta = widgets.QHBoxLayout()
        self.lbl_pasta = ui.rotulo_info("")
        linha_pasta.addWidget(self.lbl_pasta, 1)
        botao_pasta = ui.botao(
            i18n.t('Pasta...'),
            i18n.t('Escolhe a pasta do projeto (a mesma das páginas .kra).'),
            icone_chave="pasta",
        )
        botao_pasta.clicked.connect(self.pick_folder)
        linha_pasta.addWidget(botao_pasta)
        botao_abrir = ui.botao(
            i18n.t('Abrir'), i18n.t('Abre a pasta do projeto no explorador de arquivos.')
        )
        botao_abrir.clicked.connect(self.open_folder)
        linha_pasta.addWidget(botao_abrir)
        botao_atualizar = ui.botao(
            i18n.t('Atualizar'),
            i18n.t('Relê o roteiro e o progresso da pasta do projeto.'),
            icone_chave="atualizar",
        )
        botao_atualizar.clicked.connect(self.recarregar)
        linha_pasta.addWidget(botao_atualizar)
        projeto_layout.addLayout(linha_pasta)
        layout.addWidget(group_projeto)
        layout.addWidget(ui.separador())

        group_roteiro = widgets.QGroupBox(i18n.t('Roteiro'))
        roteiro_layout = ui.espacamento(
            widgets.QVBoxLayout(group_roteiro), margem=0, espaco=ui.GAP
        )
        self.caixa = _CaixaRoteiro(self.montar, self)
        self.caixa.setPlaceholderText(
            i18n.t("Cole o roteiro aqui. Ctrl+Enter monta o checklist; 'Sintaxe...' mostra o formato.")
        )
        self.caixa.setMinimumHeight(140)
        self.caixa.textChanged.connect(self._roteiro_editado)
        roteiro_layout.addWidget(self.caixa, 1)
        linha_botoes = widgets.QHBoxLayout()
        botao_montar = ui.botao(
            i18n.t('Montar checklist'),
            i18n.t('Lê o roteiro (Ctrl+Enter), guarda o texto e monta a árvore de páginas e painéis.'),
            icone_chave="novo",
        )
        botao_montar.clicked.connect(self.montar)
        linha_botoes.addWidget(botao_montar)
        botao_sintaxe = ui.botao(
            i18n.t('Sintaxe...'), i18n.t('Mostra o formato do roteiro, com exemplos.')
        )
        botao_sintaxe.clicked.connect(self.mostrar_sintaxe)
        linha_botoes.addWidget(botao_sintaxe)
        botao_exportar = ui.botao(
            i18n.t('Exportar .md'),
            i18n.t('Salva o checklist em checklist.md na pasta do projeto (para espelhar onde quiser).'),
        )
        botao_exportar.clicked.connect(self.exportar_markdown)
        linha_botoes.addWidget(botao_exportar)
        roteiro_layout.addLayout(linha_botoes)
        self.lbl_roteiro_salvo = ui.rotulo_info("")
        roteiro_layout.addWidget(self.lbl_roteiro_salvo)
        layout.addWidget(group_roteiro)
        layout.addWidget(ui.separador())

        group_checklist = widgets.QGroupBox(i18n.t('Checklist'))
        checklist_layout = ui.espacamento(
            widgets.QVBoxLayout(group_checklist), margem=0, espaco=ui.GAP
        )
        self.arvore = widgets.QTreeWidget()
        self.arvore.setColumnCount(4)
        self.arvore.setHeaderLabels(
            [
                i18n.t('Página / Painel'),
                i18n.t('Estado'),
                i18n.t('Plano'),
                i18n.t('Falas'),
            ]
        )
        self.arvore.setColumnWidth(0, 130)
        self.arvore.setColumnWidth(1, 80)
        self.arvore.setColumnWidth(2, 80)
        self.arvore.setIconSize(QtCore.QSize(12, 12))
        self.arvore.itemClicked.connect(self._item_clicado)
        self.arvore.itemDoubleClicked.connect(self._item_duplo_clique)
        self.arvore.setContextMenuPolicy(CONTEXT_MENU)
        self.arvore.customContextMenuRequested.connect(self._menu_contexto)
        checklist_layout.addWidget(self.arvore, 1)

        linha_barra = widgets.QHBoxLayout()
        self.barra = _BarraEstados()
        linha_barra.addWidget(self.barra, 1)
        checklist_layout.addLayout(linha_barra)
        self.lbl_legenda = ui.rotulo("")
        self.lbl_legenda.setText(" &nbsp; ".join(
            '<span style="color:{0}">●</span> {1}'.format(
                CORES[estado], self._rotulo_estado(estado)
            )
            for estado in ("final", "arte", "esboco")
        ))
        checklist_layout.addWidget(self.lbl_legenda)

        linha_pendente = widgets.QHBoxLayout()
        self.lbl_pendente = ui.rotulo_info("")
        linha_pendente.addWidget(self.lbl_pendente, 1)
        botao_pendente = ui.botao(
            i18n.t('Abrir próxima pendente'),
            i18n.t('Abre a primeira página com painel não final e a seleciona na lista.'),
            icone_chave="abrir",
        )
        botao_pendente.clicked.connect(self.abrir_proxima_pendente)
        linha_pendente.addWidget(botao_pendente)
        checklist_layout.addLayout(linha_pendente)

        linha_meta = widgets.QHBoxLayout()
        linha_meta.addWidget(ui.rotulo(i18n.t('Meta semanal:')))
        self.meta = widgets.QSpinBox()
        self.meta.setRange(0, 200)
        self.meta.setSuffix(i18n.t(' painéis'))
        self.meta.valueChanged.connect(self._meta_mudou)
        linha_meta.addWidget(self.meta)
        self.lbl_meta = ui.rotulo_info("")
        linha_meta.addWidget(self.lbl_meta, 1)
        checklist_layout.addLayout(linha_meta)

        self.lbl_progresso = ui.rotulo_info("")
        checklist_layout.addWidget(self.lbl_progresso)

        linha_tempo = widgets.QHBoxLayout()
        self.btn_tempo = ui.botao(
            i18n.t('Iniciar'),
            i18n.t('Conta o tempo da produção (manual): inicia ou pausa a sessão.'),
        )
        self.btn_tempo.clicked.connect(self.alternar_tempo)
        linha_tempo.addWidget(self.btn_tempo)
        self.lbl_tempo = ui.rotulo_info("")
        linha_tempo.addWidget(self.lbl_tempo, 1)
        checklist_layout.addLayout(linha_tempo)
        layout.addWidget(group_checklist, 1)

        dica = ui.rotulo(
            i18n.t("1) Cole o roteiro e use Ctrl+Enter. 2) Clique na coluna Estado para ciclar esboço, arte e final (botão direito define direto). 3) Duplo clique na página abre a pagina_NNN.kra. O roteiro.txt e o producao.json ficam na pasta do projeto.")
        )
        layout.addWidget(dica)

        self.setWidget(main)

    # ----------------------------------------------------------------- fluxo

    def _roteiro_editado(self):
        """Reinicia o relógio do auto-save e avisa que há texto novo."""
        if self._carregando:
            return
        self.lbl_roteiro_salvo.setText(i18n.t('salvando…'))
        self._timer_roteiro.start()

    def _salvar_roteiro_automatico(self):
        """Grava o roteiro.txt sem passar pelo "Montar checklist"."""
        if self._carregando:
            return
        pasta = self.pasta_dados()
        try:
            os.makedirs(pasta, exist_ok=True)
            prod.salvar_roteiro(pasta, self.caixa.toPlainText())
        except OSError:
            self.lbl_roteiro_salvo.setText(i18n.t('falha ao salvar'))
            return
        self.lbl_roteiro_salvo.setText(
            i18n.t('salvo {0}').format(
                QtCore.QTime.currentTime().toString("HH:mm")
            )
        )

    def _salvar_ao_fechar(self):
        """Última gravação ao fechar a doca (o widget pode já estar morto)."""
        try:
            self._timer_roteiro.stop()
            self._parar_tempo()
            self._salvar_roteiro_automatico()
        except (AttributeError, RuntimeError):
            pass

    def recarregar(self):
        """Relê o roteiro e o progresso da pasta e remonta a árvore."""
        if self._sessao_inicio is not None:
            self._parar_tempo()
        pasta = self.pasta_dados()
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pass
        if self._pasta_padrao():
            self.lbl_pasta.setText(
                i18n.t('Escolha a pasta do projeto em "Pasta..." (salvando provisoriamente em {0}).').format(pasta)
            )
        else:
            self.lbl_pasta.setText(i18n.t('Projeto: {0}').format(self.folder()))
            self.lbl_pasta.setToolTip(i18n.t('Checklist em: {0}').format(pasta))
        self._carregando = True
        texto = prod.carregar_roteiro(pasta)
        estados, meta = prod.carregar(pasta)
        self.tempos = prod.carregar_tempos(pasta)
        self.caixa.setPlainText(texto)
        self.meta.setValue(meta)
        self._carregando = False
        if texto.strip():
            self._montar(texto, estados)
        else:
            self.checklist = []
            self._montar_arvore()
            self._atualizar_resumo()
        self._atualizar_tempo()

    def montar(self):
        """Lê o texto, monta o checklist e salva o roteiro e os estados."""
        texto = self.caixa.toPlainText()
        pasta = self.pasta_dados()
        estados, _ = prod.carregar(pasta)
        try:
            self._montar(texto, estados)
        except ValueError as erro:
            helpers.show_info(i18n.t('Produção'), i18n.t('Roteiro: {0}').format(erro))
            return
        try:
            prod.salvar_roteiro(pasta, texto)
            prod.salvar(pasta, prod.estados_do_checklist(self.checklist), self.meta.value())
        except OSError as erro:
            helpers.show_info(i18n.t('Produção'), i18n.t('Falha ao salvar: {0}').format(erro))
            return
        self.lbl_roteiro_salvo.setText(
            i18n.t('salvo {0}').format(
                QtCore.QTime.currentTime().toString("HH:mm")
            )
        )
        contagem = prod.progresso(self.checklist)
        helpers.show_message(
            i18n.t('Checklist montado: {0} página(s), {1} painel(éis).').format(
                len(self.checklist), contagem["total"]
            )
        )
        if self._pasta_padrao():
            helpers.show_message(
                i18n.t('Checklist salvo em {0}. Escolha a pasta do projeto para guardar junto das páginas.').format(pasta)
            )

    def _montar(self, texto, estados):
        self.checklist = prod.montar(texto, estados)
        self._montar_arvore()
        self._atualizar_resumo()

    def _montar_arvore(self):
        self.arvore.clear()
        pasta = self.folder()
        for pagina in self.checklist:
            finais, total = prod.progresso_da_pagina(pagina)
            item = QtWidgets.QTreeWidgetItem(
                [
                    i18n.t('Página {0}').format(pagina["pagina"]),
                    i18n.t('{0}/{1} finais').format(finais, total),
                    "",
                    "",
                ]
            )
            item.setData(0, USER_ROLE, ("pagina", pagina["pagina"]))
            arquivo = prod.pagina_do_arquivo(pasta, pagina["pagina"]) if pasta else None
            if arquivo:
                item.setText(2, os.path.basename(arquivo))
            else:
                item.setToolTip(
                    2,
                    i18n.t('Página ainda não gerada (pagina_{0:03d}.kra).').format(
                        pagina["pagina"]
                    ),
                )
            self.arvore.addTopLevelItem(item)
            for painel in pagina["paineis"]:
                filho = QtWidgets.QTreeWidgetItem(
                    [
                        i18n.t('Painel {0}').format(painel["painel"]),
                        self._rotulo_estado(painel["estado"]),
                        painel.get("plano", ""),
                        prod.falas_resumo(painel, i18n.t('Narração')),
                    ]
                )
                filho.setData(0, USER_ROLE, ("painel", pagina["pagina"], painel["painel"]))
                self._pintar_estado(filho, painel["estado"])
                item.addChild(filho)
            item.setExpanded(True)

    # --------------------------------------------------------------- estados

    def _rotulo_estado(self, estado):
        if estado == "arte":
            return i18n.t('Arte')
        if estado == "final":
            return i18n.t('Final')
        return i18n.t('Esboço')

    def _pintar_estado(self, item, estado):
        item.setForeground(1, QtGui.QBrush(QtGui.QColor(CORES.get(estado, "#8a8a8a"))))
        item.setIcon(1, self._icone_estado(estado))

    def _icone_estado(self, estado):
        """Bolinha colorida do estado (cacheada por estado)."""
        chave = estado if estado in CORES else "esboco"
        if chave in self._icones_estado:
            return self._icones_estado[chave]
        tamanho = 12
        pixmap = QtGui.QPixmap(tamanho, tamanho)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        pintor = QtGui.QPainter(pixmap)
        pintor.setRenderHint(ANTIALIASING, True)
        pintor.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 70), 1))
        pintor.setBrush(QtGui.QColor(CORES[chave]))
        pintor.drawEllipse(QtCore.QRectF(1.5, 1.5, tamanho - 3.0, tamanho - 3.0))
        pintor.end()
        icone = QtGui.QIcon(pixmap)
        self._icones_estado[chave] = icone
        return icone

    def _achar_pagina(self, numero):
        for pagina in self.checklist:
            if pagina["pagina"] == numero:
                return pagina
        return None

    def _achar_painel(self, numero_pagina, numero_painel):
        pagina = self._achar_pagina(numero_pagina)
        if pagina is None:
            return None
        for painel in pagina["paineis"]:
            if painel["painel"] == numero_painel:
                return painel
        return None

    def _definir_estado(self, item, numero_pagina, numero_painel, estado):
        painel = self._achar_painel(numero_pagina, numero_painel)
        if painel is None:
            return
        painel["estado"] = estado
        item.setText(1, self._rotulo_estado(estado))
        self._pintar_estado(item, estado)
        pai = item.parent()
        pagina = self._achar_pagina(numero_pagina)
        if pai is not None and pagina is not None:
            finais, total = prod.progresso_da_pagina(pagina)
            pai.setText(1, i18n.t('{0}/{1} finais').format(finais, total))
        self._salvar_estados()
        self._atualizar_resumo()

    def _item_clicado(self, item, coluna):
        dados = item.data(0, USER_ROLE)
        if coluna != 1 or not dados or dados[0] != "painel":
            return
        painel = self._achar_painel(dados[1], dados[2])
        if painel is None:
            return
        self._definir_estado(
            item, dados[1], dados[2], prod.proximo_estado(painel["estado"])
        )

    def _item_duplo_clique(self, item, coluna):
        dados = item.data(0, USER_ROLE)
        if dados and dados[0] == "pagina":
            self.abrir_pagina(dados[1])

    def _menu_contexto(self, posicao):
        item = self.arvore.itemAt(posicao)
        if item is None:
            return
        dados = item.data(0, USER_ROLE)
        if not dados:
            return
        menu = QtWidgets.QMenu(self)
        if dados[0] == "painel":
            for estado in prod.ESTADOS:
                acao = menu.addAction(self._rotulo_estado(estado))
                acao.setCheckable(True)
                acao.setChecked(
                    (self._achar_painel(dados[1], dados[2]) or {}).get("estado") == estado
                )
                acao.triggered.connect(
                    lambda marcado=False, alvo=estado, d=dados, i=item: self._definir_estado(
                        i, d[1], d[2], alvo
                    )
                )
            menu.addSeparator()
            avancar = menu.addAction(i18n.t('Avançar estado'))
            avancar.triggered.connect(
                lambda marcado=False, d=dados, i=item: self._definir_estado(
                    i, d[1], d[2], prod.proximo_estado((self._achar_painel(d[1], d[2]) or {}).get("estado", "esboco"))
                )
            )
        elif dados[0] == "pagina":
            abrir = menu.addAction(i18n.t('Abrir página'))
            abrir.triggered.connect(
                lambda marcado=False, numero=dados[1]: self.abrir_pagina(numero)
            )
        if menu.actions():
            menu.exec(self.arvore.viewport().mapToGlobal(posicao))

    def _salvar_estados(self):
        pasta = self.pasta_dados()
        try:
            prod.salvar(
                pasta, prod.estados_do_checklist(self.checklist), self.meta.value()
            )
        except OSError:
            pass

    def _meta_mudou(self, valor):
        if self._carregando:
            return
        self._salvar_estados()
        self._atualizar_resumo()

    def _atualizar_resumo(self):
        contagem = prod.progresso(self.checklist)
        total = contagem["total"]
        restantes = total - contagem["finais"]
        self.barra.set_contagem(contagem)
        self._atualizar_pendente()
        if total:
            porcentagem = int(round(100.0 * contagem["finais"] / total))
            self.lbl_progresso.setText(
                i18n.t('{0}/{1} painéis finais ({2}%) · {3} em arte · {4} em esboço').format(
                    contagem["finais"],
                    total,
                    porcentagem,
                    contagem["arte"],
                    contagem["esboco"],
                )
            )
        else:
            self.lbl_progresso.setText(i18n.t('Monte o checklist para ver o progresso.'))
        meta = self.meta.value()
        if total and restantes <= 0:
            self.lbl_meta.setText(i18n.t('Tudo finalizado!'))
        elif meta and restantes > 0:
            semanas, previsao = prod.projecao(restantes, meta)
            self.lbl_meta.setText(
                i18n.t('Faltam {0} painéis: ~{1} semana(s) · entrega ~{2}').format(
                    restantes, semanas, previsao.strftime('%d/%m')
                )
            )
        else:
            self.lbl_meta.setText(
                i18n.t('Defina a meta semanal para ver a projeção.')
            )

    def _atualizar_pendente(self):
        """Acha a primeira página com painel não final e marca na árvore."""
        self._pagina_pendente = None
        for pagina in self.checklist:
            finais, total = prod.progresso_da_pagina(pagina)
            if finais < total:
                self._pagina_pendente = pagina["pagina"]
                break
        for indice in range(self.arvore.topLevelItemCount()):
            item = self.arvore.topLevelItem(indice)
            dados = item.data(0, USER_ROLE)
            numero = dados[1] if dados else None
            rotulo = i18n.t('Página {0}').format(numero)
            if numero == self._pagina_pendente:
                item.setText(0, "▶ " + rotulo)
            else:
                item.setText(0, rotulo)
        if not self.checklist:
            self.lbl_pendente.setText("")
        elif self._pagina_pendente is None:
            self.lbl_pendente.setText(i18n.t('Tudo finalizado!'))
        else:
            self.lbl_pendente.setText(
                i18n.t('Próxima pendente: Página {0}').format(self._pagina_pendente)
            )

    def abrir_proxima_pendente(self):
        """Abre a primeira página com painel não final (selecionando na lista)."""
        if not self.checklist:
            helpers.show_message(i18n.t('Monte o checklist antes de abrir.'))
            return
        if self._pagina_pendente is None:
            helpers.show_message(i18n.t('Tudo finalizado!'))
            return
        self._selecionar_pagina(self._pagina_pendente)
        self.abrir_pagina(self._pagina_pendente)

    def _selecionar_pagina(self, numero):
        for indice in range(self.arvore.topLevelItemCount()):
            item = self.arvore.topLevelItem(indice)
            dados = item.data(0, USER_ROLE)
            if dados and dados[0] == "pagina" and dados[1] == numero:
                self.arvore.setCurrentItem(item)
                self.arvore.scrollToItem(item)
                return

    # ------------------------------------------------------------------ tempo

    def alternar_tempo(self):
        """Inicia ou pausa a sessão de trabalho (timetracking manual)."""
        if self._sessao_inicio is None:
            self._iniciar_tempo()
        else:
            self._parar_tempo()

    def _iniciar_tempo(self):
        self._sessao_pagina = self._pagina_selecionada()
        self._sessao_pasta = self.pasta_dados()
        self._sessao_inicio = time.monotonic()
        self._ultimo_save = self._sessao_inicio
        self._timer_tempo.start()
        self.btn_tempo.setText(i18n.t('Pausar'))
        self._atualizar_tempo()

    def _parar_tempo(self):
        if self._sessao_inicio is None:
            return
        self._persistir_tempo()
        self._sessao_inicio = None
        self._sessao_pagina = None
        self._sessao_pasta = None
        self._ultimo_save = None
        self._timer_tempo.stop()
        try:
            self.btn_tempo.setText(i18n.t('Iniciar'))
        except (AttributeError, RuntimeError):
            pass
        self._atualizar_tempo()

    def _persistir_tempo(self):
        """Soma o trecho desde o último save (parcial a cada minuto rodando)."""
        if self._sessao_inicio is None or self._ultimo_save is None:
            return
        agora = time.monotonic()
        segundos = int(agora - self._ultimo_save)
        self._ultimo_save = agora
        if segundos <= 0:
            return
        self.tempos = prod.acumular_tempo(
            self.tempos, self._sessao_pagina, segundos
        )
        try:
            prod.salvar_tempos(self._sessao_pasta or self.pasta_dados(), self.tempos)
        except OSError:
            pass

    def _tick_tempo(self):
        if self._sessao_inicio is None:
            return
        self._atualizar_tempo()
        if self._ultimo_save is not None and time.monotonic() - self._ultimo_save >= 60:
            self._persistir_tempo()

    def _atualizar_tempo(self):
        if self._sessao_inicio is None:
            if self.tempos.get("total"):
                self.lbl_tempo.setText(
                    i18n.t('Tempo total: {0}').format(
                        prod.formatar_duracao(self.tempos["total"])
                    )
                )
            else:
                self.lbl_tempo.setText(i18n.t('Sem tempo registrado.'))
            return
        cronometro = prod.formatar_cronometro(time.monotonic() - self._sessao_inicio)
        if self._sessao_pagina:
            self.lbl_tempo.setText(
                i18n.t('Tempo: {0} · Página {1} · total {2}').format(
                    cronometro,
                    self._sessao_pagina,
                    prod.formatar_duracao(self.tempos["total"]),
                )
            )
        else:
            self.lbl_tempo.setText(
                i18n.t('Tempo: {0} · total {1}').format(
                    cronometro, prod.formatar_duracao(self.tempos["total"])
                )
            )

    def _pagina_selecionada(self):
        """Número da página do item selecionado na árvore (ou None)."""
        item = self.arvore.currentItem()
        if item is None:
            return None
        dados = item.data(0, USER_ROLE)
        if not dados:
            return None
        return dados[1]

    # --------------------------------------------------------------- páginas

    def abrir_pagina(self, numero):
        pasta = self.folder()
        if not pasta:
            helpers.show_message(i18n.t('Escolha a pasta do projeto.'))
            return
        caminho = prod.pagina_do_arquivo(pasta, numero)
        if not caminho:
            helpers.show_message(
                i18n.t('A pagina_{0:03d}.kra ainda não existe na pasta.').format(numero)
            )
            return
        documento = Krita.instance().openDocument(caminho)
        if documento is None:
            helpers.show_info(i18n.t('Produção'), i18n.t('Não foi possível abrir a página.'))
            return
        helpers.present_document(documento)

    def exportar_markdown(self):
        if not self.checklist:
            helpers.show_message(i18n.t('Monte o checklist antes de exportar.'))
            return
        pasta = self.pasta_dados()
        rotulos = {
            "esboco": i18n.t('Esboço'),
            "arte": i18n.t('Arte'),
            "final": i18n.t('Final'),
            "narracao": i18n.t('Narração'),
            "plano": i18n.t('Plano'),
        }
        texto = prod.para_markdown(
            self.checklist,
            self.meta.value(),
            rotulos=rotulos,
            titulo=i18n.t('Checklist de produção'),
            tempos=self.tempos,
        )
        caminho = os.path.join(pasta, prod.ARQUIVO_CHECKLIST)
        try:
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
        except OSError as erro:
            helpers.show_info(i18n.t('Produção'), i18n.t('Falha ao salvar: {0}').format(erro))
            return
        helpers.show_message(i18n.t('Checklist salvo: {0}').format(caminho))

    # ---------------------------------------------------------------- sintaxe

    def mostrar_sintaxe(self):
        dialogo = QtWidgets.QDialog(self.widget())
        dialogo.setWindowTitle(i18n.t('Sintaxe do roteiro'))
        layout = ui.espacamento(QtWidgets.QVBoxLayout(dialogo))
        texto = QtWidgets.QPlainTextEdit(dialogo)
        texto.setReadOnly(True)
        corpo = "\n".join(LINHAS_SINTAXE)
        texto.setPlainText("{0}\n\n{1}\n\n{2}".format(corpo, i18n.t('Exemplo:'), EXEMPLO))
        layout.addWidget(texto, 1)
        fechar = ui.botao(i18n.t('Fechar'), i18n.t('Fecha a janela da sintaxe.'))
        fechar.clicked.connect(dialogo.accept)
        layout.addWidget(fechar)
        dialogo.resize(620, 460)
        dialogo.exec()
