"""Testes do núcleo de retículas (rodam fora do Krita)."""

import unittest

from hq_tools.modules.screentone import core


class TestScreentoneCore(unittest.TestCase):
    def test_lpi_para_pixels(self):
        self.assertAlmostEqual(core.lpi_to_cell_px(60, 300), 5.0)
        self.assertAlmostEqual(core.lpi_to_cell_px(30, 600), 20.0)
        self.assertEqual(core.lpi_to_cell_px(0, 300), 0.0)

    def test_limite_de_frequencia(self):
        self.assertAlmostEqual(core.max_frequency(300), 150.0)
        self.assertAlmostEqual(core.clamp_frequency(200, 300), 150.0)
        self.assertAlmostEqual(core.clamp_frequency(60, 300), 60.0)
        self.assertAlmostEqual(core.clamp_frequency(0.2, 300), 1.0)

    def test_normalize_preset_preenche_padroes(self):
        preset = core.normalize_preset({"name": "Teste", "lpi": "45"})
        self.assertEqual(preset["name"], "Teste")
        self.assertAlmostEqual(preset["lpi"], 45.0)
        self.assertEqual(preset["pattern"], core.PATTERN_DOTS)
        self.assertEqual(preset["equalization"], 2)
        self.assertEqual(preset["fg"], "#000000")

    def test_screentone_properties(self):
        preset = core.normalize_preset(
            {"lpi": 60.0, "rotation": 45.0, "pattern": core.PATTERN_LINES}
        )
        props = core.screentone_properties(preset, 300)
        self.assertEqual(props["size_mode"], core.SIZE_MODE_RESOLUTION)
        self.assertEqual(props["resolution"], 300.0)
        self.assertEqual(props["frequency_x"], 60.0)
        self.assertEqual(props["frequency_y"], 60.0)
        self.assertEqual(props["pattern"], core.PATTERN_LINES)
        self.assertEqual(props["foreground_color"], "#000000")
        self.assertTrue(props["align_to_pixel_grid"])

    def test_screentone_properties_limita_frequencia(self):
        preset = core.normalize_preset({"lpi": 400.0})
        props = core.screentone_properties(preset, 300)
        self.assertAlmostEqual(props["frequency_x"], 150.0)

    def test_halftone_properties_prefixos(self):
        preset = core.normalize_preset({"lpi": 60.0})
        props = core.halftone_properties(preset, "RGBA", 300)
        self.assertEqual(props["mode"], "intensity")
        self.assertEqual(props["color_model_id"], "RGBA")
        self.assertEqual(props["intensity_generator"], "screentone")
        self.assertEqual(
            props["intensity_generator_screentone_frequency_x"], 60.0
        )
        self.assertEqual(props["intensity_generator_screentone_resolution"], 300.0)
        self.assertIn("intensity_hardness", props)

    def test_halftone_com_padrao(self):
        preset = core.normalize_preset({})
        props = core.halftone_properties(
            preset, "RGBA", 300, generator=core.PATTERN_GENERATOR_ID,
            pattern_name="Stars_Sized.png",
        )
        self.assertEqual(props["intensity_generator"], "pattern")
        self.assertEqual(props["intensity_generator_pattern_pattern"], "Stars_Sized.png")
        self.assertNotIn("intensity_generator_screentone_pattern", props)

    def test_halftone_cmyk_por_canal(self):
        preset = core.normalize_preset({"lpi": 60.0, "rotation": 45.0})
        props = core.halftone_cmyk_properties(preset, "CMYKA", 300)
        self.assertEqual(props["mode"], "independent_channels")
        self.assertEqual(props["color_model_id"], "CMYKA")
        for index in range(4):
            prefix = "CMYKA_channel{0}_".format(index)
            self.assertIn(prefix + "generator", props)
            self.assertIn(prefix + "generator_screentone_frequency_x", props)
        angles = [15.0, 75.0, 0.0, 45.0]
        for index, expected in enumerate(angles):
            prefix = "CMYKA_channel{0}_".format(index)
            self.assertAlmostEqual(
                props[prefix + "generator_screentone_rotation"], expected
            )

    def test_pattern_fill_properties(self):
        props = core.pattern_fill_properties("Stripes02.pat")
        self.assertEqual(props, {"pattern": "Stripes02.pat"})

    def test_fingerprint_iguala_tons(self):
        a = core.screentone_properties(core.normalize_preset({"lpi": 60.0}), 300)
        b = core.screentone_properties(core.normalize_preset({"lpi": 60.0}), 300)
        self.assertEqual(core.tone_fingerprint(a), core.tone_fingerprint(b))
        c = core.screentone_properties(core.normalize_preset({"lpi": 85.0}), 300)
        self.assertNotEqual(core.tone_fingerprint(a), core.tone_fingerprint(c))
        d = core.screentone_properties(core.normalize_preset({"lpi": 60.0}), 600)
        self.assertEqual(core.tone_fingerprint(a), core.tone_fingerprint(d))
        e = core.screentone_properties(
            core.normalize_preset({"lpi": 60.0, "position_x": 120.0}), 300
        )
        self.assertNotEqual(core.tone_fingerprint(a), core.tone_fingerprint(e))
        f = core.screentone_properties(
            core.normalize_preset({"lpi": 60.0, "position_y": 45.0}), 300
        )
        self.assertNotEqual(core.tone_fingerprint(a), core.tone_fingerprint(f))

    def test_color_xml_para_hex(self):
        xml = '<color channeldepth="U8" colorspace="RGBA" r="0" g="0" b="0" a="255"/>'
        self.assertEqual(core.color_xml_to_hex(xml), "#000000")
        self.assertEqual(core.color_xml_to_hex("#ffcc00"), "#ffcc00")
        self.assertIsNone(core.color_xml_to_hex("nada"))

    def test_presets_do_arquivo(self):
        import os

        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "hq_tools",
            "modules",
            "screentone",
            "presets.json",
        )
        presets = core.load_presets(path)
        self.assertGreaterEqual(len(presets), 8)
        names = [preset["name"] for preset in presets]
        self.assertIn("Sombra média 60 LPI", names)


if __name__ == "__main__":
    unittest.main()
