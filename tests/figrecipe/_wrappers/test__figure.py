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


def _scitex_titled_panel_label_figure(tmp_path):
    """Build+save a 1x2 SCITEX figure with auto labels AND axes titles.

    Titles are set via ``set_xyt`` AFTER ``panel_labels=True`` (mirroring real
    usage), then the figure is saved so the title-clearance finalizer runs.
    Returns the real matplotlib figure.
    """
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, axes = fr.subplots(
        1, 2, axes_width_mm=90, axes_height_mm=70, panel_labels=True
    )
    for ax in axes:
        ax.plot([0, 1], [0, 1])
        ax.set_xyt("x", "y", "A Long Panel Title")
    fr.save(fig, str(tmp_path / "fig.png"))
    return fig._fig if hasattr(fig, "_fig") else fig


def _max_label_title_band_intersection(mpl_fig):
    """Largest vertical-band overlap (device px) of a panel label and its title.

    The auto label is anchored at the left (x=-0.1) while the title is centred,
    so a fixed-y label that sits ON the title shares the title's VERTICAL band
    even when their x-ranges do not cross. Measuring the y-band intersection
    therefore captures the "label rendered on the title" defect that the
    title-clearance fix removes. Returns the worst (max) overlap; 0.0 means
    every label sits cleanly above its title.
    """
    renderer = mpl_fig.canvas.get_renderer()
    worst = 0.0
    for a in mpl_fig.axes:
        label = None
        for t in a.texts:
            if t.get_text() in set(string.ascii_uppercase):
                label = t
        if label is None or not a.get_title():
            continue
        lb = label.get_window_extent(renderer)
        tb = a.title.get_window_extent(renderer)
        worst = max(worst, max(0.0, min(lb.y1, tb.y1) - max(lb.y0, tb.y0)))
    return worst


def test_auto_panel_labels_do_not_overlap_axes_title(tmp_path):
    # Arrange
    mpl_fig = _scitex_titled_panel_label_figure(tmp_path)
    # Act
    band_overlap = _max_label_title_band_intersection(mpl_fig)
    # Assert
    assert band_overlap == 0.0
