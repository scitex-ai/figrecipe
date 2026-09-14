#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""English default, complete Japanese: figrecipe's catalogs and the pages that use them."""

import json
import os
from pathlib import Path

import django
import pytest

from scitex_app.i18n import (
    app_locale_dir,
    misplaced_locale_dirs,
    uncompiled_catalogs,
    untranslated_msgids,
)

APP = "figrecipe._django"
JA_MESSAGES = Path(app_locale_dir(APP)) / "ja" / "LC_MESSAGES"

#: Visible editor labels that must never reach a Japanese page in English.
CHECKED_LABELS = [
    "Plot", "Canvas", "Details", "No selection", "Start from an example", "No tables",
    "Current", "Preset", "Layout", "View", "Export", "Undo", "Redo", "Line", "Scatter",
]


@pytest.fixture(scope="module")
def django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _editor_html(language):
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    client.cookies["django_language"] = language
    return client.get("/").content.decode()


def _embedded_catalog(html):
    marker = 'id="scitex-i18n-catalog-figrecipe--django" type="application/json">'
    return json.loads(html.split(marker, 1)[1].split("</script>", 1)[0])["catalog"]


def test_template_and_python_catalog_is_fully_translated():
    # Arrange
    po_path = JA_MESSAGES / "django.po"
    # Act
    missing = untranslated_msgids(po_path)
    # Assert
    assert missing == []


def test_script_catalog_is_fully_translated():
    # Arrange
    po_path = JA_MESSAGES / "djangojs.po"
    # Act
    missing = untranslated_msgids(po_path)
    # Assert
    assert missing == []


def test_every_catalog_is_compiled():
    # Arrange
    locale_dir = app_locale_dir(APP)
    # Act
    uncompiled = uncompiled_catalogs(locale_dir)
    # Assert
    assert uncompiled == []


def test_catalogs_live_inside_the_django_app():
    # Arrange
    app = APP
    # Act
    misplaced = misplaced_locale_dirs(app)
    # Assert
    assert misplaced == []


def test_japanese_editor_page_embeds_translations_for_every_checked_label(django_ready):
    # Arrange
    html = _editor_html("ja")
    # Act
    catalog = _embedded_catalog(html)
    # Assert
    assert [label for label in CHECKED_LABELS if not catalog.get(label)] == []


def test_english_editor_page_embeds_an_empty_catalog(django_ready):
    # Arrange
    html = _editor_html("en")
    # Act
    catalog = _embedded_catalog(html)
    # Assert
    assert catalog == {}


def test_gallery_labels_follow_the_active_language(django_ready):
    # Arrange
    from django.test import RequestFactory
    from django.utils import translation

    from figrecipe._django.handlers.gallery import handle_gallery_available

    request = RequestFactory().get("/api/gallery")
    # Act
    with translation.override("ja"):
        payload = json.loads(handle_gallery_available(request, None).content)
    # Assert
    assert payload["categories"]["line"][0]["label"] == "折れ線"
