"""Entry-point regression guard for figrecipe.

Lead msg b4e3dc7e: when `_quality/` moved 4 private modules in #141, the
pyproject.toml entry-point string had to be updated in lockstep (because
rename-symbols doesn't rewrite TOML). It was, but the silent-skip failure
mode (where the aggregator imports a moved module via the entry point and
the dotted path now points nowhere) is the worst-class bug — no error
surfaces, the linter rules just silently stop firing ecosystem-wide.

This test parses every ``[project.entry-points.*]`` table in figrecipe's
pyproject.toml and asserts each ``<module>:<attr>`` value resolves to a
real importable attribute. New entry points + future moves are covered
automatically without extra test maintenance.

AAA-marked, single-assertion per test (STX-TQ002 / STX-TQ007).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = pytest.importorskip("tomli")  # type: ignore[assignment]


def _read_entry_points() -> dict[str, dict[str, str]]:
    """Return ``{group: {name: value}}`` from figrecipe's pyproject.toml.

    Discovered by walking up from this test file to the repo root.
    """
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.exists() and candidate.read_text(encoding="utf-8").startswith(
            "[build-system]"
        ) or (
            candidate.exists() and 'name = "figrecipe"' in candidate.read_text(encoding="utf-8")
        ):
            with candidate.open("rb") as fh:
                data = tomllib.load(fh)
            return (
                data.get("project", {})
                .get("entry-points", {})
            )
    return {}


def _value_pairs() -> list[tuple[str, str, str]]:
    """Yield (group, name, value) tuples for every entry point declared."""
    out = []
    for group, entries in _read_entry_points().items():
        for name, value in entries.items():
            out.append((group, name, value))
    return out


@pytest.mark.parametrize(
    "group,name,value",
    _value_pairs(),
    ids=[f"{g}::{n}" for g, n, _ in _value_pairs()] or ["no-entry-points"],
)
def test_every_entry_point_resolves_to_real_attribute(group, name, value):
    # Arrange
    if not value:
        pytest.skip("no entry points declared")
    if ":" in value:
        module_path, attr = value.split(":", 1)
    else:
        module_path, attr = value, None
    # Act
    mod = importlib.import_module(module_path)
    resolved = getattr(mod, attr) if attr else mod
    # Assert
    assert resolved is not None
