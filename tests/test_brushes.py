"""Testes dos conjuntos de pincéis e da sugestão de slots (fora do Krita)."""

import unittest

from hq_tools.modules.brushes import sets


INSTALLED = [
    "c) Pencil-1 Hard",
    "c) Pencil-2",
    "c) Pencil-3 Large 4B",
    "d) Ink-1 Precision",
    "d) Ink-2 Fineliner",
    "d) Ink-3 Gpen",
    "j) Watercolor Fringe",
    "j) Waterpaint Hard Edges",
    "i) Wet Bristles",
    "f) Bristles-2 Flat Rough",
    "g) Dry Brushing",
    "y) Screentones Regular",
]


class TestBrushSets(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(sets.normalize("d) Ink-1 Precision"), "dink1precision")

    def test_match_preset(self):
        self.assertEqual(sets.match_preset(INSTALLED, "Pencil-1"), "c) Pencil-1 Hard")
        self.assertEqual(sets.match_preset(INSTALLED, "Ink-3"), "d) Ink-3 Gpen")
        self.assertEqual(sets.match_preset(INSTALLED, "Nada"), "")

    def test_suggest_sets(self):
        result = dict(sets.suggest_sets(INSTALLED))
        self.assertIn("Rascunho", result)
        self.assertIn("c) Pencil-1 Hard", result["Rascunho"])
        self.assertIn("d) Ink-3 Gpen", result["Contornos"])
        self.assertIn("j) Watercolor Fringe", result["Aquarela/Guache"])
        self.assertIn("f) Bristles-2 Flat Rough", result["Acrílico/Óleo"])
        self.assertIn("y) Screentones Regular", result["Retículas"])

    def test_slot_suggestions(self):
        suggestions = sets.slot_suggestions(INSTALLED)
        self.assertEqual(len(suggestions), sets.SLOT_COUNT)
        self.assertEqual(suggestions[0], "c) Pencil-1 Hard")
        self.assertIn("d) Ink-2 Fineliner", suggestions[4:8])

    def test_slot_suggestions_limita_por_conjunto(self):
        suggestions = sets.slot_suggestions(["Pencil-1", "Pencil-2", "Pencil-3", "Pencil-5", "Pencil-4"])
        self.assertEqual(len(suggestions), sets.SLOT_COUNT)
        self.assertEqual(suggestions[:4], ["Pencil-1", "Pencil-2", "Pencil-3", "Pencil-5"])

    def test_slots_vazios_sao_preenchidos(self):
        suggestions = sets.slot_suggestions([])
        self.assertEqual(len(suggestions), sets.SLOT_COUNT)
        self.assertTrue(all(name == "" for name in suggestions))


if __name__ == "__main__":
    unittest.main()