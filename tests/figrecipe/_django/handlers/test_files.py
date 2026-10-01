#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file handlers — first-run create (`api/new`).

Mirrors ``src/figrecipe/_django/handlers/files.py`` (PS-204 mirror rule).

Card figrecipe-standalone-readiness-measured-blockers-20260902, item #2. A
fresh user runs `figrecipe gui serve` (no SOURCE) and the editor has no
`EditorState` yet, so the view passes `editor=None`. `api/new` was NOT in
`_NO_EDITOR_ENDPOINTS`, so the view returned 400 "No recipe loaded" before the
handler ran; and even if it had, `handle_api_new` dereferenced
`editor.working_dir` / `editor.files`, which are `None`-unsafe.

The create endpoint itself must not require an editor. These tests drive the
real handler with `editor=None` and assert a blank figure is created in the
user's workspace (not the server cwd) and a subsequent create increments.
Each test makes a single assertion (STX-TQ007): checks are collected and
folded into one.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

django = pytest.importorskip("django")


@pytest.fixture(scope="module", autouse=True)
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
    def test_create_blank_figure_with_no_editor(
        self, _clean_new_editor_cache
    ):
        # Arrange -- a workspace with nothing in it, requested via ?working_dir=
        from django.test import RequestFactory

        from figrecipe._django.handlers.files import handle_api_new

        tmpdir = tempfile.mkdtemp()
        try:
            request = RequestFactory().get(f"api/new?working_dir={tmpdir}")
            # Act -- the exact first-run call: no editor loaded yet.
            response = handle_api_new(request, None)
            payload = json.loads(response.content)
            problems = []
            if response.status_code != 200:
                problems.append(f"status={response.status_code}")
            if payload.get("success") is not True:
                problems.append(f"success={payload.get('success')!r}")
            if payload.get("file") != "new_figure_001.yaml":
                problems.append(f"file={payload.get('file')!r}")
            if payload.get("working_dir") != tmpdir:
                problems.append(
                    f"working_dir={payload.get('working_dir')!r} != {tmpdir!r}"
                )
            if not payload.get("image"):
                problems.append("no image in response")
            if not Path(tmpdir, "new_figure_001.yaml").exists():
                problems.append("recipe yaml not written to the workspace")
            if not Path(tmpdir, "new_figure_001.png").exists():
                problems.append("png not written to the workspace")
            # Assert -- success, a real image, and the file landed in the
            # workspace the user pointed at (not the server's cwd).
            assert problems == [], "api/new first-run create failed: " + "; ".join(problems)
        finally:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_second_create_increments(self, _clean_new_editor_cache):
        # Arrange
        from django.test import RequestFactory

        from figrecipe._django.handlers.files import handle_api_new

        tmpdir = tempfile.mkdtemp()
        try:
            request = RequestFactory().get(f"api/new?working_dir={tmpdir}")
            # Act -- two creates for the same workspace.
            first = json.loads(handle_api_new(request, None).content)
            second = json.loads(handle_api_new(request, None).content)
            problems = []
            if first.get("file") != "new_figure_001.yaml":
                problems.append(f"first={first.get('file')!r}")
            if second.get("file") != "new_figure_002.yaml":
                problems.append(f"second={second.get('file')!r}")
            if not Path(tmpdir, "new_figure_002.yaml").exists():
                problems.append("second recipe not written")
            # Assert -- the bootstrapped editor persists, so the counter moves.
            assert problems == [], "api/new counter did not increment: " + "; ".join(problems)
        finally:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_api_new_is_a_no_editor_endpoint(self):
        # Arrange -- the view gate that used to 400 the first-run create.
        from figrecipe._django import views

        # Act
        gated = "api/new" in views._NO_EDITOR_ENDPOINTS
        # Assert
        assert gated, "api/new must not require an editor (first-run create)"
