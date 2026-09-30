"""Auditoria dos packs de pincéis: referência de recurso que não vem junto.

Um preset (.kpp) é um PNG com o XML dentro de um chunk de texto. O XML cita
o recurso de que precisa (``filename=`` no ``brush_definition`` e
``requiredBrushFile``). Se o arquivo citado não estiver no pack, o preset
instala e o pincel não aparece.

Este teste trava o estado atual: nenhum preset do kit cita uma textura que não
venha no pack. Em 2026-09-30 foram medidos 3 casos assim, e os 3 presets foram
removidos do kit porque os autores dos packs nunca distribuíram as texturas
citadas, em nenhuma versão dos repositórios. Eles estão registrados em
PRESETS_REMOVIDOS, que serve de documentação do motivo.
"""

import importlib.util
import os
import pathlib
import struct
import tempfile
import unittest
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "auditar-packs.py"


def carregar_auditor():
    spec = importlib.util.spec_from_file_location("auditar_packs", str(SCRIPT))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


aud = carregar_auditor()

# Os 3 presets que citavam uma textura inexistente foram removidos do kit em
# 2026-09-30. Não dá para "consertar" gerando arquivo (é arte de terceiro), e
# os repositórios de origem não têm a textura em nenhuma versão. Ficam aqui para
# documentar o motivo da remoção, não como lista de exceções: o teste exige
# zero referências órfãs.
PRESETS_REMOVIDOS = {
    "deevad_bristle.png": "deevad 2d expressive thin.kpp",
    "flat-tip-dirty.gbr": "deevad 6n stamp floor particles.kpp",
    "T_Texture_7.gih": "X9AI_WC_Scattered_Sharp.kpp",
}


def kpp(xml, comprimido=False):
    """PNG sintético com o XML do preset em tEXt (ou zTXt, como o Krita grava)."""

    def chunk(tipo, payload):
        parte = struct.pack(">I", len(payload)) + tipo + payload
        return parte + struct.pack(">I", zlib.crc32(tipo + payload) & 0xFFFFFFFF)

    dados = bytearray(b"\x89PNG\r\n\x1a\n")
    bruto = xml.encode("utf-8")
    if comprimido:
        dados += chunk(b"zTXt", b"preset\0\0" + zlib.compress(bruto))
    else:
        dados += chunk(b"tEXt", b"preset\0" + bruto)
    dados += chunk(b"IEND", b"")
    return bytes(dados)


PRESET_COM_BRUSH = """<Preset paintopid="paintbrush" name="X">
 <param type="string" name="brush_definition"><![CDATA[
  <Brush type="auto_brush" filename="{arquivo}"/>
 ]]></param>
 <param type="string" name="requiredBrushFile"><![CDATA[{arquivo}]]></param>
</Preset>"""

PRESET_EMBUTIDO = """<Preset paintopid="paintbrush" name="X">
 <param type="string" name="brush_definition"><![CDATA[
  <Brush type="auto_brush" angle="0" spacing="0.05"/>
 ]]></param>
</Preset>"""

PRESET_FERRAMENTA = """<Preset paintopid="deformbrush" name="X">
 <param type="string" name="brush_definition"><![CDATA[
  <DeformBrush type="mirror"/>
 ]]></param>
</Preset>"""


