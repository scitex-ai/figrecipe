#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The standalone shell renders the request's language (figrecipe).

Card figrecipe-ja-shell-lang-context-20261003: the JA catalog payload was
correct but the page rendered ``<html lang=\"en\">`` under an active JA
request, because no figrecipe context carried ``shell_lang`` and the SDK
shell template defaults the absent key to ``en``. Both defining consumers --
``views.editor_page`` and ``workspace.build_workspace_context`` -- must carry
only that key (populated from the public SDK ``shell_context``, which
resolves the active Django language); every other value stays unchanged.
Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import os
import re

import django
import pytest
from django.test import RequestFactory
from django.utils import translation


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _html_lang(html: str):
    match = re.search(r'<html[^>]*lang="([^"]*)"', html)
    return match.group(1) if match else None


def test_editor_page_renders_lang_ja_under_ja_request(_django_ready):
    # Arrange
    from figrecipe._django.views import editor_page

    request = RequestFactory().get("/")
    # Act -- rendered lang="en" while the key was missing from the context.
    with translation.override("ja"):
        html = editor_page(request).content.decode()
    # Assert
    assert _html_lang(html) == "ja"


def test_workspace_context_carries_shell_lang_ja(_django_ready):
    # Arrange
    from figrecipe._django.workspace import build_workspace_context

    request = RequestFactory().get("/")
    # Act -- the builder dict had no shell_lang key at all.
    with translation.override("ja"):
        context = build_workspace_context(request)
    # Assert
    assert context.get("shell_lang") == "ja"
