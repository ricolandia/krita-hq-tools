"""PoC do moodboard: posicionar e escalar uma camada de arquivo (linkada).

Valida, dentro do Krita, as vias para o quadro de referências:

  A) ``Node.move()`` numa camada de arquivo (posicionar sem máscara);
  B1) máscara de transformação com escala em ``scaleX``/``scaleY`` e
      translação em ``transformedCenter``;
  B2) máscara de transformação com a matriz completa em
      ``flattenedPerspectiveTransform``.

Roda no Krita 5.x e 6.x. No Scripter, cole e execute; por autostart, defina
``HQ_POC_SCRIPT`` com o caminho deste arquivo.

Saídas: ``/tmp/poc-moodboard.log``, ``/tmp/poc-moodboard-*.png`` e
``/tmp/poc-moodboard.kra``. O quadro esperado (em todos os testes): a imagem de
400x300 (vermelho/verde/azul/amarelo) com escala 0,5 no ponto (300, 200).
"""

import os

try:
    from PyQt5 import QtCore, QtGui
except ImportError:  # Krita 6
    from PyQt6 import QtCore, QtGui

from krita import Krita

LOG_PATH = "/tmp/poc-moodboard.log"
JPG_PATH = "/tmp/poc-moodboard-ref.jpg"

ESCALA = 0.5
DESTINO_X = 300
DESTINO_Y = 200


def log(mensagem):
    linha = str(mensagem)
    print(linha)
    with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def _jpg_de_teste(caminho):
    """JPG 400x300 com quatro quadrantes de cores distintas."""
    imagem = QtGui.QImage(400, 300, QtGui.QImage.Format_RGB32)
    imagem.fill(QtGui.QColor(32, 32, 32))
    pintor = QtGui.QPainter(imagem)
    pintor.fillRect(0, 0, 200, 150, QtGui.QColor(220, 40, 40))
    pintor.fillRect(200, 0, 200, 150, QtGui.QColor(40, 180, 60))
    pintor.fillRect(0, 150, 200, 150, QtGui.QColor(40, 80, 220))
    pintor.fillRect(200, 150, 200, 150, QtGui.QColor(230, 200, 40))
    pintor.end()
    return imagem.save(caminho, "JPG", 92)


def _xml_escala_centros(escala, dx, dy):
    """Variante B1: escala em scaleX/scaleY, translação no centro transformado."""
    return (
        '<transform_params>'
        '<main id="tooltransformparams"/>'
        '<data mode="0"><free_transform>'
        '<transformedCenter type="pointf" x="{dx}" y="{dy}"/>'
        '<originalCenter type="pointf" x="0" y="0"/>'
        '<rotationCenterOffset type="pointf" x="0" y="0"/>'
        '<transformAroundRotationCenter value="0" type="value"/>'
        '<aX value="0" type="value"/><aY value="0" type="value"/><aZ value="0" type="value"/>'
        '<cameraPos z="1024" type="vector3d" x="0" y="0"/>'
        '<scaleX value="{escala}" type="value"/><scaleY value="{escala}" type="value"/>'
        '<shearX value="0" type="value"/><shearY value="0" type="value"/>'
        '<keepAspectRatio value="0" type="value"/>'
        '<flattenedPerspectiveTransform m11="1" m12="0" m13="0" m21="0" m22="1" '
        'm23="0" m31="0" m32="0" m33="1" type="transform"/>'
        '<filterId value="Bicubic" type="value"/>'
        '</free_transform></data></transform_params>'
    ).format(escala=escala, dx=dx, dy=dy)


def _xml_matriz(escala, dx, dy):
    """Variante B2: matriz completa (QTransform: m31/m32 = deslocamento)."""
    return (
        '<transform_params>'
        '<main id="tooltransformparams"/>'
        '<data mode="0"><free_transform>'
        '<transformedCenter type="pointf" x="0" y="0"/>'
        '<originalCenter type="pointf" x="0" y="0"/>'
        '<rotationCenterOffset type="pointf" x="0" y="0"/>'
        '<transformAroundRotationCenter value="0" type="value"/>'
        '<aX value="0" type="value"/><aY value="0" type="value"/><aZ value="0" type="value"/>'
        '<cameraPos z="1024" type="vector3d" x="0" y="0"/>'
        '<scaleX value="1" type="value"/><scaleY value="1" type="value"/>'
        '<shearX value="0" type="value"/><shearY value="0" type="value"/>'
        '<keepAspectRatio value="0" type="value"/>'
        '<flattenedPerspectiveTransform m11="{escala}" m12="0" m13="0" m21="0" '
        'm22="{escala}" m23="0" m31="{dx}" m32="{dy}" m33="1" type="transform"/>'
        '<filterId value="Bicubic" type="value"/>'
        '</free_transform></data></transform_params>'
    ).format(escala=escala, dx=dx, dy=dy)


