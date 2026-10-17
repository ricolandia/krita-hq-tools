"""PoC da exportação de páginas — parte headless-safe + achados (17/10/2026).

Roda com ``scripts/harness-krita.sh scripts/poc-exportacao.py``. Mede e
registra em ``HQ_HARNESS_LOG`` o que o harness **consegue** validar:

- criar uma A4 300 dpi e salvar o .kra (custo real por página);
- ``scaleImage`` numa cópia reaberta (caminho da resolução);
- o atalho web ``mergedimage.png`` do .kra (sem exportImage);
- perfis CMYK disponíveis no ambiente.

Achados medidos (Krita 5.3.4, harness):

- ``mergedimage.png``: **57 ms**, 2480x3508 com dpi=(300,300) — a exportação
  web rápida não precisa abrir o documento;
- criar + salvar a A4: ~2,5 s; ``scaleImage`` da cópia: ~0,9 s;
- ``Document.exportImage`` **derruba o Krita no harness** (crash nativo, sem
  traceback) em PNG/JPG/TIFF, com/sem view, com/sem atraso, com config
  explícito e com ``waitForDone``/``refreshProjection`` antes: os caminhos
  com exportImage (resoluções, CMYK, PDF) **validam-se no Krita real**, não
  aqui;
- o ambiente do harness não lista perfis CMYK (``profiles("CMYK","U8")``
  vazio): validar a conversão também no Krita real;
- ``present_document`` usava ``Krita.addView``, que **não existe** no Krita
  5.3.4 (falhava em silêncio): corrigido para ``Window.addView`` no mesmo dia.
"""

import os
import shutil
import time
import zipfile

LOG = os.environ.get("HQ_HARNESS_LOG", "/tmp/opencode/poc-exportacao.log")
BASE = "/tmp/opencode/poc-exportacao"


def log(mensagem):
    with open(LOG, "a", encoding="utf-8") as arquivo:
        arquivo.write(str(mensagem) + "\n")


def _tempo(rotulo, funcao):
    t0 = time.perf_counter()
    try:
        resultado = funcao()
        log(
            "%-26s %6.0f ms  %s"
            % (rotulo, (time.perf_counter() - t0) * 1000, resultado)
        )
    except Exception as erro:
        log("%-26s FALHOU: %s: %s" % (rotulo, type(erro).__name__, erro))


def _dimensoes(caminho):
    # Dentro do Krita não há PIL: o inspetor é o Qt (QImage).
    try:
        from PyQt5.QtGui import QImage
    except ImportError:
        from PyQt6.QtGui import QImage

    imagem = QImage(caminho)
    if imagem.isNull():
        return "ilegivel (%d KB)" % (os.path.getsize(caminho) // 1024)
    return "%dx%d dpi=%s" % (
        imagem.width(),
        imagem.height(),
        (
            round(imagem.dotsPerMeterX() * 0.0254),
            round(imagem.dotsPerMeterY() * 0.0254),
        ),
    )


def executar():
    from krita import Krita

    from hq_tools.core import krita_helpers as helpers

    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE, exist_ok=True)
    aplicacao = Krita.instance()

    def _criar():
        doc = aplicacao.createDocument(
            2480, 3508, "poc_a4", "RGBA", "U8", "sRGB built-in", 300.0
        )
        aplicacao.setActiveDocument(doc)
        aplicacao.activeWindow().addView(doc)
        fundo = doc.createFillLayer(
            "fundo",
            "color",
            helpers.make_info_object({"color": "#ffffff"}),
            helpers.full_selection(doc),
        )
        doc.rootNode().addChildNode(fundo, None)
        doc.saveAs(os.path.join(BASE, "poc_a4.kra"))
        doc.setModified(False)
        return "kra ok (%d KB)" % (
            os.path.getsize(os.path.join(BASE, "poc_a4.kra")) // 1024
        )

    _tempo("criar A4 300dpi + salvar", _criar)

    def _escala():
        copia = aplicacao.openDocument(os.path.join(BASE, "poc_a4.kra"))
        copia.scaleImage(595, 842, 72, 72, "Bicubic")
        copia.saveAs(os.path.join(BASE, "poc_a4_72.kra"))
        copia.setModified(False)
        copia.close()
        return "72 dpi (595x842)"

    _tempo("scaleImage na copia", _escala)

    def _cmyk():
        perfis = aplicacao.profiles("CMYK", "U8")
        log("perfis CMYK disponiveis: %r" % perfis[:4])
        if not perfis:
            return "sem perfil CMYK no ambiente (validar no Krita real)"
        copia = aplicacao.openDocument(os.path.join(BASE, "poc_a4.kra"))
        copia.setColorSpace("CMYK", "U8", perfis[0])
        resultado = "modo agora: %s / %s" % (copia.colorModel(), copia.colorDepth())
        copia.close()
        return resultado

    _tempo("setColorSpace CMYK", _cmyk)

    def _merged():
        with zipfile.ZipFile(os.path.join(BASE, "poc_a4.kra")) as z:
            dados = z.read("mergedimage.png")
        saida = os.path.join(BASE, "pagina_merged.png")
        with open(saida, "wb") as arquivo:
            arquivo.write(dados)
        return _dimensoes(saida)

    _tempo("mergedimage do kra", _merged)
    log("arquivos: %r" % sorted(os.listdir(BASE)))


executar()
