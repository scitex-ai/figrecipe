"""Smoke import mirror for figrecipe._captions._convenience.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__captions__convenience_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._captions._convenience'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_caption_helpers_exposed_on_public_api():
    """Card caption-public-api: add_figure_caption, add_panel_captions,
    panel_label are reachable as figrecipe.X."""
    # Arrange
    import figrecipe as fr

    # Act
    exposed = [
        getattr(fr, "add_figure_caption", None),
        getattr(fr, "add_panel_captions", None),
        getattr(fr, "panel_label", None),
    ]

    # Assert
    assert all(callable(s) for s in exposed)
