"""Sanity checks for gear_presets.json.

The presets are reference data that users copy into config.json, so the
checks guard against typos: every cassette must actually span the range
in its label, have as many cogs as its speed count, and be strictly
ascending (the order config.json/physics.gear_table expect).
"""

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).parent
RANGE_RE = re.compile(r"\b(\d+)-(\d+)\b")


def load(name):
    with open(ROOT / name) as f:
        return json.load(f)


class TestGearPresets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.presets = load("gear_presets.json")

    def test_cassettes_match_their_labels(self):
        cassettes = self.presets["cassettes"]
        self.assertTrue(cassettes)
        for key, preset in cassettes.items():
            with self.subTest(key=key):
                cogs = preset["cogs"]
                match = RANGE_RE.search(preset["label"])
                self.assertIsNotNone(match, "label must state its range")
                self.assertEqual([cogs[0], cogs[-1]], [int(match[1]), int(match[2])])
                self.assertEqual(len(cogs), preset["speeds"])
                self.assertEqual(cogs, sorted(set(cogs)))

    def test_chainrings_match_their_labels(self):
        chainrings = self.presets["chainrings"]
        self.assertTrue(chainrings)
        for key, preset in chainrings.items():
            with self.subTest(key=key):
                rings = preset["chainrings"]
                self.assertIn(len(rings), (1, 2))
                self.assertEqual(rings, sorted(set(rings)))
                for ring in rings:
                    self.assertRegex(preset["label"], rf"\b{ring}(?:T|/|\b)")

    @unittest.skipUnless(
        importlib.util.find_spec("numpy"),
        "main.load_config imports physics, which needs numpy (see requirements.txt)",
    )
    def test_presets_are_drop_in_config_values(self):
        # A preset swapped into config.json must keep main.load_config happy.
        from main import load_config

        cfg = load("config.json")
        preset_cfg = dict(cfg)
        preset_cfg["cassette"] = self.presets["cassettes"]["sram_road_12s_10_36"]["cogs"]
        preset_cfg["chainrings"] = self.presets["chainrings"]["sram_road_48_35"]["chainrings"]
        tmp = ROOT / "_test_preset_config.json"
        try:
            tmp.write_text(json.dumps(preset_cfg))
            loaded = load_config(str(tmp))
        finally:
            tmp.unlink(missing_ok=True)
        self.assertEqual(loaded["cassette"], preset_cfg["cassette"])
        self.assertEqual(loaded["chainrings"], preset_cfg["chainrings"])
        self.assertGreater(loaded["wheel_circumference_m"], 0)


if __name__ == "__main__":
    unittest.main()
