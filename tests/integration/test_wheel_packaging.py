"""Build a real wheel with ignored npm files that are explicitly re-included."""

import zipfile
from pathlib import Path

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
