#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`/datatables/data` must return rows for a CSV-backed recipe.

Card figrecipe-standalone-readiness-measured-blockers-20260902, item #3. A
recipe whose plot args reference CSVs (``data: plot_plot_data/sin_x.csv``)
renders fine, but the data table showed zero rows: a recorded arg is a mapping
``{"name", "data", "dtype"}``, and `handle_datatable_data` passed the whole
mapping to `to_json_serializable`, which for a dict returns the dict — so the
caller's `isinstance(list)` check failed, the row loop never ran, and the
columns were registered with no data. The fix extracts the ``data`` payload
first.

This drives the real handler against the gallery's own CSV-backed recipe so the
regression is pinned to the exact shape the record has after `reproduce`.
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


def _datatable_data(editor):
    # Imported here, not at module top: `figrecipe._django.handlers.__init__`
    # imports Django models and needs the app registry (django.setup()) ready,
    # which only happens once the _django_ready fixture has run.
    from figrecipe._django.handlers.datatable import handle_datatable_data

    response = handle_datatable_data(None, editor)
    assert response.status_code == 200
    return json.loads(response.content)


class TestDatatableDataCsvBacked:
    def test_csv_backed_recipe_returns_rows(self, _django_ready):
        # Arrange -- the gallery's Line template: plot args are CSV-backed.
        recipe = (
            os.path.dirname(fr.__file__)
            + "/_django/gallery_templates/plot_plot.yaml"
        )
        fig, _ = fr.reproduce(recipe)
        editor = EditorState(fig=fig)
        # Act
        payload = _datatable_data(editor)
        # Assert -- columns are present AND rows are not (the old bug was
        # columns registered, data empty).
        assert payload["source"] == "record"
        assert payload["columns"] == ["sin_x", "sin_y", "cos_x", "cos_y"]
        assert len(payload["data"]) == 100
        # The first row is the sin/cos at x=0: sin(0)=0, cos(0)=1.
        first = payload["data"][0]
        assert first["sin_x"] == pytest.approx(0.0)
        assert first["sin_y"] == pytest.approx(0.0)
        assert first["cos_y"] == pytest.approx(1.0)

    def test_inline_list_recipe_still_returns_rows(self, _django_ready):
        # Arrange -- a figure whose args are inline Python lists (no CSV); the
        # fix must not regress the inline path that already worked.
        fig, ax = fr.subplots()
        ax.plot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        editor = EditorState(fig=fig)
        # Act
        payload = _datatable_data(editor)
        # Assert -- exactly three rows, the plot's x column populated.
        assert payload["source"] == "record"
        x_cols = [c for c in payload["columns"] if c.endswith("_x")]
        assert len(payload["data"]) == 3
        assert any(k in payload["data"][0] for k in x_cols)

    def test_empty_figure_returns_empty(self, _django_ready):
        # Arrange -- a figure with no recorded data to show.
        fig, _ = fr.subplots()
        editor = EditorState(fig=fig)
        # Act
        payload = _datatable_data(editor)
        # Assert -- no columns, no rows, not an error.
        assert payload["columns"] == []
        assert payload["data"] == []
