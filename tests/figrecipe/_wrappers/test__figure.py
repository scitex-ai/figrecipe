"""Tests for figrecipe._wrappers._figure (incl. auto panel-label size/family)."""

import string

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest


def test_import__wrappers__figure_module():
    # Arrange
    module_path = "figrecipe._wrappers._figure"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _scitex_panel_label_figure():
    """Build a 1x2 SCITEX figure with auto panel labels; return (mpl_fig, ax0)."""
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, axes = fr.subplots(
        1, 2, axes_width_mm=90, axes_height_mm=70, panel_labels=True
    )
    for ax in axes:
        ax.plot([0, 1, 2], [0, 1, 2])
        ax.set_xlabel("x")
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    mpl_fig.canvas.draw()
    return mpl_fig, mpl_fig.axes[0]


def _panel_label_text(mpl_fig):
    """Return the first auto panel-label (single uppercase letter) Text."""
    for a in mpl_fig.axes:
        for t in a.texts:
            if t.get_text() in set(string.ascii_uppercase):
                return t
    return None


def test_auto_panel_labels_use_panel_label_pt_size():
    # Arrange
    mpl_fig, _ax0 = _scitex_panel_label_figure()

    # Act
    label = _panel_label_text(mpl_fig)

    # Assert: SCITEX panel_label_pt is 10 (NOT title_pt=8).
    assert label.get_fontsize() == 10.0
    plt.close(mpl_fig)


def test_auto_panel_labels_match_body_font_family():
    # Arrange
    mpl_fig, ax0 = _scitex_panel_label_figure()

    # Act
    label = _panel_label_text(mpl_fig)
    same_family = label.get_fontfamily() == ax0.xaxis.label.get_fontfamily()

    # Assert
    assert same_family
    plt.close(mpl_fig)
