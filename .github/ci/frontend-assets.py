"""Bind transferred frontend bytes and packaged assets to the release source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

PROOF = ".release-provenance.json"
PREFIX = "figrecipe/_django/static/figrecipe/"


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("frontend artifact contains a symlink")
        if path.is_file() and path.name != PROOF:
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not {"assets/index.js", "assets/workspace.js", ".vite/manifest.json"} <= result.keys():
        raise ValueError("frontend artifact is missing entry assets")
    return result


def verify(root, version, sha, wheel=None):
    proof = json.loads((root / PROOF).read_text())
    if proof["version"] != version or proof["source_sha"] != sha:
        raise ValueError("frontend artifact source/version mismatch")
    if proof["files"] != inventory(root):
        raise ValueError("frontend artifact content mismatch")
    if wheel:
        with zipfile.ZipFile(wheel) as archive:
            actual = {name[len(PREFIX):]: hashlib.sha256(archive.read(name)).hexdigest()
                      for name in archive.namelist() if name.startswith(PREFIX)
                      and not name.endswith("/") and name != PREFIX + PROOF}
            if actual != proof["files"]:
                raise ValueError("wheel frontend differs from qualified artifact")
            if json.loads(archive.read(PREFIX + PROOF)) != proof:
                raise ValueError("wheel frontend provenance differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["record", "verify"])
    parser.add_argument("root", type=Path)
    parser.add_argument("version")
    parser.add_argument("sha")
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise ValueError("noncanonical frontend version")
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise ValueError("noncanonical source SHA")
    if args.mode == "record":
        files = inventory(args.root)
        # The entry's baked version must match the release, not a prior build.
        if json.dumps(args.version) not in (args.root / "assets/workspace.js").read_text():
            raise ValueError("frontend entry has a stale version")
        proof = {"version": args.version, "source_sha": args.sha, "files": files}
        (args.root / PROOF).write_text(json.dumps(proof, sort_keys=True) + "\n")
    verify(args.root, args.version, args.sha, args.wheel)


if __name__ == "__main__":
    main()
