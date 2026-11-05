"""Source distributions must not contain dangling documentation image links."""
import posixpath
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_documentation_image_links_have_jailed_tracked_regular_png_targets():
    # Arrange: read Git objects, never follow arbitrary host symlinks.
    listing = subprocess.run(
        ['git', '-C', str(ROOT), 'ls-files', '--stage', '-z', 'docs/sphinx'],
        check=True, capture_output=True, timeout=10,
    ).stdout
    entries = {}
    for row in filter(None, listing.split(b'\0')):
        metadata, name = row.split(b'\t', 1)
        mode, blob, stage = metadata.decode().split()
        entries[name.decode()] = (mode, blob, stage)
    links = {path: item for path, item in entries.items()
             if path.startswith('docs/sphinx/_static/') and path.endswith('.png') and item[0] == '120000'}
    # Act
    violations = []
    for path, (_, blob, stage) in links.items():
        text = subprocess.run(['git', '-C', str(ROOT), 'cat-file', 'blob', blob],
                              check=True, capture_output=True, timeout=10).stdout.decode()
        target = posixpath.normpath(str(PurePosixPath(path).parent / text))
        entry = entries.get(target)
        if (stage != '0' or not target.startswith('docs/sphinx/')
            or entry is None or entry[0] not in {'100644', '100755'} or entry[2] != '0'):
            violations.append(path + ': missing, unmerged or unjailed regular Git target')
            continue
        signature = subprocess.run(['git', '-C', str(ROOT), 'cat-file', 'blob', entry[1]],
                                   check=True, capture_output=True, timeout=10).stdout[:8]
        if signature != b'\x89PNG\r\n\x1a\n':
            violations.append(path + ': target is not a PNG')
    # Assert
    assert (bool(links), violations) == (True, [])
