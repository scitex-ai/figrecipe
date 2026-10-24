#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""datatable/plot builds a figure from columns of the imported CSV.

The Data pane's Plot button sends only the plot type and column names; the
values come from the table the editor kept at import, so the plot lands in
the recipe like any other call and exports with it.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe._django.services import EditorState

django = pytest.importorskip("django")


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


class _PostRequest:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()


class _GetRequest:
    GET = {}


_CSV = "subject,time,signal\na,0,1.5\nb,1,2.5\nc,2,4.0"
_LINE_REQUEST = {"plot_type": "line", "x": "time", "columns": ["signal"]}
_LINE_XY = [[0.0, 1.5], [1.0, 2.5], [2.0, 4.0]]


def _imported(editor):
    from figrecipe._django.handlers.datatable import handle_datatable_import

    handle_datatable_import(_PostRequest({"content": _CSV, "format": "csv"}), editor)


def _plotted(editor):
    from figrecipe._django.handlers.datatable import handle_datatable_plot

    _imported(editor)
    return handle_datatable_plot(_PostRequest(_LINE_REQUEST), editor)


def _plotted_editor(tmp_path):
    fig, _ = fr.subplots()
    editor = EditorState(fig=fig, recipe_path=tmp_path / "plotted.yaml")
    response = _plotted(editor)
    return editor, response


def test_plot_draws_named_columns_of_the_imported_csv(_django_ready):
    # Arrange
    from figrecipe._django.handlers.datatable import (
        handle_datatable_import,
        handle_datatable_plot,
    )

    fig, _ = fr.subplots()
    editor = EditorState(fig=fig)
    csv = "subject,time,signal\na,0,1.5\nb,1,2.5\nc,2,4.0"
    handle_datatable_import(_PostRequest({"content": csv, "format": "csv"}), editor)
    request = _PostRequest({"plot_type": "line", "x": "time", "columns": ["signal"]})
    # Act
    handle_datatable_plot(request, editor)
    # Assert
    assert editor.fig.flat[0].lines[0].get_xydata().tolist() == [
        [0.0, 1.5],
        [1.0, 2.5],
        [2.0, 4.0],
    ]


def test_plot_reports_a_successful_save(_django_ready, tmp_path):
    # Arrange
    editor, _ = _plotted_editor(tmp_path)
    # Act
    response = _plotted(editor)
    # Assert
    assert response.status_code == 200 and json.loads(response.content)["saved"] is True


def test_plot_writes_the_new_call_to_the_recipe_file(_django_ready, tmp_path):
    # Arrange
    # Act
    _plotted_editor(tmp_path)
    # Assert
    assert (tmp_path / "plotted.yaml").exists()


def test_plotted_recipe_replays_the_drawn_line(_django_ready, tmp_path):
    # Arrange
    # Act
    _plotted_editor(tmp_path)
    # Assert
    assert fr.reproduce(str(tmp_path / "plotted.yaml"))[0].flat[0].lines[
        0
    ].get_xydata().tolist() == _LINE_XY


def test_plot_refreshes_the_recipe_png(_django_ready, tmp_path):
    # Arrange
    # Act
    _plotted_editor(tmp_path)
    # Assert
    assert len((tmp_path / "plotted.png").read_bytes()) > 1000


def test_datatable_data_serves_element_data_map_for_record_calls(_django_ready):
    # Arrange: a recipe whose calls carry file-backed data
    from figrecipe._django.handlers.datatable import handle_datatable_data
    from figrecipe._django.services import _create_editor

    gallery = (
        __import__("pathlib").Path(__file__).parents[4]
        / "src"
        / "figrecipe"
        / "_django"
        / "gallery_templates"
        / "plot_bar.yaml"
    )
    editor = _create_editor(str(gallery))
    # Act
    payload = json.loads(handle_datatable_data(_GetRequest(), editor).content.decode())
    # Assert
    element_map = payload.get("element_data_map") or {}
    bar_keys = sorted(k for k in element_map if k.startswith("ax0_bar"))
    assert bar_keys and element_map[bar_keys[0]] == {
        "columns": ["bar_0_x", "bar_0_y"],
        "row_indices": list(range(len(payload["rows"]))),
    }


def test_datatable_data_links_ui_plotted_line_to_its_table_columns(
    _django_ready, tmp_path
):
    # Arrange
    from figrecipe._django.handlers.datatable import handle_datatable_data

    editor, _ = _plotted_editor(tmp_path)
    # Act
    payload = json.loads(handle_datatable_data(_GetRequest(), editor).content.decode())
    # Assert
    assert payload.get("element_data_map", {}).get("ax0_line0") == {
        "columns": ["time", "signal"],
        "row_indices": [0, 1, 2],
    }
