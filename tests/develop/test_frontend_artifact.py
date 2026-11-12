"""Real-file controls for the cross-job frontend and wheel handoff."""
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".github/ci/frontend-assets.py"
spec = importlib.util.spec_from_file_location("frontend_assets", SCRIPT)
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)
SHA = "a" * 40


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / ".vite").mkdir()
    for name, data in {"assets/index.js": "entry", "assets/workspace.js": 'const version="0.44.7";',
                       ".vite/manifest.json": "{}"}.items():
        (tmp_path / name).write_text(data)
    proof = {"version": "0.44.7", "source_sha": SHA, "files": assets.inventory(tmp_path)}
    (tmp_path / assets.PROOF).write_text(json.dumps(proof))
    return tmp_path


def test_transferred_bytes_and_wheel_match(tree, tmp_path):
    wheel = tmp_path / "artifact.whl"
    # Keep the wheel outside the transferred tree.
    payload = {p.relative_to(tree).as_posix(): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    wheel = tmp_path.parent / (tmp_path.name + ".whl")
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in payload.items():
            archive.writestr(assets.PREFIX + name, content)
    assets.verify(tree, "0.44.7", SHA, wheel)


@pytest.mark.parametrize("kind", ["changed", "extra", "missing", "missing-proof", "symlink"])
def test_transfer_changes_are_refused(tree, kind):
    if kind == "changed":
        (tree / "assets/index.js").write_text("stale bytes")
    elif kind == "extra":
        (tree / "assets/extra.js").write_text("unqualified bytes")
    elif kind == "missing":
        (tree / "assets/workspace.js").unlink()
    elif kind == "missing-proof":
        (tree / assets.PROOF).unlink()
    else:
        (tree / "assets/link.js").symlink_to(tree / "assets/index.js")
    with pytest.raises((ValueError, FileNotFoundError)):
        assets.verify(tree, "0.44.7", SHA)


@pytest.mark.parametrize("version,sha", [("0.44.6", SHA), ("0.44.7", "b" * 40)])
def test_other_source_or_version_is_refused(tree, version, sha):
    with pytest.raises(ValueError, match="source/version mismatch"):
        assets.verify(tree, version, sha)


def test_wheel_with_old_frontend_is_refused(tree, tmp_path):
    wheel = tmp_path.parent / (tmp_path.name + "-stale.whl")
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(assets.PREFIX + "assets/index.js", "old code")
    with pytest.raises(ValueError, match="wheel frontend differs"):
        assets.verify(tree, "0.44.7", SHA, wheel)


def test_workflow_transfers_hidden_proof_and_manifest_before_build():
    import yaml
    jobs = yaml.safe_load((SCRIPT.parents[1] / "workflows/pypi-publish-and-github-release-on-tag.yml").read_text())["jobs"]
    upload = next(step for step in jobs["frontend"]["steps"] if step.get("uses") == "actions/upload-artifact@v4")
    download = next(step for step in jobs["build"]["steps"] if step.get("uses") == "actions/download-artifact@v4")
    assert upload["with"]["name"] == download["with"]["name"] == "qualified-frontend"
    assert upload["with"]["include-hidden-files"] is True
    steps = jobs["build"]["steps"]
    assert steps.index(download) < next(i for i,s in enumerate(steps) if "build-in-sif.sh" in s.get("run", ""))
