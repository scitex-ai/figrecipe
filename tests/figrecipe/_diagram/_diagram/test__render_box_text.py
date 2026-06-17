"""Per-line vertical stacking for diagram box text (NeuroVista Ask 4).

A box with a multi-line title and a multi-line subtitle used to render the
subtitle on top of the title because the layout counted *items* rather than
*visual lines* (an item with an embedded ``\\n`` occupies two rows). These
tests pin the per-line layout: each text artist lands at a distinct y and
consecutive multi-line items do not overlap.
"""

from __future__ import annotations

import pytest


def _render_multiline_box():
    """Render a box with a 2-line title + 2-line subtitle + 2 content lines.

    Returns the matplotlib axes carrying the rendered text artists.
    """
    import matplotlib

    matplotlib.use("Agg")
    from figrecipe.diagram import Diagram

    diag = Diagram(title=None, width_mm=60, height_mm=40)
    diag.add_box(
        "pha",
        "Phase\nfilterbank",
        subtitle="25 bands\n2-30 Hz",
        content=["line one", "line two"],
        emphasis="primary",
        x_mm=30,
        y_mm=20,
        width_mm=44,
        height_mm=34,
        padding_mm=3.0,
    )
    _fig, ax = diag.render()
    return ax


def _text_y(ax, text):
    """Return the y data coordinate of the artist whose text equals ``text``."""
    return next(t.get_position()[1] for t in ax.texts if t.get_text() == text)


def test_multiline_box_emits_one_text_artist_per_item():
    # Arrange
    pytest.importorskip("figrecipe")
    ax = _render_multiline_box()
    # Act
    n_text_artists = len(ax.texts)
    # Assert
    assert n_text_artists == 4


def test_multiline_box_text_artists_have_distinct_y_positions():
    # Arrange
    pytest.importorskip("figrecipe")
    ax = _render_multiline_box()
    # Act
    distinct_y = {round(t.get_position()[1], 3) for t in ax.texts}
    # Assert
    assert len(distinct_y) == len(ax.texts)


def test_two_line_title_reserves_two_rows_below_itself():
    # Arrange
    pytest.importorskip("figrecipe")
    ax = _render_multiline_box()
    # The 2-line title pushes the subtitle down by ~2 single-line row pitches,
    # whereas two single-line content rows sit ~1 pitch apart. Counting items
    # (the old bug) spaced every item by 1 pitch -> ratio ~1.0 -> the 2-line
    # title overflowed onto the subtitle.
    single_row_pitch = _text_y(ax, "line one") - _text_y(ax, "line two")
    # Act
    title_to_subtitle = _text_y(ax, "Phase\nfilterbank") - _text_y(
        ax, "25 bands\n2-30 Hz"
    )
    # Assert
    assert title_to_subtitle == pytest.approx(2 * single_row_pitch, rel=0.05)
