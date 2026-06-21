"""Diagram fonts are read from the active figrecipe style (not hardcoded).

Diagrams used to hardcode ``FONT_CONFIG`` (title 11 / node 9 / edge 7) and
ignore the active style, so a diagram title (11pt) clashed with SCITEX figure
titles (8pt). These guards pin the new behaviour: diagram text sizes come from
the SAME source regular figures read (``to_subplots_kwargs`` over the active
style), with the role -> point-size mapping

    title_size      <- fonts_title_pt       (SCITEX 8)
    node_size       <- fonts_axis_label_pt  (SCITEX 7)
    edge_label_size <- fonts_legend_pt      (SCITEX 6)

and the FONT_CONFIG constants kept only as the no-style fallback.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe.diagram import Diagram


def _title_fontsize(ax) -> float:
    """Return the fontsize of the rendered diagram-title text artist."""
    return next(t.get_fontsize() for t in ax.texts if t.get_text() == "My Title")


def _label_fontsize(ax, label: str) -> float:
    """Return the fontsize of the rendered box-label text artist ``label``."""
    return next(t.get_fontsize() for t in ax.texts if t.get_text() == label)


def _render_titled_diagram():
    """Render a small titled diagram with two labelled boxes; return its axes."""
    diag = Diagram(title="My Title", width_mm=120, height_mm=60)
    diag.add_box("a", title="Alpha", x_mm=30, y_mm=30, width_mm=30, height_mm=18)
    diag.add_box("b", title="Beta", x_mm=90, y_mm=30, width_mm=30, height_mm=18)
    _fig, ax = diag.render()
    return ax


def test_diagram_title_size_equals_active_style_title_pt():
    # Arrange
    fr.load_style("SCITEX")
    expected = fr.STYLE.fonts.title_pt
    # Act
    ax = _render_titled_diagram()
    # Assert
    assert _title_fontsize(ax) == expected


def test_box_label_size_equals_active_style_axis_label_pt():
    # Arrange
    fr.load_style("SCITEX")
    expected = fr.STYLE.fonts.axis_label_pt
    # Act
    ax = _render_titled_diagram()
    # Assert
    assert _label_fontsize(ax, "Alpha") == expected


def test_style_title_pt_override_propagates_to_diagram_title():
    # Arrange
    fr.load_style("SCITEX")
    fr.STYLE.fonts.title_pt = 20
    try:
        # Act
        size = _title_fontsize(_render_titled_diagram())
    finally:
        fr.load_style("SCITEX")
    # Assert
    assert size == 20


def test_no_active_style_returns_font_config_fallback_values():
    # Arrange
    from figrecipe._diagram._shared import _styles_native as sn

    fr.load_style(None)
    sn._FALLBACK_WARNED = True  # silence the one-shot warning for this check
    try:
        # Act
        resolved = sn.resolve_font_config()
    finally:
        fr.load_style("SCITEX")
    # Assert
    assert resolved["title_size"] == sn.FONT_CONFIG["title_size"]


def test_no_active_style_warns_about_font_config_fallback():
    # Arrange
    import warnings

    from figrecipe._diagram._shared import _styles_native as sn

    fr.load_style(None)
    sn._FALLBACK_WARNED = False
    # Act
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sn.resolve_font_config()
    finally:
        fr.load_style("SCITEX")
    # Assert
    assert any("FONT_CONFIG fallback" in str(w.message) for w in caught)
