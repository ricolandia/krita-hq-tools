"""Funções utilitárias sobre a API do Krita usadas por todos os módulos."""

import sys

from krita import InfoObject, Krita, Selection

from .compat import QIcon


def app():
    return Krita.instance()


def active_document():
    return app().activeDocument()


def active_view():
    window = app().activeWindow()
    return window.activeView() if window is not None else None


def read_text_file(path, encodings=("utf-8-sig", "cp1252", "latin-1")):
    """Lê um arquivo de texto tentando as codificações usuais.

    SVG exportado pelo Inkscape ou por um editor no Windows em português
    costuma vir em Windows-1252, e ``open(..., encoding="utf-8")`` levantava
    ``UnicodeDecodeError``: a exceção não é ``OSError``, então escapava do
    ``except`` do docker e aparecia como erro do Python no meio da interface.
    """
    with open(path, "rb") as handle:
        bruto = handle.read()
    for encoding in encodings:
        try:
            return bruto.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return bruto.decode("utf-8", errors="replace")


def log(text):
    """Escreve no log do Krita (stderr capturado pelo plugin loader).

    Usado em pontos onde antes o erro era engolido em silêncio, para o autor
    conseguir diagnosticar sem o plugin travar.
    """
    try:
        sys.stderr.write("[hq_tools] {0}\n".format(text))
        sys.stderr.flush()
    except (AttributeError, ValueError, OSError):
        pass


def show_message(text, timeout=4000):
    """Mostra uma mensagem flutuante no canvas, se houver uma janela ativa.

    Sem view ativa o texto vai só para o log: abrir uma caixa de diálogo aqui
    transformaria avisos rotineiros (slot vazio, recurso ausente) em modais
    repetidos, que era o comportamento de ``show_info``.
    """
    view = active_view()
    if view is not None:
        try:
            view.showFloatingMessage(text, QIcon(), timeout, 0)
        except (TypeError, RuntimeError):
            log("showFloatingMessage falhou: {0}".format(text))
            return
    log(text)


def present_document(document):
    """Abre uma aba para o documento e o torna ativo.

    Sem ``addView`` o documento fica sem janela: o usuário não vê o que foi
    criado e os comandos que dependem de view (``activateResource``, seleção,
    atalhos de pincel) passam a não ter efeito.
    """
    if document is None:
        return False
    try:
        app().addView(document)
        app().setActiveDocument(document)
    except (AttributeError, RuntimeError):
        return False
    return True


def close_document(document, modified=False):
    """Fecha um documento descartando alterações pendentes.

    Devolve ``True`` quando o documento foi realmente fechado. Sem isso, um
    documento aberto só para adaptar um modelo fica como aba órfã e o Krita
    pergunta ao usuário se quer salvar na saída.
    """
    if document is None:
        return True
    try:
        if not modified:
            document.setModified(False)
        document.close()
    except (AttributeError, RuntimeError):
        return False
    return True


def run_in_macro(document, action):
    """Executa ``action()`` dentro de uma macro do Krita (desfazer por Ctrl+Z).

    O ``endMacro`` sempre roda, mesmo se a ação levantar, para não deixar a
    macro aberta no histórico.
    """
    if document is None:
        return action()
    try:
        document.beginMacro(action.__name__ if hasattr(action, "__name__") else "HQ Tools")
    except (AttributeError, RuntimeError):
        return action()
    try:
        return action()
    finally:
        try:
            document.endMacro()
        except (AttributeError, RuntimeError):
            pass


def modal_parent():
    """Widget pai para janelas modais (QMainWindow do Krita), ou None."""
    window = app().activeWindow()
    if window is not None:
        try:
            return window.qwindow()
        except (AttributeError, RuntimeError):
            pass
    return None


def show_info(title, text):
    """Aviso modal para fluxos e decisões importantes."""
    from .compat import QtWidgets

    QtWidgets.QMessageBox.information(modal_parent(), title, text)


def find_filter(*names):
    """Procura um filtro instalado pelo id, tolerando variações de nome."""
    wanted = {name.lower() for name in names}
    for name in app().filters():
        if name.lower() in wanted:
            return app().filter(name)
    return None


def selection_vazia(selection):
    """Diz se a seleção não tem pixels (ou não existe).

    No Krita ``document.selection()`` devolve um objeto de seleção mesmo sem
    nada selecionado. Só ``byteCount()`` diz se há área de verdade: testar
    ``is not None`` fazia o plugin criar máscara de 0 px, e o filtro passava a
    não fazer nada sem explicar por quê.
    """
    if selection is None:
        return True
    try:
        return selection.byteCount() == 0
    except (AttributeError, RuntimeError, TypeError):
        return True


def has_selection(document):
    return not selection_vazia(document.selection())


def active_selection(document):
    """Seleção ativa com pixels, ou None."""
    selection = document.selection()
    if selection_vazia(selection):
        return None
    return selection


def full_selection(document):
    """Cria uma seleção que cobre todo o documento."""
    selection = Selection()
    selection.select(0, 0, document.width(), document.height(), 255)
    return selection


def selection_for_apply(document, use_active_selection=True):
    """Devolve a seleção ativa quando pedida, ou uma seleção total."""
    if use_active_selection:
        selection = document.selection()
        if selection is not None:
            return selection
    return full_selection(document)


def target_container(document):
    """Resolve onde inserir uma camada nova a partir do nó ativo.

    Devolve ``(pai, acima_de)``. Se o nó ativo for um grupo, a camada entra
    dentro dele; caso contrário, entra logo acima do nó ativo, no mesmo grupo.
    """
    node = document.activeNode()
    root = document.rootNode()
    if node is None:
        return root, None
    if node.type() == "grouplayer":
        return node, None
    parent = node.parentNode()
    return (parent or root), node


def attach(document, node, parent=None, above=None):
    """Insere (ou move) um nó no documento e atualiza a projeção."""
    if parent is None:
        parent, above = target_container(document)
    result = parent.addChildNode(node, above)
    document.refreshProjection()
    return result


def make_info_object(properties):
    info = InfoObject()
    info.setProperties(dict(properties))
    return info


def unique_layer_name(document, base_name):
    """Gera um nome de camada livre, com sufixo numérico se preciso."""
    existing = {
        node.name() for node in document.rootNode().findChildNodes(recursive=True)
    }
    if base_name not in existing:
        return base_name
    index = 2
    while "{0} {1}".format(base_name, index) in existing:
        index += 1
    return "{0} {1}".format(base_name, index)


def document_dpi(document):
    try:
        return float(document.xRes())
    except (AttributeError, TypeError, ValueError):
        return 300.0
