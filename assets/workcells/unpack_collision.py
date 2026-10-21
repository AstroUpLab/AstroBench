# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Verify and safely unpack a workcell's collision mesh archive."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def unpack(asset_directory):
    root=Path(asset_directory).resolve()
    record=json.loads((root/'collision.json').read_text())['mesh_archive']
    path=root/record['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
        raise ValueError('Collision archive SHA256 mismatch')
    with zipfile.ZipFile(path) as archive:
        members=archive.infolist()
        if sum(m.file_size for m in members)>512*1024*1024:
            raise ValueError('Archive expands beyond 512 MiB')
        for member in members:
            name=PurePosixPath(member.filename)
            destination=(root/member.filename).resolve()
            if name.is_absolute() or '..' in name.parts or '\\' in member.filename or not destination.is_relative_to(root):
                raise ValueError('Unsafe archive path')
            if not name.parts or name.parts[0]!=record['extract_directory']:
                raise ValueError('Unexpected archive directory')
            if stat.S_ISLNK(member.external_attr>>16):raise ValueError('Archive symlinks are forbidden')
            if destination.exists() and destination.is_symlink():raise ValueError('Refusing symlink overwrite')
        for member in members:
            if member.is_dir():continue
            destination=root/member.filename
            destination.parent.mkdir(parents=True,exist_ok=True)
            data=archive.read(member)
            if destination.exists() and destination.read_bytes()!=data:
                raise FileExistsError('Different existing mesh: '+str(destination))
            destination.write_bytes(data)
    return root/record['extract_directory']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset_directory',type=Path)
    print(unpack(parser.parse_args().asset_directory))
