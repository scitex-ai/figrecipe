"""Tests for figrecipe._recorder._panel_id.

Pure-function unit tests, no matplotlib. Each test follows
Arrange / Act / Assert with one assertion and a >=3-word name that
describes the behaviour.
"""

from __future__ import annotations

from figrecipe._recorder._panel_id import panel_label_for_position


def test_top_left_is_panel_a_in_2x3_grid():
    # Arrange — 2 rows × 3 cols, top-left position.

    # Act
    label = panel_label_for_position(0, 0, nrows=2, ncols=3)

    # Assert
    assert label == "A"


def test_top_right_is_panel_c_in_2x3_grid():
    # Arrange — top row, last column.

    # Act
    label = panel_label_for_position(0, 2, nrows=2, ncols=3)

    # Assert
    assert label == "C"


def test_bottom_left_wraps_to_d_in_2x3_grid():
    # Arrange — second row, first column. Row-major index = 1*3 + 0 = 3.

    # Act
    label = panel_label_for_position(1, 0, nrows=2, ncols=3)

    # Assert
    assert label == "D"


def test_bottom_right_is_panel_f_in_2x3_grid():
    # Arrange — last row, last column.

    # Act
    label = panel_label_for_position(1, 2, nrows=2, ncols=3)

    # Assert
    assert label == "F"


def test_single_panel_returns_none_label():
    # Arrange — 1x1 figure: no panel suffix should be applied.

    # Act
    label = panel_label_for_position(0, 0, nrows=1, ncols=1)

    # Assert
    assert label is None


def test_missing_grid_shape_returns_none_label():
    # Arrange — legacy recipe without nrows/ncols recorded.

    # Act
    label = panel_label_for_position(0, 0, nrows=None, ncols=None)

    # Assert
    assert label is None


def test_position_beyond_z_returns_none_label():
    # Arrange — 27-th panel exceeds the A..Z alphabet.

    # Act
    label = panel_label_for_position(0, 26, nrows=1, ncols=27)

    # Assert
    assert label is None


def test_two_by_two_grid_labels_a_b_c_d_in_row_major():
    # Arrange — collect all four labels of a 2x2 grid.

    # Act
    labels = [
        panel_label_for_position(r, c, nrows=2, ncols=2)
        for r in range(2)
        for c in range(2)
    ]

    # Assert
    assert labels == ["A", "B", "C", "D"]


# EOF
