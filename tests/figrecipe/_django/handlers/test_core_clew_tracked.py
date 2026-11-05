#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preview serves the live record's clew-tracked flag.

The Figures row tracked indicator reads the preview response, so a
clew-saved figure shows tracked on every load with no extra endpoint.
Stamping itself is serializer work (see test__clew_stamp); here the record
is stamped directly -- no mocks, the flag is plain record state.
"""

import matplotlib

matplotlib.use("Agg")

import json
import os

import pytest

import figrecipe as fr
from figrecipe._django.services import EditorState

django = pytest.importorskip("django")


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


class _GetRequest:
    GET = {}


def _replayed_editor(tmp_path, tracked):
    fig, ax = fr.subplots()
    ax.plot([0, 1], [1.5, 2.5])
    fig.record.clew_tracked = tracked
    path = tmp_path / "flagged.yaml"
    fig.save_recipe(path)
    replayed, _ = fr.reproduce(str(path))
    return EditorState(fig=replayed, recipe_path=path)


def test_preview_reports_clew_tracked_for_a_tracked_save(_django_ready, tmp_path):
    # Arrange
    from figrecipe._django.handlers.core import handle_preview

    editor = _replayed_editor(tmp_path, True)
    # Act
    payload = json.loads(handle_preview(_GetRequest(), editor).content.decode())
    # Assert
    assert payload["clew_tracked"] is True


def test_preview_reports_untracked_for_an_ordinary_save(_django_ready, tmp_path):
    # Arrange
    from figrecipe._django.handlers.core import handle_preview

    editor = _replayed_editor(tmp_path, False)
    # Act
    payload = json.loads(handle_preview(_GetRequest(), editor).content.decode())
    # Assert
    assert payload["clew_tracked"] is False
