#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""datatable/data must speak the shape the React editor store reads.

`loadDatatable` reads ``columns[].name`` and positional ``rows``. The handler
returned bare column names plus ``data`` (a list of dicts), so the store saw
``rows`` undefined and every column name undefined: the Data table stayed
empty even for a figure with data, and an imported CSV never appeared because
import did not keep the table for the follow-up ``datatable/data`` read.
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


def _data(editor):
    from figrecipe._django.handlers.datatable import handle_datatable_data

    return json.loads(handle_datatable_data(None, editor).content)


def test_record_table_has_named_columns_and_positional_rows(_django_ready):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1.0, 2.0], [3.0, 4.0])
    editor = EditorState(fig=fig)
    # Act
    payload = _data(editor)
    shape = (len(payload["columns"]), payload["rows"])
    # Assert
    assert shape == (2, [[1.0, 3.0], [2.0, 4.0]])


def test_imported_csv_is_what_the_next_data_read_shows(_django_ready):
    # Arrange
    from figrecipe._django.handlers.datatable import handle_datatable_import

    fig, _ = fr.subplots()
    editor = EditorState(fig=fig)
    request = _PostRequest({"content": "time,signal\n0,1.5\n1,2.5", "format": "csv"})
    handle_datatable_import(request, editor)
    # Act
    payload = _data(editor)
    # Assert
    assert payload == {
        "columns": [
            {"name": "time", "dtype": "numeric"},
            {"name": "signal", "dtype": "numeric"},
        ],
        "rows": [[0.0, 1.5], [1.0, 2.5]],
        "source": "import",
    }
