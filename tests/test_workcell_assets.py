import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from astrobench.workcell_assets import check_workcell_assets


class AssetIntegrityTests(unittest.TestCase):
    def fixture(self, root):
        for name in ('melfi_v6', 'rrm_tb1'):
            folder = root / name
            folder.mkdir()
            files = []
            for rel, blob in [('parts.json', b'{}'), ('model.blend', b'BLENDER'), ('model.glb', b'glTF')]:
                (folder/rel).write_bytes(blob)
                files.append(dict(path=rel, sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob)))
            (folder/'manifest.json').write_text(json.dumps({'files': files}))
        return root

    def test_verifies_both_and_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d))
            self.assertTrue(check_workcell_assets(root)['verified'])
            (root/'melfi_v6/model.glb').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                check_workcell_assets(root)

    def test_rejects_path_escape_and_duplicate(self):
        for attack in ('../outside', '/tmp/outside', 'parts.json'):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                root = self.fixture(Path(d))
                f = root/'melfi_v6/manifest.json'
                data = json.loads(f.read_text())
                data['files'].append(dict(data['files'][0], path=attack))
                f.write_text(json.dumps(data))
                with self.assertRaises(ValueError): check_workcell_assets(root)

    def test_rejects_archive_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.fixture(Path(d)); folder = root/'rrm_tb1'
            with zipfile.ZipFile(folder/'collision.zip', 'w') as z: z.writestr('../escape.obj', 'x')
            blob = (folder/'collision.zip').read_bytes()
            f = folder/'manifest.json'; data = json.loads(f.read_text())
            data['files'].append(dict(path='collision.zip',sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)))
            f.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'within'):
                check_workcell_assets(root)


if __name__ == '__main__': unittest.main()
