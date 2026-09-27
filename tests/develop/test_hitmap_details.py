#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canvas hitmap hit-testing + element details panel.

Owner correction 2026-09-27: "hitmap" is canvas hit-testing, not a color
heatmap plot. Clicking a canvas element (cell/bar/point) must hit-select it
and show its details — value, row/column, series — in the Details panel.
The backend half is the ``element_details`` endpoint (values read off the
live artists the hitmap key names); the frontend half is the ElementDetails
section plus cell-picking clicks on already-selected matrix grids. Each
test makes a single assertion.
"""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe._django.services import EditorState

django = pytest.importorskip("django")

_FRONTEND = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "frontend"
    / "src"
)
_LOCALE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "locale"
    / "ja"
    / "LC_MESSAGES"
    / "djangojs.po"
)


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


class _GetRequest:
    def __init__(self, params):
        self.GET = params


def _editor_with_axes():
    import numpy as np

    fig, _ = fr.subplots(nrows=1, ncols=2)
    ax0, ax1 = fig.flat[0], fig.flat[1]
    ax0.bar(["a", "b", "c"], [1.5, 2.5, 0.5])
    ax0.scatter([1, 2, 3], [4, 5, 6], label="pts")
    ax1.imshow(np.arange(12, dtype=float).reshape(3, 4))
    editor = EditorState(fig=fig)
    editor._color_map = {
        "ax0_bar1": {
            "type": "bar",
            "label": "bar_0_bar1",
            "ax_index": 0,
            "call_id": "bar_0",
        }
    }
    return editor


def _details(editor, **params):
    from figrecipe._django.handlers.elements import handle_element_details

    response = handle_element_details(_GetRequest(params), editor)
    return response.status_code, json.loads(response.content.decode())


def test_bar_reports_its_value(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax0_bar1")
    # Assert
    assert body["value"] == 2.5


def test_bar_reports_row_and_category_column(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax0_bar1")
    # Assert
    assert (body["row"], body["column"]) == (1, "b")


def test_bar_reports_its_series(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax0_bar1")
    # Assert
    assert body["series"] == "bar_0_bar1"


def test_matrix_cell_reports_value_row_and_col(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax1_image0", row="2", col="3")
    # Assert
    assert (body["value"], body["row"], body["col"]) == (11.0, 2, 3)


def test_matrix_without_cell_reports_shape_and_range(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax1_image0")
    # Assert
    assert (body["shape"], body["minimum"], body["maximum"]) == ([3, 4], 0.0, 11.0)


def test_scatter_point_reports_coordinates_and_series(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    _, body = _details(editor, element="ax0_scatter0", index="1")
    # Assert
    assert (body["value"], body["series"]) == ([2.0, 5.0], "pts")


def test_out_of_range_cell_is_not_found(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    status, _ = _details(editor, element="ax1_image0", row="9", col="0")
    # Assert
    assert status == 404


def test_missing_element_key_is_bad_request(_django_ready):
    # Arrange
    editor = _editor_with_axes()
    # Act
    status, _ = _details(editor)
    # Assert
    assert status == 400


def test_element_details_endpoint_is_registered(_django_ready):
    # Arrange
    from figrecipe._django.handlers import HANDLERS
    from figrecipe._django.handlers.elements import handle_element_details

    # Act
    registered = HANDLERS.get("element_details")
    # Assert
    assert registered is handle_element_details


def test_properties_renders_the_details_section():
    # Arrange
    source = (_FRONTEND / "components" / "Properties" / "Properties.tsx").read_text(
        encoding="utf-8"
    )
    # Act
    wired = "<ElementDetails />" in source
    # Assert
    assert wired


def test_hitmap_overlay_picks_cells_on_the_selected_matrix():
    # Arrange
    source = (_FRONTEND / "components" / "Canvas" / "HitmapOverlay.tsx").read_text(
        encoding="utf-8"
    )
    # Act
    picks_cells = "setElementCell(cell.row, cell.col)" in source
    # Assert
    assert picks_cells


def test_selection_loads_details_from_the_endpoint():
    # Arrange
    source = (_FRONTEND / "store" / "syncActions.ts").read_text(encoding="utf-8")
    # Act
    loads = "element_details?element=" in source
    # Assert
    assert loads


def test_details_strings_have_japanese_translations():
    # Arrange
    catalog = _LOCALE.read_text(encoding="utf-8")
    # Act
    missing = [
        s for s in ("Value", "Row", "Column", "Series") if f'msgid "{s}"' not in catalog
    ]
    # Assert
    assert missing == []
