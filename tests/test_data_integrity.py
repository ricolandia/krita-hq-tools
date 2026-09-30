"""Testes de integridade de dados (rodam fora do Krita).

Cobrem as correções que impediam perda de trabalho do autor: configuração
sobrescrita por outro docker, ``.kra`` órfão, registro duplicado no CPMT,
presets de retícula truncados e preset de pincel do usuário sobrescrito em
silêncio.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from hq_tools.core.config import Config
from hq_tools.core.cpmt import CPMTError, CPMTProject, create_project_with_page
from hq_tools.modules.brushes import packs
from hq_tools.modules.screentone import core as screentone_core


def escrever_json(path, data, encoding="utf-8"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def temporarios_em(pasta):
    """Arquivos temporários que sobraram (o ideal é nenhum)."""
    return [nome for nome in os.listdir(pasta) if ".json" in nome and ".tmp" in nome]


class TestConfigSemPerdaDeDados(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="hq_tools_cfg_")
        self.path = os.path.join(self.pasta, "config.json")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_set_nao_apaga_o_que_outro_docker_gravou(self):
        # Duas instâncias vivas, como dois módulos abertos ao mesmo tempo.
        paginas = Config(self.path)
        pincéis = Config(self.path)
        paginas.set("pages.format", "A5")
        # Antes da correção, isto gravava por cima do arquivo e trazia de
        # volta só os padrões: o formato escolhido era perdido.
        pincéis.set("brushes.slots", ["Pencil-1"] + [""] * 15)

        self.assertEqual(Config(self.path).get("pages.format"), "A5")
        self.assertEqual(Config(self.path).get("brushes.slots")[0], "Pencil-1")

    def test_set_rejeita_caminho_sobre_lista(self):
        config = Config(self.path)
        with self.assertRaises(TypeError):
            config.set("brushes.slots.novo", "x")
        self.assertEqual(len(config.get("brushes.slots")), 16)

    def test_get_int_tolerante(self):
        config = Config(self.path)
        config.set("pages.dpi", "lixo")
        self.assertEqual(config.get_int("pages.dpi", 300), 300)
        config.set("pages.dpi", "150")
        self.assertEqual(config.get_int("pages.dpi", 300), 150)

    def test_arquivo_ilegivel_e_preservado(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{isto nao e json")
        # O aviso vai para o log do Krita (stderr); aqui só o arquivo importa.
        with contextlib.redirect_stderr(io.StringIO()) as aviso:
            config = Config(self.path)
        self.assertEqual(config.get("pages.format"), "A4")
        self.assertIn("ilegivel", aviso.getvalue())
        backups = [
            nome for nome in os.listdir(self.pasta) if ".ilegivel-" in nome
        ]
        self.assertEqual(len(backups), 1, "o arquivo corrompido precisa ficar salvo")
        with open(os.path.join(self.pasta, backups[0]), encoding="utf-8") as handle:
            self.assertIn("isto nao e json", handle.read())


class TestCPMTSemDuplicarPaginas(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="hq_tools_cpmt_int_")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_register_pages_ignora_repetida(self):
        criar = os.path.join(self.root, "pages")
        os.makedirs(criar, exist_ok=True)
        open(os.path.join(criar, "HQ001.kra"), "wb").close()
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))

        projeto = CPMTProject(self.root)
        projeto.register_pages([os.path.join("pages", "HQ001.kra")])
        self.assertEqual(projeto.page_relatives(), [os.path.join("pages", "HQ001.kra")])

        projeto.register_pages([os.path.join("pages", "HQ001.kra")])
        self.assertEqual(len(projeto.page_relatives()), 1)

    def test_register_pages_devolve_apenas_as_novas(self):
        os.makedirs(os.path.join(self.root, "pages"), exist_ok=True)
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        projeto = CPMTProject(self.root)
        novas = projeto.register_pages(
            [os.path.join("pages", "HQ001.kra"), os.path.join("pages", "HQ002.kra")]
        )
        self.assertEqual(novas, [os.path.join("pages", "HQ002.kra")])
        self.assertEqual(projeto.page_number, 2)

    def test_set_page_order_ignora_repetida(self):
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        projeto = CPMTProject(self.root)
        projeto.set_page_order(["a.kra", "b.kra", "a.kra"])
        self.assertEqual(CPMTProject(self.root).page_relatives(), ["a.kra", "b.kra"])

    def test_criacao_nao_deixa_temporario(self):
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        self.assertEqual(temporarios_em(self.root), [])

    def test_save_nao_deixa_temporario(self):
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        projeto = CPMTProject(self.root)
        projeto.save()
        self.assertEqual(temporarios_em(self.root), [])

    def test_json_corrompido_da_erro_explicito(self):
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        with open(os.path.join(self.root, "comicConfig.json"), "wb") as handle:
            handle.write("isto nao e json".encode("utf-16"))
        with self.assertRaises(CPMTError):
            CPMTProject(self.root)

    def test_page_number_corrompido_nao_derruba(self):
        create_project_with_page(self.root, os.path.join("pages", "HQ001.kra"))
        projeto = CPMTProject(self.root)
        projeto.config["pageNumber"] = "dois"
        self.assertEqual(projeto.page_number, 0)
        self.assertTrue(projeto.next_page_name().endswith("001.kra"))


class TestPresetsDeReticula(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="hq_tools_presets_")
        self.path = os.path.join(self.pasta, "presets.json")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_item_quebrado_nao_derruba_o_resto(self):
        escrever_json(
            self.path,
            {
                "presets": [
                    {"name": "ok", "lpi": 65},
                    "isto nao e um preset",
                    {"name": "lpi escrito como texto", "lpi": "60"},
                ]
            },
        )
        presets = screentone_core.load_presets(self.path)
        # O item que nem é preset é descartado e o de campo escrito como texto
        # é convertido; antes a exceção subia na construção do docker e o módulo
        # inteiro não abria.
        self.assertEqual(
            [p["name"] for p in presets], ["ok", "lpi escrito como texto"]
        )
        self.assertEqual(presets[1]["lpi"], 60.0)

    def test_normalize_tolera_campos_como_texto(self):
        padrao = screentone_core.DEFAULT_PRESET
        preset = screentone_core.normalize_preset(
            {"name": "x", "lpi": "60", "rotation": None, "align_x": "8"}
        )
        self.assertEqual(preset["lpi"], 60.0)
        # Campo sem valor volta ao padrão do preset, não a zero.
        self.assertEqual(preset["rotation"], padrao["rotation"])
        self.assertEqual(preset["align_x"], 8)

    def test_save_presets_e_atomico(self):
        screentone_core.save_presets(self.path, [{"name": "a", "lpi": 60}])
        self.assertEqual(temporarios_em(self.pasta), [])
        self.assertEqual(len(screentone_core.load_presets(self.path)), 1)


class TestPacksNaoSobrescrevemOPautor(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="hq_tools_pack_")
        self.pack = os.path.join(self.pasta, "pack", "paintoppresets")
        self.destinos = {"paintoppresets": os.path.join(self.pasta, "destino")}
        os.makedirs(self.pack)
        os.makedirs(self.destinos["paintoppresets"])
        with open(os.path.join(self.pack, "A.kpp"), "wb") as handle:
            handle.write(b"versao do pack")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def destino(self, nome="A.kpp"):
        return os.path.join(self.destinos["paintoppresets"], nome)

    def test_preset_editado_pelo_autor_e_preservado(self):
        with open(self.destino(), "wb") as handle:
            handle.write(b"meu pincel ajustado")
        relatorio = []
        total = packs.instalar_pack(
            os.path.join(self.pasta, "pack"), self.destinos, relatorio
        )
        with open(self.destino(), "rb") as handle:
            self.assertEqual(handle.read(), b"versao do pack")
        self.assertTrue(os.path.isfile(self.destino() + ".hqtools-backup"))
        self.assertEqual(total, 1)
        self.assertTrue(any("cópia" in linha for linha in relatorio))

    def test_arquivo_identico_nao_e_recopiado(self):
        with open(self.destino(), "wb") as handle:
            handle.write(b"versao do pack")
        total = packs.instalar_pack(os.path.join(self.pasta, "pack"), self.destinos)
        self.assertEqual(total, 0)
        self.assertFalse(os.path.isfile(self.destino() + ".hqtools-backup"))

    def test_instalacao_simples_continua_funcionando(self):
        total = packs.instalar_pack(os.path.join(self.pasta, "pack"), self.destinos)
        self.assertEqual(total, 1)
        self.assertTrue(os.path.isfile(self.destino()))


class TestDockerDePinceisDestruido(unittest.TestCase):
    def test_ponteiro_para_objeto_morto_e_descartado(self):
        from hq_tools.modules import brushes

        class Morto:
            def __getattribute__(self, nome):
                raise RuntimeError("objeto C++ destruído")

        brushes.register_docker(Morto())
        self.assertIsNone(brushes.current_docker())
        # O atalho tem de continuar funcionando pelo caminho sem docker.
        brushes.activate_slot(0)
        brushes.register_docker(None)
        self.assertIsNone(brushes.current_docker())


if __name__ == "__main__":
    unittest.main()
