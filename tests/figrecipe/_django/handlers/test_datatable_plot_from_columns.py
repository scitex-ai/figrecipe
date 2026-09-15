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
