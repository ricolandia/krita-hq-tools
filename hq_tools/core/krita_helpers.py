"""Funções utilitárias sobre a API do Krita usadas por todos os módulos."""

from krita import InfoObject, Krita, Selection

from .compat import QIcon


def app():
    return Krita.instance()


def active_document():
    return app().activeDocument()


def active_view():
    window = app().activeWindow()
    return window.activeView() if window is not None else None


def show_message(text, timeout=4000):
    """Mostra uma mensagem flutuante no canvas, se houver uma janela ativa."""
    view = active_view()
    if view is not None:
        try:
            view.showFloatingMessage(text, QIcon(), timeout, 0)
        except (TypeError, RuntimeError):
            pass


def find_filter(*names):
    """Procura um filtro instalado pelo id, tolerando variações de nome."""
    wanted = {name.lower() for name in names}
    for name in app().filters():
        if name.lower() in wanted:
            return app().filter(name)
    return None


def has_selection(document):
    return document.selection() is not None


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
    existing = {node.name() for node in document.rootNode().findChildNodes()}
    existing.update(
        node.name()
        for node in document.rootNode().findChildNodes(recursive=True)
    )
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
