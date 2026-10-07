"""Funções utilitárias sobre a API do Krita usadas por todos os módulos."""

import contextlib

from krita import InfoObject, Krita, Selection

from . import mapeamento
from .camadas import ordem_com_no_abaixo
from .compat import WAIT_CURSOR, QIcon, QtCore, QtGui, QtWidgets
from .erros import escrever_erro


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
    escrever_erro("[hq_tools] {0}\n".format(text), flush=True)


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


@contextlib.contextmanager
def cursor_espera(ativo=True):
    """Cursor de espera durante uma operação lenta, sempre restaurado.

    Gerar as páginas de um roteiro inteiro, instalar as fontes do kit ou
    aplicar retícula em um documento grande leva segundos rodando na thread da
    interface: sem o cursor, o Krita parece travado e o autor clica de novo,
    o que duplica o trabalho. O ``finally`` é obrigatório: cursor de espera
    esquecido deixa o Krita inteiro travado até reiniciar.
    """
    if not ativo:
        yield
        return
    try:
        QtWidgets.QApplication.setOverrideCursor(QtCore.QCursor(WAIT_CURSOR))
    except (AttributeError, RuntimeError, TypeError):
        # Sem QApplication (testes, script avulso), segue sem cursor.
        yield
        return
    try:
        yield
    finally:
        try:
            QtWidgets.QApplication.restoreOverrideCursor()
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
    nada selecionado. O libkis **não tem** ``byteCount()`` (a versão anterior
    usava esse nome, caía no ``except`` e considerava toda seleção vazia);
    ``width()``/``height()`` devolvem o retângulo exato da seleção, 0 quando
    não há área.
    """
    if selection is None:
        return True
    try:
        return selection.width() <= 0 or selection.height() <= 0
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


def selection_bounds(document):
    """Retângulo (x, y, w, h) da seleção ativa em pixels, ou None.

    É a base da inserção do visualizador 3D: a seleção já vem em pixels da
    imagem, sem conversão de tela (zoom, rolagem, rotação).
    """
    selection = active_selection(document)
    if selection is None:
        return None
    try:
        return (selection.x(), selection.y(), selection.width(), selection.height())
    except (AttributeError, RuntimeError):
        return None


def deselect(document=None):
    """Desfaz a seleção ativa (ação do Krita, com fallback silencioso)."""
    try:
        acao = app().action("deselect")
        if acao is not None:
            acao.trigger()
            return
    except (AttributeError, RuntimeError):
        pass
    if document is None:
        document = active_document()
    if document is not None:
        try:
            document.setSelection(Selection())
        except (AttributeError, RuntimeError):
            pass


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


def attach_below_active(document, node, parent=None):
    """Insere o nó logo abaixo do nó ativo, no mesmo grupo.

    Feedback do usuário: a referência 3D entra abaixo do esboço, para poder
    traçar por cima. Se o nó ativo for um grupo, mantém o comportamento
    normal (entra no grupo). O Krita não tem "inserir abaixo": o nó entra no
    topo e a lista é reordenada com ``setChildNodes`` (ordem base -> topo,
    confirmada em ``libs/libkis/Node.cpp``).
    """
    ativo = document.activeNode()
    if ativo is None or ativo.type() == "grouplayer":
        return attach(document, node, parent=parent)
    if parent is None:
        parent = ativo.parentNode() or document.rootNode()

    def chave(item):
        try:
            return str(item.uniqueId())
        except (AttributeError, RuntimeError):
            return str(id(item))

    parent.addChildNode(node, None)
    ordem = ordem_com_no_abaixo(parent.childNodes(), ativo, node, chave=chave)
    if ordem is not None:
        try:
            parent.setChildNodes(ordem)
        except (AttributeError, RuntimeError):
            pass
    document.refreshProjection()
    return node


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


def viewport_da_view(view):
    """Viewport do canvas da view ativa (para ancorar o flutuante), ou None.

    O casamento da sub-janela com a view é por índice, como no visualizador
    3D (o mesmo ponto a validar com dois documentos abertos, apontado na
    auditoria de 05/10).
    """
    try:
        janela = view.window()
        q_janela = janela.qwindow()
    except (AttributeError, RuntimeError):
        return None
    central = q_janela.centralWidget() if q_janela is not None else None
    area_mdi = central.findChild(QtWidgets.QMdiArea) if central is not None else None
    if area_mdi is None:
        return None
    subjanelas = area_mdi.subWindowList()
    views = list(janela.views())
    for indice, sub in enumerate(subjanelas):
        if indice < len(views) and views[indice] == view:
            area = sub.widget().findChild(QtWidgets.QAbstractScrollArea)
            return area.viewport() if area is not None else None
    if subjanelas:
        area = subjanelas[0].widget().findChild(QtWidgets.QAbstractScrollArea)
        return area.viewport() if area is not None else None
    return None


def pan_do_viewport(viewport):
    """Deslocamento (px do widget) das barras de rolagem, relativo ao centro."""
    area = viewport.parentWidget()
    if area is None:
        return (0.0, 0.0)
    try:
        horizontal = area.horizontalScrollBar()
        vertical = area.verticalScrollBar()
    except (AttributeError, RuntimeError):
        return (0.0, 0.0)
    return (
        mapeamento.deslocamento_da_barra(
            horizontal.minimum(), horizontal.maximum(), horizontal.value()
        ),
        mapeamento.deslocamento_da_barra(
            vertical.minimum(), vertical.maximum(), vertical.value()
        ),
    )


def parametros_do_canvas(documento, viewport):
    """(centro_widget, centro_imagem, zoom, rotacao, pan, espelhado) ou None.

    Em modo pixel (o padrão do Krita), a escala de tela é ``zoomLevel``: em
    100%, um pixel da imagem vira um pixel do widget. É a mesma conta do
    visualizador 3D, usada aqui para ancorar o flutuante sobre a seleção.
    """
    view = active_view()
    canvas = view.canvas() if view is not None else None
    if canvas is None:
        return None
    try:
        zoom = canvas.zoomLevel()
    except (AttributeError, RuntimeError):
        return None
    if zoom <= 0:
        return None
    try:
        rotacao = canvas.rotation()
    except (AttributeError, RuntimeError):
        rotacao = 0.0
    try:
        espelhado = canvas.mirror()
    except (AttributeError, RuntimeError):
        espelhado = False
    centro_imagem = (documento.width() / 2.0, documento.height() / 2.0)
    pan = pan_do_viewport(viewport)
    centro_widget = (viewport.width() / 2.0, viewport.height() / 2.0)
    return centro_widget, centro_imagem, zoom, rotacao, pan, espelhado


def centro_da_vista(documento):
    """Ponto (x, y) da imagem no centro da vista atual, ou None.

    É o "onde você está olhando": a inserção de balões, onomatopeias e
    recursos usa este ponto (em vez do canto do documento) quando não há
    seleção, para a arte nascer no meio da tela mesmo com zoom.
    """
    if documento is None:
        return None
    view = active_view()
    if view is None:
        return None
    viewport = viewport_da_view(view)
    if viewport is None:
        return None
    parametros = parametros_do_canvas(documento, viewport)
    if parametros is None:
        return None
    return mapeamento.centro_da_vista(*parametros)


def destino_de_insercao(documento, largura, altura):
    """(x, y, escala) de onde inserir uma arte de ``largura`` x ``altura``.

    Com seleção, cabe nela reduzindo (nunca amplia) e fica centralizada;
    sem seleção, mantém o tamanho natural e vai para o centro da vista.
    """
    caixa = selection_bounds(documento)
    if caixa is not None:
        return mapeamento.encaixe_central(caixa, largura, altura)
    centro = centro_da_vista(documento)
    if centro is None:
        return (0.0, 0.0, 1.0)
    return (centro[0] - largura / 2.0, centro[1] - altura / 2.0, 1.0)


def posicionar_vetor(documento, camada):
    """Posiciona a camada vetorial (seleção ou centro da vista).

    Devolve True quando conseguiu posicionar; sem seleção e sem vista (ou
    com um documento sem conteúdo), devolve False e a arte fica onde o SVG
    a colocou (como antes).
    """
    try:
        limites = camada.bounds()
    except (AttributeError, RuntimeError):
        return False
    if limites is None or limites.isEmpty():
        return False
    destino_x, destino_y, escala = destino_de_insercao(
        documento, limites.width(), limites.height()
    )
    return _transformar_vetor(camada, limites, escala, destino_x, destino_y)


def _transformar_vetor(camada, limites, escala, destino_x, destino_y):
    """Aplica escala e translação nos shapes do topo da camada vetorial.

    A matriz global entra DEPOIS da transformação de cada shape
    (``atual * global``: no Qt, ``X * Y`` aplica X primeiro), então a arte
    inteira (inclusive grupos do SVG) anda e escala junto.
    """
    try:
        shapes = camada.shapes()
    except (AttributeError, RuntimeError):
        return False
    if not shapes:
        return False
    global_transform = QtGui.QTransform()
    global_transform.translate(destino_x, destino_y)
    global_transform.scale(escala, escala)
    global_transform.translate(-limites.x(), -limites.y())
    for shape in shapes:
        try:
            antigo = shape.boundingBox()
            atual = shape.transformation()
            shape.setTransformation(atual * global_transform)
        except (AttributeError, RuntimeError, TypeError):
            return False
        try:
            # Ao mover/escalar, o Krita precisa repintar a UNIÃO da área
            # antiga com a nova; sem isso a arte fica "fantasma" na posição
            # original (visto no smoke de 07/10).
            shape.updateAbsolute(antigo.united(shape.boundingBox()))
        except (AttributeError, RuntimeError, TypeError):
            try:
                shape.update()
            except (AttributeError, RuntimeError):
                pass
    return True
