#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conditional datatable writes: a stale save is refused, never applied.

Card figrecipe-datatable-save-ordering-20261015: ``save_project_table`` was a
blind full-table ``write_text`` — two sequential saves were last-write-wins
and a delayed request silently discarded newer edits. The write path is now
revision-gated: ``datatable/data`` and import responses carry the stored
table's opaque ``revision``; an import sending ``base_revision`` lands only
while the stored table still carries it, else 409 with the CURRENT revision
so the client reloads instead of clobbering.

These tests drive the REAL handlers (same harness as
test_datatable_import_project_scope.py): import, read back through a fresh
EditorState, import again with a stale base, and prove the stored table is
untouched. Each test makes a single assertion (STX-TQ007).
"""

import json
import os

import pytest

from figrecipe._django.services import EditorState

django = pytest.importorskip("django")

EDITED = {
    "content": "mass,label\n1.5,alpha\n2.5,beta\n",
    "format": "csv",
}

NEWER = {
    "content": "mass,label\n9.0,gamma\n",
    "format": "csv",
}


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


@pytest.fixture()
def project(tmp_path):
    """A selected project: its own directory, with a recipe in it."""
    recipe = tmp_path / "figure.yaml"
    recipe.write_text("recipe: {}\n", encoding="utf-8")
    return recipe


def _post_import(editor, body):
    from figrecipe._django.handlers.datatable import handle_datatable_import

    request = type("Request", (), {"body": json.dumps(body).encode()})()
    response = handle_datatable_import(request, editor)
    return response.status_code, json.loads(response.content)


def _read_data(editor):
    from figrecipe._django.handlers.datatable import handle_datatable_data

    response = handle_datatable_data(None, editor)
    assert response.status_code == 200, response.content
    return json.loads(response.content)


def _editor_for(project):
    return EditorState(recipe_path=project, working_dir=project.parent)


class TestConditionalImport:
    def test_import_without_a_base_still_writes(self, _django_ready, project):
        # Arrange -- legacy explicit-replace path (file import, sample data).
        # Act
        status, _ = _post_import(_editor_for(project), dict(EDITED))
        # Assert
        assert status == 200

    def test_the_import_response_carries_the_revision(self, _django_ready, project):
        # Arrange
        # Act
        _, body = _post_import(_editor_for(project), dict(EDITED))
        # Assert -- opaque string the pane sends back as base_revision.
        assert isinstance(body["revision"], str)

    def test_the_data_response_carries_the_revision(self, _django_ready, project):
        # Arrange
        _post_import(_editor_for(project), dict(EDITED))
        # Act -- a FRESH editor: the restart/second-process case.
        body = _read_data(_editor_for(project))
        # Assert
        assert isinstance(body["revision"], str)

    def test_a_matching_base_writes(self, _django_ready, project):
        # Arrange
        _, first = _post_import(_editor_for(project), dict(EDITED))
        # Act
        status, _ = _post_import(
            _editor_for(project), dict(NEWER, base_revision=first["revision"])
        )
        # Assert
        assert status == 200

    def test_a_stale_base_is_refused_with_409(self, _django_ready, project):
        # Arrange
        _post_import(_editor_for(project), dict(EDITED))
        # Act -- based on a revision the stored table no longer carries.
        status, _ = _post_import(
            _editor_for(project), dict(NEWER, base_revision="stale")
        )
        # Assert
        assert status == 409

    def test_the_conflict_carries_the_current_revision(self, _django_ready, project):
        # Arrange
        _, first = _post_import(_editor_for(project), dict(EDITED))
        # Act
        _, body = _post_import(
            _editor_for(project), dict(NEWER, base_revision="stale")
        )
        # Assert -- the client reloads from this instead of guessing.
        assert body["revision"] == first["revision"]

    def test_a_refused_write_leaves_the_stored_table_untouched(
        self, _django_ready, project
    ):
        # Arrange
        _post_import(_editor_for(project), dict(EDITED))
        # Act
        _post_import(_editor_for(project), dict(NEWER, base_revision="stale"))
        # Assert -- the newer edits are still there, through a fresh editor.
        body = _read_data(_editor_for(project))
        assert body["rows"] == [[1.5, "alpha"], [2.5, "beta"]]

    def test_a_nonstring_base_is_rejected(self, _django_ready, project):
        # Arrange
        # Act
        status, _ = _post_import(_editor_for(project), dict(NEWER, base_revision=42))
        # Assert
        assert status == 400


# EOF
