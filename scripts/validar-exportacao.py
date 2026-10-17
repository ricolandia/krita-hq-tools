"""Validação interativa da exportação — rodar no Krita real (Scripter).

O harness headless não consegue validar o ``Document.exportImage`` (derruba o
Krita; ver ``scripts/poc-exportacao.py``). Este script é o par interativo:
prova, no **seu** Krita, os caminhos que o diálogo de exportação vai usar.

Como rodar (2 minutos):
1. No Krita: Ferramentas > Scripts > Scripter (Tools > Scripts > Scripter).
2. Abra este arquivo no Scripter (botão de abrir) e clique em Run (rodar).
3. No fim aparece um resumo; o mesmo texto fica em
   ``/tmp/validar-exportacao.log``.

Ele cria uma A4 300 dpi de teste em ``/tmp/validar-exportacao/`` e tenta:
PNG nativo, PNG reamostrado (96 dpi), JPG, TIFF CMYK (lista os perfis
disponíveis) e PDF de uma página — medindo o tempo e conferindo a saída.
"""

import os
import shutil
import time
import zipfile

BASE = "/tmp/validar-exportacao"
LOG = "/tmp/validar-exportacao.log"
linhas = []


def registrar(texto):
    linhas.append(str(texto))


def _tempo(rotulo, funcao):
    t0 = time.perf_counter()
    try:
        resultado = funcao()
        registrar(
            "%-22s %6.0f ms  %s"
            % (rotulo, (time.perf_counter() - t0) * 1000, resultado)
        )
    except Exception as erro:
        registrar("%-22s FALHOU: %s: %s" % (rotulo, type(erro).__name__, erro))


def _dimensoes(caminho):
    from PyQt5.QtGui import QImage

    imagem = QImage(caminho)
    if imagem.isNull():
        return "ilegivel (%d KB)" % (os.path.getsize(caminho) // 1024)
    return "%dx%d dpi=(%d,%d) %d KB" % (
        imagem.width(),
        imagem.height(),
        round(imagem.dotsPerMeterX() * 0.0254),
        round(imagem.dotsPerMeterY() * 0.0254),
        os.path.getsize(caminho) // 1024,
    )


def executar():
    from krita import InfoObject, Krita
    from PyQt5.QtWidgets import QMessageBox

    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE, exist_ok=True)
    aplicacao = Krita.instance()
    registrar("Krita %s" % aplicacao.version())

    doc = aplicacao.createDocument(
        2480, 3508, "validar_export", "RGBA", "U8", "sRGB built-in", 300.0
    )
    if doc is None:
        registrar("ERRO: não consegui criar o documento de teste.")
        return _fechar(QMessageBox)
    aplicacao.setActiveDocument(doc)
    aplicacao.activeWindow().addView(doc)
    info = InfoObject()
    info.setProperty("color", "#3366aa")
    fundo = doc.createFillLayer("fundo", "color", info, None)
    if fundo is not None:
        doc.rootNode().addChildNode(fundo, None)
    kra = os.path.join(BASE, "validar_export.kra")
    doc.saveAs(kra)
    doc.setModified(False)
    registrar("kra de teste: %s" % os.path.exists(kra))

    registrar("perfis CMYK U8: %r" % aplicacao.profiles("CMYK", "U8")[:4])

    # 1) PNG nativo (o caminho que o harness não consegue provar).
    png = os.path.join(BASE, "pagina_300.png")
    _tempo("png nativo", lambda: (doc.exportImage(png, info), _dimensoes(png))[1])

    # 2) Reamostragem numa cópia (96 dpi).
    def _96():
        copia = aplicacao.openDocument(kra)
        copia.scaleImage(794, 1123, 96, 96, "Bicubic")
        saida = os.path.join(BASE, "pagina_96.png")
        copia.exportImage(saida, info)
        copia.setModified(False)
        copia.close()
        return _dimensoes(saida)

    _tempo("png 96 dpi", _96)

    # 3) JPG (qualidade 90).
    def _jpg():
        info_jpg = InfoObject()
        info_jpg.setProperty("quality", 90)
        saida = os.path.join(BASE, "pagina.jpg")
        doc.exportImage(saida, info_jpg)
        return _dimensoes(saida)

    _tempo("jpg q90", _jpg)

    # 4) CMYK: perfis + conversão numa cópia + TIFF.
    def _cmyk():
        perfis = aplicacao.profiles("CMYK", "U8")
        if not perfis:
            return "sem perfis CMYK instalados"
        copia = aplicacao.openDocument(kra)
        copia.setColorSpace("CMYK", "U8", perfis[0])
        saida = os.path.join(BASE, "pagina_cmyk.tiff")
        copia.exportImage(saida, info)
        copia.setModified(False)
        copia.close()
        return "%s | %s" % (
            "modo %s/%s" % (copia.colorModel(), copia.colorDepth()),
            _dimensoes(saida),
        )

    _tempo("tiff cmyk", _cmyk)

    # 5) PDF de uma página.
    def _pdf():
        saida = os.path.join(BASE, "pagina.pdf")
        doc.exportImage(saida, info)
        with open(saida, "rb") as arquivo:
            cabecalho = arquivo.read(4)
        return "header=%r %d KB" % (cabecalho, os.path.getsize(saida) // 1024)

    _tempo("pdf 1 pagina", _pdf)

    # 6) Atalho web (mergedimage do .kra) — o caminho rápido do preset Web.
    def _merged():
        with zipfile.ZipFile(kra) as z:
            dados = z.read("mergedimage.png")
        saida = os.path.join(BASE, "pagina_merged.png")
        with open(saida, "wb") as arquivo:
            arquivo.write(dados)
        return _dimensoes(saida)

    _tempo("mergedimage (atalho)", _merged)

    doc.setModified(False)
    doc.close()
    registrar("arquivos: %r" % sorted(os.listdir(BASE)))
    _fechar(QMessageBox)


def _fechar(QMessageBox):
    texto = "\n".join(linhas)
    with open(LOG, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto + "\n")
    caixa = QMessageBox()
    caixa.setWindowTitle("HQ Tools - validação da exportação")
    caixa.setText("Resultado (também em %s):" % LOG)
    caixa.setDetailedText(texto)
    caixa.setInformativeText(
        "Copie o texto (botão 'Show Details'/'Mostrar detalhes') e cole na conversa."
    )
    caixa.exec_()


executar()
