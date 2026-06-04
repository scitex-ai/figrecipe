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

AAA-marked, single-assertion per parametrized leg (STX-TQ002 / TQ006 /
TQ007). The value-splitting is extracted into a helper so the test body
has no top-level ``if``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import List, Tuple

import pytest

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = pytest.importorskip("tomli")  # type: ignore[assignment]


def _read_entry_points() -> dict:
    """Return ``{group: {name: value}}`` from figrecipe's pyproject.toml.

    Discovered by walking up from this test file to the repo root.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pyproject.toml"
        if not candidate.exists():
            continue
        with candidate.open("rb") as fh:
            data = tomllib.load(fh)
        if data.get("project", {}).get("name") == "figrecipe":
            return data.get("project", {}).get("entry-points", {})
    return {}


def _value_pairs() -> List[Tuple[str, str, str]]:
    """Yield (group, name, value) for every entry point declared."""
    out: List[Tuple[str, str, str]] = []
    for group, entries in _read_entry_points().items():
        for name, value in entries.items():
            out.append((group, name, value))
    return out


def _resolve(value: str):
    """Resolve a ``<module>[:<attr>]`` entry-point value.

    Extracted so the test body has no top-level ``if`` (STX-TQ006).
    Returns the module itself when no attr suffix is present; otherwise
    returns ``getattr(module, attr)``.
    """
    parts = value.split(":", 1)
    mod = importlib.import_module(parts[0])
    return getattr(mod, parts[1]) if len(parts) == 2 else mod


_PAIRS = _value_pairs()


@pytest.mark.parametrize(
    "group,name,value",
    _PAIRS,
    ids=[f"{g}::{n}" for g, n, _ in _PAIRS] or ["no-entry-points"],
)
def test_every_entry_point_resolves_to_real_attribute(group, name, value):
    # Arrange
    pytest.importorskip("figrecipe")
    # Act
    resolved = _resolve(value)
    # Assert
    assert resolved is not None
