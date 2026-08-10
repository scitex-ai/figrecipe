#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for the file-tree recipe-detection helpers.

Guards the 2026-07-13 fix: a listed file the backend refuses to read (e.g. a
symlinked node_modules/@scitex/ui escaping the root, which scitex-app's
FileSystemBackend rejects with ``ValueError("Path traversal detected")``) must
be treated as "not a recipe", never propagate out and 500 the whole
``/api/files`` tree.
"""

import os
from pathlib import Path

import pytest

django = pytest.importorskip("django")


@pytest.fixture(scope="module")
def _django_ready():
    # Importing the handlers package (via _files_tree) wires Django models
    # from scitex-app's chat app, so settings must be configured first.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


class _RaisingBackend:
    """Files backend whose read() raises, mimicking the traversal guard."""

    def __init__(self, exc):
        self._exc = exc

    def read(self, path):
        raise self._exc

    def exists(self, path):
        return False


def test_is_figrecipe_yaml_rel_returns_false_on_value_error(_django_ready):
    # Arrange -- backend rejects the path like scitex-app's traversal guard.
    from figrecipe._django.handlers._files_tree import _is_figrecipe_yaml_rel

    backend = _RaisingBackend(ValueError("Path traversal detected: 'x'"))
    # Act
    result = _is_figrecipe_yaml_rel("escaping/symlink.yml", backend)
    # Assert
    assert result is False


def test_is_figrecipe_yaml_rel_returns_false_on_os_error(_django_ready):
    # Arrange -- pre-existing behaviour must be preserved.
    from figrecipe._django.handlers._files_tree import _is_figrecipe_yaml_rel

    backend = _RaisingBackend(OSError("boom"))
    # Act
    result = _is_figrecipe_yaml_rel("unreadable.yml", backend)
    # Assert
    assert result is False


def test_enrich_tree_skips_value_error_file_without_raising(_django_ready):
    # Arrange -- a one-file tree whose only entry escapes the root.
    from figrecipe._django.handlers._files_tree import _enrich_tree

    backend = _RaisingBackend(ValueError("Path traversal detected: 'x'"))
    tree = [{"type": "file", "name": "codecov.yml", "path": "node_modules/x.yml"}]
    # Act -- must not propagate the ValueError up to the API dispatcher.
    enriched = _enrich_tree(tree, Path("/tmp"), None, backend)
    # Assert
    assert enriched == []


# EOF
