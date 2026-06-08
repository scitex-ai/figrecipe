"""Smoke import mirror for figrecipe._wrappers._panel_labels.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import matplotlib
import matplotlib.pyplot as plt
import pytest

import figrecipe._wrappers._panel_labels as _panel_labels


def test_import__wrappers__panel_labels_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._wrappers._panel_labels'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_panel_label_returns_text():
    """Test that panel_label places a single label on an axes and returns the Text object."""
    fig, ax = plt.subplots()
    # Act
    result = _panel_labels.panel_label(ax, "A")
    # Assert
    assert isinstance(result, matplotlib.text.Text)
    assert result.get_text() == "A"
    plt.close(fig)
