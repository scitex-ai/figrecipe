#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First-run create: `api/new` must work with NO recipe loaded.

Card figrecipe-standalone-readiness-measured-blockers-20260902, item #2. A
fresh user runs `figrecipe gui serve` (no SOURCE) and the editor has no
`EditorState` yet, so the view passes `editor=None`. `api/new` was NOT in
`_NO_EDITOR_ENDPOINTS`, so the view returned 400 "No recipe loaded" before the
handler ran; and even if it had, `handle_api_new` dereferenced
`editor.working_dir` / `editor.files`, which are `None`-unsafe.

The create endpoint itself must not require an editor. These tests drive the
real handler with `editor=None` and assert a blank figure is created in the
user's workspace (not the server cwd) and a subsequent create increments.
"""

import json
import os
import tempfile

import pytest

django = pytest.importorskip("django")

from pathlib import Path  # noqa: E402

from django.test import RequestFactory  # noqa: E402


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


@pytest.fixture
def _clean_new_editor_cache():
    """Drop any editor these tests bootstrap into the services cache."""
    from figrecipe._django.services import _editor_cache

    before = set(_editor_cache)
    yield
    for key in set(_editor_cache) - before:
        _editor_cache.pop(key, None)


class TestApiNewNoEditor:
    def test_create_blank_figure_with_no_editor(self, _django_ready, _clean_new_editor_cache):
        # Arrange -- a workspace with nothing in it, requested via ?working_dir=
        from figrecipe._django.handlers.files import handle_api_new

        factory = RequestFactory()
        with tempfile.TemporaryDirectory() as tmpdir:
            request = factory.get(f"api/new?working_dir={tmpdir}")
            # Act -- the exact first-run call: no editor loaded yet.
            response = handle_api_new(request, None)
            payload = json.loads(response.content)
            # Assert -- success, a real image, and the file landed in the
            # workspace the user pointed at (not the server's cwd).
            assert response.status_code == 200
            assert payload["success"] is True
            assert payload["file"] == "new_figure_001.yaml"
            assert payload["working_dir"] == tmpdir
            assert payload["image"]
            assert Path(tmpdir, "new_figure_001.yaml").exists()
            assert Path(tmpdir, "new_figure_001.png").exists()

    def test_second_create_increments(self, _django_ready, _clean_new_editor_cache):
        # Arrange
        from figrecipe._django.handlers.files import handle_api_new

        factory = RequestFactory()
        with tempfile.TemporaryDirectory() as tmpdir:
            request = factory.get(f"api/new?working_dir={tmpdir}")
            # Act -- two creates for the same workspace.
            first = json.loads(handle_api_new(request, None).content)
            second = json.loads(handle_api_new(request, None).content)
            # Assert -- the bootstrapped editor persists, so the counter moves.
            assert first["file"] == "new_figure_001.yaml"
            assert second["file"] == "new_figure_002.yaml"
            assert Path(tmpdir, "new_figure_002.yaml").exists()

    def test_api_new_is_a_no_editor_endpoint(self, _django_ready):
        # Arrange -- the view gate that used to 400 the first-run create.
        # Act
        from figrecipe._django import views

        # Assert
        assert "api/new" in views._NO_EDITOR_ENDPOINTS
