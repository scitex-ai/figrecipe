"""Tests for the mm column grid (0.5 / 1 / 1.5 / 2 columns).

Pure arithmetic, no figures. One assertion per test, AAA markers.

The tests are written as INVARIANTS rather than as expected literals wherever
possible: a grid whose numbers merely match a hardcoded list can still be
internally inconsistent, and inconsistency is the whole failure this grid exists
to prevent.
"""

from __future__ import annotations

import pytest

from figrecipe._composition._column_grid import (
    COLUMN_STEPS,
    CONTENT_WIDTH_MM,
    DEFAULT_GAP_MM,
    column_grid_mm,
    columns_for_width,
    snap_to_column_grid,
)


# ---------------------------------------------------------------------------
# the invariants that make it a GRID rather than four arbitrary numbers
# ---------------------------------------------------------------------------


def test_two_single_columns_plus_a_gutter_fill_the_content_width():
    # Arrange: the load-bearing invariant. If this fails, a two-panel row does
    # not fit the page and every layout built on the grid is wrong.
    grid = column_grid_mm()
    # Act
    total = grid[1.0] * 2 + DEFAULT_GAP_MM
    # Assert
    assert total == pytest.approx(CONTENT_WIDTH_MM)


def test_two_half_columns_plus_a_gutter_make_one_column():
    # Arrange
    grid = column_grid_mm()
    # Act
    total = grid[0.5] * 2 + DEFAULT_GAP_MM
    # Assert
    assert total == pytest.approx(grid[1.0])


def test_a_column_plus_a_gutter_plus_a_half_makes_one_and_a_half():
    # Arrange
    grid = column_grid_mm()
    # Act
    total = grid[1.0] + DEFAULT_GAP_MM + grid[0.5]
    # Assert
    assert total == pytest.approx(grid[1.5])


def test_the_full_span_is_exactly_the_content_width():
    # Arrange: a full-width panel has no neighbour, so it gives up no gutter.
    grid = column_grid_mm()
    # Act
    actual = grid[2.0]
    # Assert
    assert actual == pytest.approx(CONTENT_WIDTH_MM)


def test_the_grid_covers_every_declared_step():
    # Arrange
    expected = set(COLUMN_STEPS)
    # Act
    actual = set(column_grid_mm().keys())
    # Assert
    assert actual == expected


def test_widths_increase_with_column_count():
    # Arrange
    grid = column_grid_mm()
    # Act
    widths = [grid[s] for s in sorted(grid)]
    # Assert
    assert widths == sorted(widths)


# ---------------------------------------------------------------------------
# cross-module consistency — the grid and the width check must agree about
# what fits, or one warns about figures the other calls legal
# ---------------------------------------------------------------------------


def test_the_content_width_matches_the_compose_width_limit():
    # Arrange
    from figrecipe._quality._compose_width import COMPOSE_MAX_WIDTH_MM

    expected = COMPOSE_MAX_WIDTH_MM
    # Act
    actual = CONTENT_WIDTH_MM
    # Assert
    assert actual == expected


# ---------------------------------------------------------------------------
# snapping
# ---------------------------------------------------------------------------


def test_snaps_to_the_nearest_legal_width():
    # Arrange: 95mm is nearest the 1-column 89mm.
    width = 95.0
    # Act
    actual = snap_to_column_grid(width)
    # Assert
    assert actual == pytest.approx(column_grid_mm()[1.0])


def test_snaps_a_narrow_panel_to_the_half_column():
    # Arrange
    width = 40.0
    # Act
    actual = snap_to_column_grid(width)
    # Assert
    assert actual == pytest.approx(column_grid_mm()[0.5])


def test_does_not_snap_wider_than_the_content_width():
    # Arrange: past the content width is the case the page silently rescales,
    # so the snap must clamp rather than hand back something unprintable.
    width = 200.0
    # Act
    actual = snap_to_column_grid(width)
    # Assert
    assert actual == pytest.approx(CONTENT_WIDTH_MM)


def test_widening_past_the_content_width_is_opt_in():
    # Arrange: the card allows wide panels as deliberate exceptions.
    width = 200.0
    # Act
    actual = snap_to_column_grid(width, allow_wider=True)
    # Assert
    assert actual == pytest.approx(width)


def test_an_exact_grid_width_snaps_to_itself():
    # Arrange
    width = column_grid_mm()[1.5]
    # Act
    actual = snap_to_column_grid(width)
    # Assert
    assert actual == pytest.approx(width)


# ---------------------------------------------------------------------------
# identifying a width — None means "off grid", not "closest is fine"
# ---------------------------------------------------------------------------


def test_identifies_the_column_count_of_a_grid_width():
    # Arrange
    width = column_grid_mm()[1.0]
    # Act
    actual = columns_for_width(width)
    # Assert
    assert actual == 1.0


def test_returns_none_for_an_off_grid_width():
    # Arrange: 120mm matches no step. Rounding it onto one would imply the
    # panel was on the grid when it is not.
    width = 120.0
    # Act
    actual = columns_for_width(width)
    # Assert
    assert actual is None


# ---------------------------------------------------------------------------
# the page is a parameter, not a constant
# ---------------------------------------------------------------------------


def test_a_custom_content_width_rescales_the_whole_grid():
    # Arrange: a journal with a wider text block.
    content = 240.0
    # Act
    grid = column_grid_mm(content_width_mm=content)
    # Assert
    assert grid[2.0] == pytest.approx(content)


def test_a_custom_gap_still_satisfies_the_two_column_invariant():
    # Arrange
    gap = 6.0
    # Act
    grid = column_grid_mm(gap_mm=gap)
    # Assert
    assert grid[1.0] * 2 + gap == pytest.approx(CONTENT_WIDTH_MM)
