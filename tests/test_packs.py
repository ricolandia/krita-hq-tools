"""Testes do instalador de packs de pincéis (fora do Krita)."""

import os
import shutil
import struct
import tempfile
import unittest
import zlib

from hq_tools.modules.brushes import packs


def png_com_preset(nome_interno):
    """PNG sintético com o chunk tEXt 'preset' (formato real do .kpp)."""
    dados = bytearray(b"\x89PNG\r\n\x1a\n")

    def chunk(tipo, payload):
        parte = struct.pack(">I", len(payload)) + tipo + payload
        parte += struct.pack(">I", zlib.crc32(tipo + payload) & 0xFFFFFFFF)
        return parte

    xml = '<Preset paintopid="paintbrush" name="{0}"/>'.format(nome_interno).encode()
    dados += chunk(b"tEXt", b"preset\0" + xml)
    dados += chunk(b"IEND", b"")
    return bytes(dados)


def fazer_pack(base, nome="deevad-v8.2"):
    pack = os.path.join(base, nome)
    os.makedirs(os.path.join(pack, "paintoppresets"), exist_ok=True)
    os.makedirs(os.path.join(pack, "brushes"), exist_ok=True)
    with open(os.path.join(pack, "FONTE.md"), "w", encoding="utf-8") as handle:
        handle.write(
            "# Pack\n"
            "- Autor: Teste\n"
            "- Licenca: CC-BY 4.0\n"
            "- Origem: https://exemplo.test\n"
        )
    with open(os.path.join(pack, "LICENSE.txt"), "w", encoding="utf-8") as handle:
        handle.write("CC-BY 4.0 (teste)\n")
    for nome in ("A-Teste.kpp", "B-Teste.kpp"):
        with open(os.path.join(pack, "paintoppresets", nome), "wb") as handle:
            handle.write(b"\x89PNG")
    with open(os.path.join(pack, "brushes", "textura.gbr"), "wb") as handle:
        handle.write(b"gbr")
    return pack


class TestPacks(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="hq_tools_packs_")
        self.pack = fazer_pack(self.base)
        self.destinos = {tipo: os.path.join(self.base, "dest", tipo) for tipo in packs.TIPOS}

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_listar_packs(self):
        resultado = packs.listar_packs(self.base)
        self.assertIn("deevad-v8.2", resultado)

    def test_pack_info(self):
        info = packs.pack_info(self.pack)
        self.assertEqual(info["autor"], "Teste")
        self.assertEqual(info["licenca"], "CC-BY 4.0")
        self.assertEqual(info["nome"], "deevad-v8.2")

    def test_pack_license(self):
        self.assertIn("CC-BY 4.0", packs.pack_license(self.pack))

    def test_arquivos_por_tipo(self):
        arquivos = packs.arquivos_por_tipo(self.pack)
        self.assertEqual(len(arquivos["paintoppresets"]), 2)
        self.assertEqual(len(arquivos["brushes"]), 1)
        self.assertNotIn("patterns", arquivos)

    def test_instalar_e_verificar(self):
        self.assertFalse(packs.pack_instalado(self.pack, self.destinos))
        total = packs.instalar_pack(self.pack, self.destinos)
        self.assertEqual(total, 3)
        self.assertTrue(packs.pack_instalado(self.pack, self.destinos))
        self.assertTrue(
            os.path.isfile(os.path.join(self.destinos["paintoppresets"], "A-Teste.kpp"))
        )

    def test_instalar_sem_destino(self):
        total = packs.instalar_pack(self.pack, {})
        self.assertEqual(total, 0)

    def test_preset_names(self):
        nomes = packs.preset_names(self.pack)
        self.assertIn("A-Teste", nomes)
        self.assertIn("B-Teste", nomes)
        self.assertEqual(len(nomes), 2)

    def test_preset_aliases(self):
        pasta = os.path.join(self.pack, "paintoppresets")
        with open(os.path.join(pasta, "X9AA_WC_Basic.kpp"), "wb") as handle:
            handle.write(png_com_preset("X9AA - WC Basic"))
        with open(os.path.join(pasta, "SemNome.kpp"), "wb") as handle:
            handle.write(b"\x89PNG\r\n\x1a\n")
        aliases = dict(packs.preset_aliases(self.pack))
        self.assertEqual(aliases["X9AA_WC_Basic"], "X9AA - WC Basic")
        self.assertEqual(aliases["SemNome"], "SemNome")
        self.assertEqual(aliases["A-Teste"], "A-Teste")

    def test_aliases_kpp_real_do_kit(self):
        real = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "hq_tools",
            "resources",
            "brushes",
            "vasco-basque-watercolor",
            "paintoppresets",
            "X9AA_WC_Basic.kpp",
        )
        self.assertTrue(os.path.isfile(real), "kpp real do kit esperado no repo")
        self.assertEqual(packs._preset_internal_name(real), "X9AA - WC Basic")


if __name__ == "__main__":
    unittest.main()