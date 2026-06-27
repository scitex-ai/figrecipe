"""Tests for figrecipe._composition._layout_report (empty_cells + layout_report)."""

import matplotlib

matplotlib.use("Agg")

import pytest

from figrecipe._composition._layout_report import empty_cells, layout_report


def test_empty_cells_reports_the_blank_grid_cell():
    # Arrange: a 2x2 grid with only 3 of 4 cells supplied.
    sources = {(0, 0): "a", (0, 1): "b", (1, 0): "c"}
    # Act
    blanks = empty_cells((2, 2), sources)
    # Assert
    assert blanks == [(1, 1)]


def test_empty_cells_empty_when_grid_full():
    # Arrange
    sources = {(0, 0): "a", (0, 1): "b"}
    # Act
    blanks = empty_cells((1, 2), sources)
    # Assert
    assert blanks == []


def test_empty_cells_infers_layout_from_sources():
    # Arrange: no explicit layout; inferred 2x2 from max (row,col).
    sources = {(0, 0): "a", (1, 1): "b"}
    # Act
    blanks = empty_cells(None, sources)
    # Assert
    assert blanks == [(0, 1), (1, 0)]


def test_empty_cells_non_grid_layout_returns_empty():
    # Arrange: a tiled (list-of-rows) layout has no grid-cell concept.
    sources = {"A": "a", "B": "b"}
    # Act
    blanks = empty_cells([["A", "B"]], sources)
    # Assert
    assert blanks == []


def _panel(tmp_path, name):
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 2, 3], id="line")
    path = str(tmp_path / name)
    fr.save(fig, path)
    return path


def test_layout_report_flags_empty_region_in_underfilled_grid(tmp_path):
    # Arrange: 2x2 compose with only 3 panels -> one blank cell. (The under-fill
    # warning itself is asserted by test_compose_warns_on_underfilled_grid;
    # suppress it here so this test makes exactly one assertion.)
    import warnings

    import figrecipe as fr

    fr.set_manuscript_mode(False)
    a, b, c = (_panel(tmp_path, n) for n in ("a.yaml", "b.yaml", "c.yaml"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cfig, _ = fr.compose(layout=(2, 2), sources={(0, 0): a, (0, 1): b, (1, 0): c})
    # Act
    report = layout_report(cfig)
    # Assert: a blank region is detected for the missing panel.
    assert report["empty_regions"]


def test_compose_warns_on_underfilled_grid(tmp_path):
    # Arrange
    import figrecipe as fr

    fr.set_manuscript_mode(False)
    a, b, c = (_panel(tmp_path, n) for n in ("a2.yaml", "b2.yaml", "c2.yaml"))
    # Act
    # Assert
    with pytest.warns(UserWarning, match="empty cell"):
        fr.compose(layout=(2, 2), sources={(0, 0): a, (0, 1): b, (1, 0): c})