def _exportar(documento, caminho):
    """Salva a projeção do documento; pixelData (BGRA) como reserva."""
    imagem = documento.projection(0, 0, 0, 0)
    if imagem is not None and not imagem.isNull():
        return bool(imagem.save(caminho))
    largura, altura = documento.width(), documento.height()
    dados = documento.pixelData(0, 0, largura, altura)
    if dados is None:
        return False
    reserva = QtGui.QImage(bytes(dados), largura, altura, QtGui.QImage.Format_ARGB32)
    return bool(reserva.save(caminho))


def _testar_mascara(documento, raiz, rotulo, xml, png):
    camada = documento.createFileLayer(rotulo, JPG_PATH, "None", "Bilinear")
    if camada is None:
        log("{0}) createFileLayer falhou".format(rotulo))
        return
    raiz.addChildNode(camada, None)
    mascara = documento.createTransformMask(rotulo + "-mask")
    if mascara is None:
        log("{0}) createTransformMask falhou".format(rotulo))
        camada.remove()
        return
    camada.addChildNode(mascara, None)
    ok = mascara.fromXML(xml)
    log("{0}) fromXML={1}".format(rotulo, ok))
    documento.refreshProjection()
    try:
        afin = mascara.finalAffineTransform()
        esperado = (
            abs(afin.m11() - ESCALA) < 1e-6
            and abs(afin.m22() - ESCALA) < 1e-6
            and abs(afin.dx() - DESTINO_X) < 0.01
            and abs(afin.dy() - DESTINO_Y) < 0.01
        )
        log(
            "{0}) finalAffineTransform m11={1} m22={2} dx={3} dy={4} -> esperado={5}".format(
                rotulo, afin.m11(), afin.m22(), afin.dx(), afin.dy(), esperado
            )
        )
    except Exception as erro:
        log("{0}) erro em finalAffineTransform: {1}".format(rotulo, erro))
    log("{0}) exportacao={1}".format(rotulo, _exportar(documento, png)))
    log("{0}) toXML depois: {1}".format(rotulo, mascara.toXML()))
    camada.remove()


def executar_poc():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    aplicacao = Krita.instance()
    log("Krita {0}".format(aplicacao.version()))
    log("JPG de teste: {0}".format(_jpg_de_teste(JPG_PATH)))

    documento = aplicacao.createDocument(
        1600, 1000, "poc-moodboard", "RGBA", "U8", "", 72.0
    )
    if documento is None:
        log("createDocument falhou")
        return None
    janela = aplicacao.activeWindow()
    if janela is not None:
        janela.addView(documento)
    raiz = documento.rootNode()

    camada = documento.createFileLayer("A-move", JPG_PATH, "None", "Bilinear")
    raiz.addChildNode(camada, None)
    antes = camada.position()
    camada.move(120, 80)
    documento.refreshProjection()
    depois = camada.position()
    log(
        "A) position antes=({0}, {1}) depois=({2}, {3})".format(
            antes.x(), antes.y(), depois.x(), depois.y()
        )
    )
    log("A) exportacao={0}".format(_exportar(documento, "/tmp/poc-moodboard-a-move.png")))
    camada.remove()

    _testar_mascara(
        documento, raiz, "B1", _xml_escala_centros(ESCALA, DESTINO_X, DESTINO_Y),
        "/tmp/poc-moodboard-b1-centros.png",
    )
    _testar_mascara(
        documento, raiz, "B2", _xml_matriz(ESCALA, DESTINO_X, DESTINO_Y),
        "/tmp/poc-moodboard-b2-matriz.png",
    )

    documento.saveAs("/tmp/poc-moodboard.kra")
    log("kra salvo em /tmp/poc-moodboard.kra")
    return documento


if __name__ == "__main__" or os.environ.get("HQ_POC_AUTORUN"):
    executar_poc()
