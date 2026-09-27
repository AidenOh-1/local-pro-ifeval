"""Read-only release inventory verification. No automatic allowlist expansion."""
import hashlib
import json
from pathlib import Path
import subprocess

INDEX = 'UPLOAD_ALLOWLIST.json'

def payload(files):
    return hashlib.sha256(''.join(f'{files[p]}  {p}\n' for p in sorted(files)).encode()).hexdigest()

def verify(root, inventory=None):
    root = Path(root)
    data = json.loads((root / INDEX).read_text())
    expected = data['files']
    if inventory is None:
        # Include ignored/untracked files: do not silently accept a dirty upload tree.
        inventory = {p.relative_to(root).as_posix() for p in root.rglob('*')
                     if '.git' not in p.relative_to(root).parts and (p.is_file() or p.is_symlink())}
    if set(inventory) != set(expected) | {INDEX}:
        raise ValueError('FILE_SET_MISMATCH')
    for name, digest in expected.items():
        p = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.is_file():
            raise ValueError('INVALID_FILE')
        if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise ValueError('CONTENT_MISMATCH:' + name)
    if payload(expected) != data['payload_sha256']:
        raise ValueError('PAYLOAD_MISMATCH')
    return {'files': len(expected) + 1, 'payload_sha256': data['payload_sha256']}

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    result = verify(root)
    tracked = set(subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')) - {''}
    verify(root, tracked)
    print(json.dumps(result, sort_keys=True))
