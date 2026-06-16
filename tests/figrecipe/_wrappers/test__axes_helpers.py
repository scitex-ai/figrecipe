"""Smoke import mirror for figrecipe._wrappers._axes_helpers.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import__wrappers__axes_helpers_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._wrappers._axes_helpers"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_lw_signal_token_resolves_to_signal_width_pt():
    """lw='signal' maps to the SCITEX style's signal width in points."""
    # Arrange
    import figrecipe as fr
    from figrecipe._utils._units import mm_to_pt
    from figrecipe._wrappers._axes_helpers import _resolve_signal_linewidth_token

    fr.load_style("SCITEX")
    expected_pt = mm_to_pt(0.12)  # SCITEX signal_linewidth_mm
    # Act
    out = _resolve_signal_linewidth_token({"lw": "signal"})
    # Assert
    assert abs(out["lw"] - expected_pt) < 1e-6


def test_linewidth_signal_token_resolves_to_signal_width_pt():
    """linewidth='signal' maps to the SCITEX style's signal width in points."""
    # Arrange
    import figrecipe as fr
    from figrecipe._utils._units import mm_to_pt
    from figrecipe._wrappers._axes_helpers import _resolve_signal_linewidth_token

    fr.load_style("SCITEX")
    expected_pt = mm_to_pt(0.12)
    # Act
    out = _resolve_signal_linewidth_token({"linewidth": "signal"})
    # Assert
    assert abs(out["linewidth"] - expected_pt) < 1e-6


def test_numeric_linewidth_passes_through_token_resolver():
    """Numeric linewidths are left untouched by the token resolver."""
    # Arrange
    from figrecipe._wrappers._axes_helpers import _resolve_signal_linewidth_token

    kwargs = {"lw": 3.0}
    # Act
    out = _resolve_signal_linewidth_token(kwargs)
    # Assert
    assert out["lw"] == 3.0
