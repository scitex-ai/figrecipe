"""Smoke import mirror for figrecipe._wrappers._panel_labels.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import matplotlib
import pytest

import figrecipe._wrappers._panel_labels as _panel_labels


def test_import__wrappers__panel_labels_module():
    # Arrange
    module_path = "figrecipe._wrappers._panel_labels"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_panel_label_renders_given_label_text_on_recording_axes():
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()

    # Act
    result = _panel_labels.panel_label(ax, "A")

    # Assert
    assert result.get_text() == "A"


def test_panel_label_returns_matplotlib_text_artist_instance():
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()

    # Act
    result = _panel_labels.panel_label(ax, "A")

    # Assert
    assert isinstance(result, matplotlib.text.Text)
