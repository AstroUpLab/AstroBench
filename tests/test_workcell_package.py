"""Cross-file release checks: targets must resolve in editable and neutral assets."""
import json
import struct
from pathlib import Path
import unittest
from astrobench.workcell_assets import check_workcell_assets
from astrobench.workcells import workcell_catalog, make_workcell_plan

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'workcells'


class WorkcellPackageTests(unittest.TestCase):
    def test_release_bytes_and_catalog_binding(self):
        self.assertTrue(check_workcell_assets(ROOT)['verified'])
        catalog = workcell_catalog(ROOT)
        self.assertEqual(set(catalog['assets']), {'melfi_v6', 'rrm_tb1'})
        plan = make_workcell_plan(repeats=2, seed=42, asset_root=ROOT)
        self.assertEqual(len(plan['episodes']), 58)

    def test_semantic_targets_survive_glb_export(self):
        for name in ('melfi_v6', 'rrm_tb1'):
            with self.subTest(workcell=name):
                folder = ROOT / name
                parts = json.loads((folder/'parts.json').read_text())
                blob = (folder/(name+'.glb')).read_bytes()
                magic, version, length = struct.unpack_from('<4sII', blob)
                self.assertEqual((magic, version, length), (b'glTF', 2, len(blob)))
                json_length, kind = struct.unpack_from('<II', blob, 12)
                self.assertEqual(kind, 0x4e4f534a)
                gltf = json.loads(blob[20:20+json_length])
                names = {n.get('name') for n in gltf['nodes']}
                for target, binding in parts['semantic_targets'].items():
                    for field in ('root_object', 'moving_object', 'lid_object', 'latch_object', 'card_object', 'tool_root_object'):
                        if binding.get(field):
                            self.assertIn(binding[field], parts['nodes'], (target,field))
                            self.assertIn(binding[field], names, (target,field))
                self.assertTrue(all('uri' not in b for b in gltf.get('buffers', [])))
                self.assertTrue(all('uri' not in img for img in gltf.get('images', [])))


if __name__ == '__main__': unittest.main()
