"""Data fidelity and fallback guarantees for the connected profile."""
import collections
import copy
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_connections as render
from collect_activity import aggregate


class ConnectedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "activity.json").read_text())
        cls.files = render.build(cls.snapshot)

    def test_pulses_conserve_each_daily_metric_and_visibility(self):
        actual = collections.Counter()
        for packet in render.packets(self.snapshot):
            self.assertGreater(packet.weight, 0)
            actual[packet.day, packet.kind, packet.visibility] += packet.weight
        for day in range(56):
            for i, (kind, _) in enumerate(render.KINDS):
                for visibility in ("public", "private"):
                    self.assertEqual(actual[day, i, visibility], self.snapshot["metrics"][kind][visibility][day])

    def test_replay_totals_follow_the_snapshot(self):
        self.assertEqual(render.totals(self.snapshot, -1)["total"], 0)
        for day in range(56):
            values = render.totals(self.snapshot, day)
            self.assertEqual(values["total"], sum(self.snapshot["series"][:day + 1]))
            self.assertEqual(values["public"] + values["private"], values["total"])
            self.assertEqual(sum(values["kinds"]), values["total"])

    def test_empty_window_has_no_phantom_activity(self):
        empty = aggregate(self.snapshot["days"], [], [], self.snapshot["generated_at"])
        self.assertEqual(render.packets(empty), [])
        self.assertEqual(render.totals(empty)["total"], 0)
        ET.fromstring(render.hero(empty, True, "dark").finish())

    def test_non_aggregate_fields_cannot_be_published(self):
        invalid = copy.deepcopy(self.snapshot)
        invalid["repositories"] = ["private-project-should-never-be-exported"]
        with self.assertRaises(ValueError):
            render.build(invalid)

    def test_readme_is_only_the_map_with_still_alternatives(self):
        root = ET.fromstring(self.files["README.md"])
        self.assertEqual(root.tag, "picture")
        self.assertEqual(len(root.findall("img")), 1)
        self.assertEqual(len(root.findall("source")), 7)
        self.assertNotIn("<details", self.files["README.md"])
        for source in list(root):
            path = source.get("srcset") or source.get("src")
            self.assertIn(path.removeprefix("./"), self.files)
        sources = root.findall("source")
        self.assertTrue(all("prefers-reduced-motion" in x.get("media") for x in sources[:4]))

    def test_still_and_animated_assets_share_the_final_snapshot(self):
        ns = {"s": "http://www.w3.org/2000/svg"}
        for theme in render.PALETTES:
            for mobile in (False, True):
                suffix = f'{theme}{"-mobile" if mobile else ""}.svg'
                animation = ET.fromstring(self.files["assets/connections/map-" + suffix])
                still = ET.fromstring(self.files["assets/connections/map-still-" + suffix])
                animated_final = animation.find("s:g[@class='snapshot']", ns)
                still_final = still.find("s:g[@class='snapshot']", ns)
                self.assertEqual(ET.tostring(animated_final), ET.tostring(still_final))
                self.assertNotIn("@keyframes", self.files["assets/connections/map-still-" + suffix])
                for node in animation.iter():
                    self.assertNotIn(node.tag.split("}")[-1], ("script", "foreignObject", "image", "a"))
                    self.assertFalse(any(name.startswith("on") for name in node.attrib))
                self.assertNotIn("infinite", self.files["assets/connections/map-" + suffix])


if __name__ == "__main__":
    unittest.main()
