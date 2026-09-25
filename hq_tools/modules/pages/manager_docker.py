"""Docker de páginas: gerenciador com miniaturas e gerador a partir do roteiro.

O gerenciador lê o ``comicsConfig.json`` de um projeto do CPMT (ou uma pasta
qualquer com arquivos ``.kra``), mostra as miniaturas internas das páginas,
abre a página com duplo clique e permite reordenar arrastando (a ordem é
gravada no projeto). A aba Roteiro gera páginas novas a partir da sintaxe
própria do HQ Tools.
"""

import os

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    DRAG_INTERNAL_MOVE,
    ICON_MODE,
    LIST_ADJUST,
    MOVE_ACTION,
    USER_ROLE,
    WAIT_CURSOR,
    QtCore,
    QtGui,
    QtWidgets,
    pyqtSignal,
)
from ...core.config import Config
from ...core.cpmt import CPMTProject
from ...core.thumbs import thumbnail_pixmap
from . import generator, roteiro

SAMPLE_SCRIPT = """# Roteiro de exemplo
pagina 1
formato A4
layout grade2x2
narracao p1: Era uma vez, numa cidade pequena...
fala p1: Voce viu aquilo?
fala p2: Nao vi nada.
fala p3: Entao olhe de novo.
"""


class PageListWidget(QtWidgets.QListWidget):
    orderChanged = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


class PagesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: páginas")
        self.config = Config()
        self.project = None
        self.folder = ""
        self._loading = False
        self._build_ui()
        last = self.config.get("pages.last_project")
        if last and os.path.isfile(last):
            self._load_project(last)

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)
        self.tabs = widgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_manager_tab(), "Gerenciador")
        self.tabs.addTab(self._build_script_tab(), "Roteiro")
        self.setWidget(main)

    def _build_manager_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        row = widgets.QHBoxLayout()
        self.lbl_project = widgets.QLabel("Nenhum projeto aberto.")
        self.lbl_project.setWordWrap(True)
        row.addWidget(self.lbl_project, 1)
        button_open = widgets.QPushButton("Projeto...")
        button_open.setToolTip("Abrir um comicsConfig.json do CPMT")
        button_open.clicked.connect(self.pick_project)
        row.addWidget(button_open)
        button_folder = widgets.QPushButton("Pasta...")
        button_folder.setToolTip("Abrir uma pasta com arquivos .kra")
        button_folder.clicked.connect(self.pick_folder)
        row.addWidget(button_folder)
        layout.addLayout(row)

        row2 = widgets.QHBoxLayout()
        button_refresh = widgets.QPushButton("Atualizar miniaturas")
        button_refresh.clicked.connect(self.refresh)
        row2.addWidget(button_refresh)
        button_open_folder = widgets.QPushButton("Abrir pasta")
        button_open_folder.clicked.connect(self.open_current_folder)
        row2.addWidget(button_open_folder)
        layout.addLayout(row2)

        self.list_pages = PageListWidget()
        self.list_pages.setViewMode(ICON_MODE)
        self.list_pages.setIconSize(QtCore.QSize(150, 210))
        self.list_pages.setGridSize(QtCore.QSize(180, 250))
        self.list_pages.setResizeMode(LIST_ADJUST)
        self.list_pages.setDragDropMode(DRAG_INTERNAL_MOVE)
        self.list_pages.setDefaultDropAction(MOVE_ACTION)
        self.list_pages.setWordWrap(True)
        self.list_pages.itemDoubleClicked.connect(self.open_page)
        self.list_pages.orderChanged.connect(self._on_order_changed)
        layout.addWidget(self.list_pages, 1)

        hint = widgets.QLabel(
            "Clique duas vezes para abrir a página. Arraste para reordenar "
            "(a ordem é salva no projeto CPMT)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return tab

    def _build_script_tab(self):
        widgets = QtWidgets
        tab = widgets.QWidget()
        layout = widgets.QVBoxLayout(tab)

        form = widgets.QFormLayout()
        self.cmb_format = widgets.QComboBox()
        for name in roteiro.FORMATS:
            self.cmb_format.addItem(name)
        self.cmb_format.setCurrentText(self.config.get("pages.format", "A4"))
        form.addRow("Formato:", self.cmb_format)

        self.spin_dpi = widgets.QSpinBox()
        self.spin_dpi.setRange(72, 1200)
        self.spin_dpi.setValue(int(self.config.get("pages.dpi", 300)))
        form.addRow("DPI:", self.spin_dpi)

        self.chk_use_project = widgets.QCheckBox("Gerar dentro do projeto CPMT aberto")
        self.chk_use_project.setChecked(True)
        form.addRow("", self.chk_use_project)
        layout.addLayout(form)

        self.txt_script = widgets.QPlainTextEdit(SAMPLE_SCRIPT)
        self.txt_script.setTabChangesFocus(True)
        layout.addWidget(self.txt_script, 1)

        button_generate = widgets.QPushButton("Gerar páginas")
        button_generate.clicked.connect(self.generate_pages)
        layout.addWidget(button_generate)

        hint = widgets.QLabel(
            "Sintaxe: pagina, formato, dpi, layout (grade2x2, tira3, 2x3...), "
            "direcao (ltr/rtl), margem, sarjeta, fala pN: texto, "
            "narracao pN: texto. Veja docs/ROTEIRO-SINTAXE.md."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return tab

    def pick_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.widget(), "Abrir comicsConfig.json", self.folder, "comicsConfig.json"
        )
        if path:
            self._load_project(path)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), "Pasta com páginas .kra", self.folder or os.path.expanduser("~")
        )
        if folder:
            self.project = None
            self.folder = folder
            self.lbl_project.setText("Pasta: {0}".format(folder))
            self.refresh()

    def _load_project(self, config_path):
        try:
            self.project = CPMTProject(os.path.dirname(config_path))
        except (OSError, ValueError):
            helpers.show_message("Não foi possível abrir o projeto CPMT.")
            return
        self.folder = self.project.pages_dir()
        self.lbl_project.setText(
            "Projeto: {0} ({1} páginas)".format(
                self.project.project_name, len(self.project.page_relatives())
            )
        )
        self.config.set("pages.last_project", config_path)
        self.refresh()

    def open_current_folder(self):
        folder = self.folder
        if not folder:
            helpers.show_message("Abra um projeto ou uma pasta primeiro.")
            return
        os.makedirs(folder, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def _page_paths(self):
        if self.project is not None:
            return list(zip(self.project.page_relatives(), self.project.page_paths()))
        if not self.folder:
            return []
        try:
            names = sorted(
                name for name in os.listdir(self.folder) if name.lower().endswith(".kra")
            )
        except OSError:
            return []
        return [(name, os.path.join(self.folder, name)) for name in names]

    def refresh(self):
        self._loading = True
        self.list_pages.clear()
        for relative, path in self._page_paths():
            item = QtWidgets.QListWidgetItem(os.path.basename(path))
            item.setData(USER_ROLE, relative)
            item.setToolTip(path)
            pixmap = thumbnail_pixmap(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_pages.addItem(item)
        self._loading = False
        if self.project is not None:
            self.lbl_project.setText(
                "Projeto: {0} ({1} páginas)".format(
                    self.project.project_name, self.list_pages.count()
                )
            )

    def _on_order_changed(self):
        if self._loading or self.project is None:
            return
        ordered = [
            self.list_pages.item(index).data(USER_ROLE)
            for index in range(self.list_pages.count())
        ]
        self.project.set_page_order(ordered)
        helpers.show_message("Ordem das páginas atualizada no projeto.")

    def open_page(self, item):
        relative = item.data(USER_ROLE)
        path = relative
        if self.project is not None:
            path = os.path.join(self.project.root, relative)
        elif self.folder:
            path = os.path.join(self.folder, relative)
        if not os.path.isfile(path):
            helpers.show_message("Arquivo não encontrado: {0}".format(path))
            return
        document = Krita.instance().openDocument(path)
        if document is None:
            helpers.show_message("Não foi possível abrir a página.")
            return
        window = Krita.instance().activeWindow()
        if window is not None:
            window.addView(document)
        Krita.instance().setActiveDocument(document)

    def generate_pages(self):
        script = self.txt_script.toPlainText()
        try:
            pages = roteiro.parse_script(script)
        except roteiro.RoteiroError as error:
            helpers.show_message(str(error))
            return
        if not pages:
            helpers.show_message("O roteiro está vazio.")
            return

        self.config.set("pages.format", self.cmb_format.currentText())
        self.config.set("pages.dpi", self.spin_dpi.value())

        use_project = self.chk_use_project.isChecked() and self.project is not None
        project = self.project if use_project else None
        target_dir = None
        if project is None:
            target_dir = QtWidgets.QFileDialog.getExistingDirectory(
                self.widget(), "Pasta de destino das páginas"
            )
            if not target_dir:
                return

        QtWidgets.QApplication.setOverrideCursor(WAIT_CURSOR)
        try:
            created = generator.generate(
                script,
                target_dir=target_dir,
                project=project,
                format_override=self.cmb_format.currentText(),
                dpi_override=self.spin_dpi.value(),
            )
        except roteiro.RoteiroError as error:
            helpers.show_message(str(error))
            return
        except (RuntimeError, OSError) as error:
            helpers.show_message("Falha ao gerar: {0}".format(error))
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        if project is not None:
            self.refresh()
        helpers.show_message("{0} página(s) gerada(s).".format(len(created)))