class TestExtracaoDePreset(unittest.TestCase):
    def test_preset_simples(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = pathlib.Path(pasta) / "p.kpp"
            caminho.write_bytes(kpp(PRESET_COM_BRUSH.format(arquivo="a.gbr")))
            self.assertIn("requiredBrushFile", aud.xml_do_preset(caminho))

    def test_preset_comprimido(self):
        # 4 presets do pack do Deevad vêm assim; sem o zlib, a auditoria via
        # "não encontrou definição" e culpa o preset à toa.
        with tempfile.TemporaryDirectory() as pasta:
            caminho = pathlib.Path(pasta) / "p.kpp"
            caminho.write_bytes(kpp(PRESET_COM_BRUSH.format(arquivo="a.gbr"),
                                   comprimido=True))
            xml = aud.xml_do_preset(caminho)
            self.assertIn("a.gbr", xml)
            self.assertEqual("a.gbr", aud.valor_do_param(xml, "requiredBrushFile"))

    def test_arquivo_que_nao_e_png(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = pathlib.Path(pasta) / "p.kpp"
            caminho.write_bytes(b"isto nao e um png")
            self.assertEqual("", aud.xml_do_preset(caminho))


class TestAuditoriaDePack(unittest.TestCase):
    def _pack(self, base, arquivos_brushes, presets):
        pack = pathlib.Path(base) / "pack-x"
        (pack / "paintoppresets").mkdir(parents=True)
        (pack / "brushes").mkdir(parents=True)
        for nome in arquivos_brushes:
            (pack / "brushes" / nome).write_bytes(b"gbr")
        for nome, xml, comprimido in presets:
            (pack / "paintoppresets" / nome).write_bytes(kpp(xml, comprimido))
        return pack

    def test_referencia_quebrada_e_apontada(self):
        with tempfile.TemporaryDirectory() as base:
            pack = self._pack(base, [], [("A.kpp", PRESET_COM_BRUSH.format(arquivo="faltando.gbr"), False)])
            orfas, _emb, _esp, _sx = aud.auditar(pack)
            self.assertEqual({"faltando.gbr"}, set(orfas))

    def test_referencia_que_existe_nao_e_apontada(self):
        with tempfile.TemporaryDirectory() as base:
            pack = self._pack(base, ["tem.gbr"], [("A.kpp", PRESET_COM_BRUSH.format(arquivo="tem.gbr"), False)])
            orfas, _emb, _esp, _sx = aud.auditar(pack)
            self.assertEqual({}, orfas)

    def test_preset_embutido_nao_conta_como_quebrado(self):
        with tempfile.TemporaryDirectory() as base:
            pack = self._pack(base, [], [("A.kpp", PRESET_EMBUTIDO, False)])
            orfas, embutidos, _esp, _sx = aud.auditar(pack)
            self.assertEqual({}, orfas)
            self.assertEqual(["A.kpp"], embutidos)

    def test_paintop_de_ferramenta_nao_conta_como_quebrado(self):
        with tempfile.TemporaryDirectory() as base:
            pack = self._pack(base, [], [("A.kpp", PRESET_FERRAMENTA, False)])
            orfas, _emb, especiais, _sx = aud.auditar(pack)
            self.assertEqual({}, orfas)
            self.assertEqual(1, len(especiais))
            self.assertIn("deformbrush", especiais[0])

    def test_estrito_sai_com_um_quando_ha_quebrada(self):
        with tempfile.TemporaryDirectory() as base:
            pack = self._pack(base, [], [("A.kpp", PRESET_COM_BRUSH.format(arquivo="x.gbr"), False)])
            # A pasta de packs do script aponta para o repo; para o teste,
            # auditamos o pack temporário direto e checamos o sinal.
            orfas, _e, _s, _sx = aud.auditar(pack)
            self.assertTrue(orfas, "referência quebrada deveria ser apontada")


class TestEstadoDosPacks(unittest.TestCase):
    """O estado real do kit, para o relatório e para a documentação."""

    def setUp(self):
        self.brushes_dir = REPO / "hq_tools" / "resources" / "brushes"

    def test_packs_tem_licenca_e_fonte(self):
        for pack in sorted(p for p in self.brushes_dir.iterdir() if p.is_dir()):
            with self.subTest(pack=pack.name):
                self.assertTrue((pack / "LICENSE.txt").is_file())
                self.assertTrue((pack / "FONTE.md").is_file())

    def test_nenhum_pack_deixa_referencia_quebrada(self):
        # Invariante: se alguém acrescentar um preset que cita um arquivo de
        # fora do pack, o teste falha com o nome do arquivo e do preset.
        orfas = {}
        for pack in sorted(p for p in self.brushes_dir.iterdir() if p.is_dir()):
            encontradas, _embutidos, _especiais, sem_xml = aud.auditar(pack)
            self.assertEqual([], sem_xml, "{0} tem preset sem XML legível".format(pack.name))
            orfas.update(encontradas)
        self.assertEqual(
            {},
            orfas,
            "presets citaram recursos que não vêm no pack: {0}. Ou o arquivo "
            "sumiu, ou o preset aponta para a textura de outro preset.".format(
                {nome: sorted(ps) for nome, ps in sorted(orfas.items())}
            ),
        )

    def test_referencia_quebrada_seria_preset_removido(self):
        # Se uma referência quebrada aparecer de novo, ela só pode ser uma das
        # 3 que tiramos do kit: ou um preset voltou por engano, ou alguém criou
        # um arquivo com o nome errado. Nos dois casos a mensagem diz o que
        # aconteceu.
        for pack in sorted(p for p in self.brushes_dir.iterdir() if p.is_dir()):
            orfas, _e, _s, _sx = aud.auditar(pack)
            for nome, presets in orfas.items():
                with self.subTest(pack=pack.name, arquivo=nome):
                    self.assertIn(
                        nome,
                        PRESETS_REMOVIDOS,
                        "referência quebrada que não é dos presets removidos",
                    )
                    self.assertIn(presets[0], PRESETS_REMOVIDOS[nome])


if __name__ == "__main__":
    unittest.main()
