"""Build a real wheel with ignored npm files that are explicitly re-included."""

import tarfile
import zipfile
from pathlib import Path

from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder


def test_npm_dependency_config_cannot_leak_into_leaf_wheel(tmp_path):
    # Arrange
    contract = {}
    # Act
    project = Path(__file__).resolve().parents[2]
    (tmp_path / "pyproject.toml").write_bytes((project / "pyproject.toml").read_bytes())
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
