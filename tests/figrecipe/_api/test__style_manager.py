"""Smoke import mirror for figrecipe._api._style_manager.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__api__style_manager_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._api._style_manager'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_apply_style_rejects_non_axes_first_positional():
    # Arrange
    import matplotlib.pyplot as plt
    from figrecipe._api._style_manager import apply_style

    # Act & Assert: passing the preset name (a str) where the Axes goes must
    # fail loud at the boundary, not crash deep inside (#160).
    with pytest.raises(TypeError, match="must be a matplotlib Axes"):
        apply_style("SCITEX_STYLE")
    plt.close("all")


def test_apply_style_accepts_a_real_axes():
    # Arrange
    import matplotlib.axes
    import matplotlib.pyplot as plt
    from figrecipe._api._style_manager import apply_style

    fig, ax = plt.subplots()
    try:
        # Act
        result = apply_style(ax)
        # Assert: returns the trace line width in points.
        assert isinstance(result, float)
        assert result > 0
    finally:
        plt.close(fig)


def test_apply_style_accepts_figrecipe_wrapped_axes():
    # Arrange
    import matplotlib.pyplot as plt
    import figrecipe as fr

    # fr.subplots() returns a RecordingAxes composition wrapper (not an Axes
    # subclass); apply_style must unwrap it, not reject it (#160 review).
    fig, ax = fr.subplots()
    try:
        # Act
        result = fr.apply_style(ax)
        # Assert
        assert isinstance(result, float)
        assert result > 0
    finally:
        plt.close("all")
