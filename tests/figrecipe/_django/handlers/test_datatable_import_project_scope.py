#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""An edited table survives the process that made the edit.

Card figrecipe-data-column-and-plot-variant-ux-20260916 / scitex-hub PR 923
(Private Beta spec, FigRecipe slice): "project data, figure source, recipe, and
exported artifacts remain connected", and no project content may be created in a
directory the user did not select.

Before this, ``handle_datatable_import`` only set ``editor.imported_table`` — an
attribute on one EditorState in one server process. The pane looked right until
the server restarted (or a second process opened the same project), at which
point the user's edits were simply gone, because the table was never part of the
project. These tests drive the REAL handler and then read the table back through
a freshly constructed EditorState that never saw the import — the restart case of
the project's own table rather than a session's memory.

Each test makes a single assertion (STX-TQ007); checks are collected and folded
into one.
"""

import json
import os
from pathlib import Path

import pytest

from figrecipe._django.services import EditorState

django = pytest.importorskip("django")

EDITED = {
    "content": "mass,label\n1.5,alpha\n2.5,beta\n",
    "format": "csv",
}


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _import(editor):
    """Drive the real import handler; returns the parsed response."""
    # Imported here, not at module top: the handler package imports Django models
    # and needs the app registry ready, which the fixture guarantees.
    from figrecipe._django.handlers.datatable import handle_datatable_import

    request = type("Request", (), {"body": json.dumps(EDITED).encode()})()
    response = handle_datatable_import(request, editor)
    assert response.status_code == 200, response.content
    return json.loads(response.content)


def _datatable_data(editor):
    from figrecipe._django.handlers.datatable import handle_datatable_data

    response = handle_datatable_data(None, editor)
    assert response.status_code == 200, response.content
    return json.loads(response.content)


@pytest.fixture()
def project(tmp_path):
    """A selected project: its own directory, with a recipe in it."""
    recipe = tmp_path / "figure.yaml"
    recipe.write_text("recipe: {}\n", encoding="utf-8")
    return recipe


class TestImportWritesIntoTheProject:
    def test_the_table_lands_next_to_the_recipe(self, _django_ready, project):
        # Arrange
        editor = EditorState(recipe_path=project, working_dir=project.parent)
        # Act
        _import(editor)
        # Assert -- the project's own file, named as the CSV export names it.
        written = project.parent / "figure_data.csv"
        problems = []
        if not written.is_file():
            problems.append(f"no {written.name} in the project")
        else:
            text = written.read_text(encoding="utf-8")
            if "mass,label" not in text:
                problems.append(f"header missing: {text!r}")
            if "1.5,alpha" not in text:
                problems.append(f"edited row missing: {text!r}")
        assert problems == [], "; ".join(problems)

    def test_the_edit_is_read_back_by_a_process_that_never_saw_it(
        self, _django_ready, project
    ):
        # Arrange -- one process makes the edit...
        _import(EditorState(recipe_path=project, working_dir=project.parent))
        # Act -- ...and a fresh editor (a restarted server, a second process) for
        # the same project reads the pane's table. No imported_table here.
        after_restart = EditorState(
            recipe_path=project, working_dir=project.parent
        )
        payload = _datatable_data(after_restart)
        # Assert
        problems = []
        if payload["source"] != "project":
            problems.append(f"source={payload['source']!r}")
        names = [c["name"] for c in payload["columns"]]
        if names != ["mass", "label"]:
            problems.append(f"columns={names}")
        if payload["rows"] != [[1.5, "alpha"], [2.5, "beta"]]:
            problems.append(f"rows={payload['rows']}")
        assert problems == [], "edited table did not survive: " + "; ".join(problems)


class TestNoUnselectedDirectoryIsEverWritten:
    def test_a_session_with_only_the_process_cwd_writes_nothing(
        self, _django_ready, tmp_path, monkeypatch
    ):
        # Arrange -- EditorState.working_dir defaults to the process CWD, which
        # is the directory the server was launched from, NOT a project the user
        # chose. No recipe either: nothing owns this table.
        monkeypatch.chdir(tmp_path)
        editor = EditorState()
        # Act
        _import(editor)
        # Assert -- the live pane still shows the edit...
        problems = []
        if _datatable_data(editor)["rows"] != [[1.5, "alpha"], [2.5, "beta"]]:
            problems.append("the session's own pane lost the edit")
        # ...but nothing was created in a directory nobody selected.
        created = sorted(p.name for p in Path(tmp_path).iterdir())
        if created != []:
            problems.append(f"files created in the CWD: {created}")
        assert problems == [], "; ".join(problems)
