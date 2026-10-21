"""Verify published model bytes before a workcell adapter uses them.

SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

WORKCELLS = ('melfi_v6', 'rrm_tb1')


def _relative(value):
    if type(value) is not str or not value or '\\' in value:
        raise ValueError('invalid asset path')
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in ('.', '..') for part in p.parts):
        raise ValueError('asset path must remain within its workcell directory')
    return p


def check_workcell_assets(asset_root):
    """Check manifests, every declared file, and portable archive member names.

    This checks release identities and packaging, not physical task success.
    The asset root is the cloned repository's assets/workcells directory.
    """
    root = Path(asset_root).resolve(strict=True)
    rows = []
    for name in WORKCELLS:
        folder = root / name
        raw = (folder / 'manifest.json').read_bytes()
        manifest = json.loads(raw)
        files = manifest.get('files')
        if not isinstance(files, list) or not files:
            raise ValueError(f'{name}: nonempty asset file manifest required')
        seen = set()
        total = 0
        for record in files:
            rel = _relative(record['path'])
            if str(rel) in seen:
                raise ValueError(f'{name}: duplicate asset file')
            seen.add(str(rel))
            source = (folder / str(rel)).resolve(strict=True)
            if not source.is_relative_to(folder.resolve()) or not source.is_file():
                raise ValueError(f'{name}: asset escapes its directory')
            blob = source.read_bytes()
            sha = hashlib.sha256(blob).hexdigest()
            if sha != record['sha256'] or len(blob) != record['bytes']:
                raise ValueError(f'{name}/{rel}: size or SHA256 mismatch')
            if source.suffix == '.zip':
                with zipfile.ZipFile(source) as archive:
                    members = set()
                    for member in archive.infolist():
                        part = _relative(member.filename)
                        if str(part) in members:
                            raise ValueError('duplicate archive entry')
                        members.add(str(part))
                        if (member.external_attr >> 16) & 0o170000 == 0o120000:
                            raise ValueError('asset archive contains a symbolic link')
                    bad = archive.testzip()
                    if bad is not None:
                        raise ValueError(f'corrupt archive member: {bad}')
            total += len(blob)
        if not {'parts.json'} <= seen or not any(p.endswith('.blend') for p in seen) or not any(p.endswith('.glb') for p in seen):
            raise ValueError(f'{name}: blend, glb and semantic parts required')
        rows.append(dict(workcell_id=name, manifest_sha256=hashlib.sha256(raw).hexdigest(),
                         file_count=len(files), bytes=total, verified=True))
    return {'schema': 'astrobench.workcell-asset-check/v1', 'workcells': rows,
            'verified': True}
