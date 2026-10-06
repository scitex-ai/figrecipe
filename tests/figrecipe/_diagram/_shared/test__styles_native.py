"""Smoke import mirror for figrecipe._diagram._shared._styles_native.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest

from figrecipe._diagram._shared._styles_native import get_emphasis_style


def test_import__diagram__shared__styles_native_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._diagram._shared._styles_native'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


class TestContextEmphasis:
    """manim opacity-layering port: a dimmed 'context' level below 'muted'."""

    def test_context_emphasis_is_dimmer_than_muted(self):
        # Arrange
        # Act
        context = get_emphasis_style("context")
        muted = get_emphasis_style("muted")
        # Assert -- context fill is closer to white than muted fill.
        def _lum(hex_color):
            h = hex_color.lstrip("#")
            return sum(int(h[i : i + 2], 16) for i in (0, 2, 4))

        assert _lum(context["fill"]) > _lum(muted["fill"])
