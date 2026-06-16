#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import guard for the Django handlers package.

A broken intra-package import in any handler (e.g. ``from ._core import …`` when
the module is ``core``) is invisible to the rest of the suite — nothing else
imports ``figrecipe._django.handlers`` (it needs Django configured), so such a
typo only surfaces as a 500 when the GUI server actually starts. This test
imports the package with Django set up so that class of bug fails in CI instead.
"""

import os

import pytest

django = pytest.importorskip("django")


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


class TestHandlersImport:
    def test_handlers_package_imports(self, _django_ready):
        # Arrange -- Django is set up via the fixture.
        # Act -- importing the package wires every handler module; a broken
        # import (e.g. wrong relative module name) raises here.
        from figrecipe._django.handlers import HANDLERS

        # Assert
        assert isinstance(HANDLERS, dict) and len(HANDLERS) > 0

    def test_files_handler_imports_dpi_helper(self, _django_ready):
        # Arrange -- Django is set up via the fixture.
        # Act -- the DPI fix added `from .core import _dpi_from_request` to
        # files.py; guard the exact module path that regressed.
        from figrecipe._django.handlers.files import _dpi_from_request

        # Assert
        assert callable(_dpi_from_request)
