import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from astrobench.inventory import object_inventory, scene_catalog, select_catalog


class InventoryTests(unittest.TestCase):
    def test_default_core(self):
        result = object_inventory()
        self.assertEqual(result['object_set'], 'core20')
        self.assertEqual(result['object_count'], 20)
        self.assertEqual(result['objects'][0]['object_id'], 'candidate_standard_cube')
        self.assertEqual(len({r['object_id'] for r in result['objects']}), 20)

    def test_expansion(self):
        rows = object_inventory('objaverse8414')['objects']
        self.assertEqual(len(rows), 8414)
        uids = sorted(r['source_uid'] for r in rows)
        self.assertEqual(len(set(uids)), 8414)
        self.assertEqual(hashlib.sha256('\n'.join(uids).encode()).hexdigest(), 'fa7e4389130cbefb35c76771dbaa247c3a109f53cd3dd1c090b9d1f1ebe4fe9d')
        self.assertTrue(all(r['object_id'] == 'objaverse_' + r['source_uid'] for r in rows))
        self.assertTrue(all(r['source_url'] and r['license'] for r in rows))

    def test_selection_errors(self):
        rows = object_inventory()['objects']
        self.assertEqual(select_catalog(list(reversed(rows))), rows)
        with self.assertRaisesRegex(ValueError, 'Missing'):
            select_catalog(rows[:-1])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            select_catalog(rows + rows[:1])
        self.assertEqual(select_catalog([], 'custom'), [])
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            object_inventory('unknown')

    def test_corrupt_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'data').mkdir()
            (root/'data/core20.json').write_text('[]')
            (root/'data/object_sets.json').write_text(json.dumps({'sets': {'core20': {
                'manifest': 'core20.json', 'format': 'json', 'sha256': 'wrong'}}}))
            with patch('astrobench.inventory.files', return_value=root):
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    object_inventory()

    def test_scenes(self):
        catalog = scene_catalog()
        self.assertEqual(catalog['default'], 'iss_jpm')
        self.assertEqual({r['id'] for r in catalog['scenes']}, {
            'iss_jpm', 'iss_us_lab', 'iss_eu_lab', 'iss_node2', 'iss_cupola'})

    def test_cli_and_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'objects.json'
            cmd = [sys.executable, '-m', 'astrobench.cli', 'objects', '--output', str(target)]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(json.loads(target.read_text())['object_count'], 20)
            original = target.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(target.read_bytes(), original)
