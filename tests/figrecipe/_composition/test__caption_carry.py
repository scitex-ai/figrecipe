"""Tests for figrecipe._composition._caption_carry (panel-caption carry-forward)."""

from figrecipe._composition._caption_carry import (
    auto_panel_captions_grid,
    auto_panel_captions_seq,
)


def test_grid_assembles_row_major_from_source_captions():
    # Arrange
    caps = {(0, 0): "A cap", (0, 1): "B cap"}
    # Act
    out = auto_panel_captions_grid(caps, nrows=1, ncols=2)
    # Assert
    assert out == ["A cap", "B cap"]


def test_grid_fills_missing_cells_with_empty_string():
    # Arrange: only the first cell carries a caption.
    caps = {(0, 0): "only A", (0, 1): None}
    # Act
    out = auto_panel_captions_grid(caps, nrows=1, ncols=2)
    # Assert
    assert out == ["only A", ""]


def test_grid_returns_none_when_no_source_has_caption():
    # Arrange
    caps = {(0, 0): None, (0, 1): "   "}
    # Act
    out = auto_panel_captions_grid(caps, nrows=1, ncols=2)
    # Assert
    assert out is None


def test_seq_assembles_in_source_order_when_one_axes_each():
    # Arrange
    # Act
    out = auto_panel_captions_seq(["a", "b", "c"], axis_counts=[1, 1, 1])
    # Assert
    assert out == ["a", "b", "c"]


def test_seq_declines_when_any_source_has_multiple_axes():
    # Arrange: a multi-subplot source breaks the one-caption-per-axes mapping.
    # Act
    out = auto_panel_captions_seq(["a", "b"], axis_counts=[1, 2])
    # Assert
    assert out is None


def test_seq_returns_none_when_no_caption_present():
    # Arrange
    # Act
    out = auto_panel_captions_seq([None, ""], axis_counts=[1, 1])
    # Assert
    assert out is None
