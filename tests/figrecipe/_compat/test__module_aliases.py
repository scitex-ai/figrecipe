"""Behavioural tests for figrecipe._compat._module_aliases.

Each test is AAA-marked, single-assertion (STX-TQ002 / STX-TQ007). The
seam under test is the sys.modules registration installed by figrecipe's
top-level __init__; tests assert observable properties (resolution +
warning emission) rather than internal state.
"""

from __future__ import annotations

import importlib
import sys
import warnings

import pytest

pytest.importorskip("figrecipe")


def test_old_validator_path_resolves_to_a_module():
    # Arrange
    import figrecipe  # noqa: F401 — ensure aliases are installed
    # Act
    mod = importlib.import_module("figrecipe._validator")
    # Assert
    assert mod is not None


def test_old_validator_path_exposes_same_validation_result_as_new_path():
    # Arrange
    import figrecipe  # noqa: F401
    new_mod = importlib.import_module("figrecipe._quality._validator")
    # Act
    old_mod = importlib.import_module("figrecipe._validator")
    # Assert
    assert old_mod.ValidationResult is new_mod.ValidationResult


def test_old_linter_plugin_path_exposes_get_plugin_function():
    # Arrange
    import figrecipe  # noqa: F401
    # Act
    from figrecipe._linter_plugin import get_plugin
    # Assert
    assert callable(get_plugin)


def test_old_axis_range_alignment_path_exposes_check_function():
    # Arrange
    import figrecipe  # noqa: F401
    # Act
    from figrecipe._axis_range_alignment import check_axis_range_alignment
    # Assert
    assert callable(check_axis_range_alignment)


def test_old_axis_alignment_checker_path_exposes_checker_class():
    # Arrange
    import figrecipe  # noqa: F401
    # Act
    from figrecipe._axis_alignment_checker import AxisAlignmentChecker
    # Assert
    assert AxisAlignmentChecker is not None


def test_first_access_to_old_path_emits_deprecation_warning():
    # Arrange — drop the cached alias so the proxy's first-fire branch runs.
    # Use a SEPARATE module path that test_*_resolves_to_a_module
    # doesn't touch (so each test stays single-assertion / isolated).
    import figrecipe  # noqa: F401
    sys.modules.pop("figrecipe._linter_plugin", None)
    from figrecipe._compat import install_module_aliases
    install_module_aliases()
    proxy = sys.modules["figrecipe._linter_plugin"]
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = proxy.get_plugin  # trigger __getattr__
    # Assert
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_install_module_aliases_is_idempotent():
    # Arrange
    import figrecipe  # noqa: F401
    from figrecipe._compat import install_module_aliases
    first = sys.modules.get("figrecipe._validator")
    # Act
    install_module_aliases()
    second = sys.modules.get("figrecipe._validator")
    # Assert
    assert first is second
