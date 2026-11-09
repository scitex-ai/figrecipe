"""Build a real wheel with ignored npm files that are explicitly re-included."""

import tarfile
import shutil
import zipfile
from pathlib import Path

from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder


def _copy_cli_dictionary(project, destination):
    source = project / ".scitex/dev/cli-audit-dict.yaml"
    target = destination / ".scitex/dev/cli-audit-dict.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def test_npm_dependency_config_cannot_leak_into_leaf_wheel(tmp_path):
    # Arrange
    contract = {}
    # Act
    project = Path(__file__).resolve().parents[2]
    (tmp_path / "pyproject.toml").write_bytes((project / "pyproject.toml").read_bytes())
    _copy_cli_dictionary(project, tmp_path)
    (tmp_path / "README.md").write_text("Synthetic packaging fixture\n")
    (tmp_path / "LICENSE").write_text("Synthetic packaging fixture\n")
    (tmp_path / ".gitignore").write_text(
        "node_modules/\n!pyproject.toml\n!*.yaml\n!.gitkeep\n"
    )
    package = tmp_path / "src/figrecipe"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("__version__ = '0.34.2'\n")
    for relative in (
        "_django/frontend/node_modules/@scitex/sdk/pyproject.toml",
        "_django/frontend/node_modules/@scitex/sdk/.readthedocs.yaml",
        "_django/frontend/node_modules/@scitex/sdk/docs/sphinx/_static/.gitkeep",
        "_django/frontend/node_modules/@scitex/ui/pyproject.toml",
        "_django/frontend/node_modules/@scitex/ui/.readthedocs.yaml",
        "_django/frontend/node_modules/@scitex/ui/docs/sphinx/_static/.gitkeep",
        "_django/static/figrecipe/assets/workspace.js",
        "_django/static/figrecipe/assets/workspace.js.map",
        "_django/templates/figrecipe/workspace_partial.html",
    ):
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic member\n")
    wheel = next(WheelBuilder(str(tmp_path)).build(directory=str(tmp_path / "dist")))
    with zipfile.ZipFile(wheel) as archive:
        contract[
            "1: not any(('/node_modules/' in name for name in archive.namelist()))"
        ] = bool(not any("/node_modules/" in name for name in archive.namelist()))
        contract[
            "2: archive.read('figrecipe/_django/static/figrecipe/assets/workspace.js') == b'Synthetic member\\n'"
        ] = bool(
            archive.read("figrecipe/_django/static/figrecipe/assets/workspace.js")
            == b"Synthetic member\n"
        )
        contract[
            "3: archive.read('figrecipe/_django/static/figrecipe/assets/workspace.js.map') == b'Synthetic member\\n'"
        ] = bool(
            archive.read("figrecipe/_django/static/figrecipe/assets/workspace.js.map")
            == b"Synthetic member\n"
        )
        contract[
            "4: archive.read('figrecipe/_django/templates/figrecipe/workspace_partial.html') == b'Synthetic member\\n'"
        ] = bool(
            archive.read("figrecipe/_django/templates/figrecipe/workspace_partial.html")
            == b"Synthetic member\n"
        )
    # Assert
    assert all(contract.values()), contract


def test_npm_install_stays_out_of_sdist_while_authored_build_inputs_ship(tmp_path):
    # Arrange
    project = Path(__file__).resolve().parents[2]
    (tmp_path / "pyproject.toml").write_bytes((project / "pyproject.toml").read_bytes())
    _copy_cli_dictionary(project, tmp_path)
    (tmp_path / "README.md").write_text("Owned packaging fixture\n")
    (tmp_path / "LICENSE").write_text("Owned packaging fixture\n")
    (tmp_path / ".gitignore").write_text("dist/\n")
    frontend = tmp_path / "src/figrecipe/_django/frontend"
    frontend.mkdir(parents=True)
    (frontend / ".gitignore").write_text("node_modules/\n")
    payloads = {
        "src/main.tsx": b"export const authored = true;\n",
        "build-version.ts": b"export const buildOnlyVersion = true;\n",
        "package.json": (
            project / "src/figrecipe/_django/frontend/package.json"
        ).read_bytes(),
        "package-lock.json": (
            project / "src/figrecipe/_django/frontend/package-lock.json"
        ).read_bytes(),
        "node_modules/owned-dependency/native.node": b"Owned dependency fixture\n",
    }
    for relative, data in payloads.items():
        path = frontend / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    # Act
    archive_path = next(
        SdistBuilder(str(tmp_path)).build(directory=str(tmp_path / "dist"))
    )
    with tarfile.open(archive_path) as archive:
        members = archive.getnames()
        shipped = {}
        for relative in payloads:
            matches = [
                name for name in members if name.endswith("/frontend/" + relative)
            ]
            shipped[relative] = (
                archive.extractfile(matches[0]).read() if matches else None
            )
    expected = dict(payloads, **{"node_modules/owned-dependency/native.node": None})
    # Assert
    assert shipped == expected


def test_cli_dictionary_survives_source_and_rebuilt_wheel(tmp_path):
    # Arrange
    project = Path(__file__).resolve().parents[2]
    (tmp_path / "pyproject.toml").write_bytes((project / "pyproject.toml").read_bytes())
    _copy_cli_dictionary(project, tmp_path)
    (tmp_path / "README.md").write_text("Owned dictionary packaging fixture\n")
    (tmp_path / "LICENSE").write_text("Owned dictionary packaging fixture\n")
    (tmp_path / ".gitignore").write_text("dist/\n.scitex/\n")
    package = tmp_path / "src/figrecipe"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    private = tmp_path / ".scitex/private/runtime/canary.key"
    private.parent.mkdir(parents=True)
    private.write_text("SYNTHETIC NONSECRET PRIVATE-STATE CANARY\n")
    expected = (project / ".scitex/dev/cli-audit-dict.yaml").read_bytes()
    shipped = {}

    # Act
    wheel = next(WheelBuilder(str(tmp_path)).build(directory=str(tmp_path / "dist")))
    with zipfile.ZipFile(wheel) as archive:
        name = "figrecipe/_cli_audit_dict.yaml"
        shipped["wheel"] = archive.read(name) if name in archive.namelist() else None
        shipped["wheel-private"] = any("canary.key" in n for n in archive.namelist())
    source = next(SdistBuilder(str(tmp_path)).build(directory=str(tmp_path / "dist")))
    unpacked = tmp_path / "unpacked"
    with tarfile.open(source) as archive:
        matches = [
            m
            for m in archive.getmembers()
            if m.name.endswith("/.scitex/dev/cli-audit-dict.yaml")
        ]
        shipped["source"] = archive.extractfile(matches[0]).read() if matches else None
        shipped["source-private"] = any("canary.key" in n for n in archive.getnames())
        archive.extractall(unpacked, filter="data")
    rebuilt_root = next(unpacked.iterdir())
    rebuilt = next(
        WheelBuilder(str(rebuilt_root)).build(directory=str(tmp_path / "rebuilt"))
    )
    with zipfile.ZipFile(rebuilt) as archive:
        name = "figrecipe/_cli_audit_dict.yaml"
        shipped["rebuilt"] = archive.read(name) if name in archive.namelist() else None
        shipped["rebuilt-private"] = any("canary.key" in n for n in archive.namelist())

    # Assert
    assert shipped == {
        "wheel": expected,
        "source": expected,
        "rebuilt": expected,
        "wheel-private": False,
        "source-private": False,
        "rebuilt-private": False,
    }
