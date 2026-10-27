#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""English default, complete Japanese: figrecipe's catalogs and the pages that use them."""

import json
import os
from pathlib import Path

import django
import pytest
from scitex_sdk.app.i18n import (
    app_locale_dir,
    misplaced_locale_dirs,
    uncompiled_catalogs,
    untranslated_msgids,
)

APP = "figrecipe._django"
JA_MESSAGES = Path(app_locale_dir(APP)) / "ja" / "LC_MESSAGES"

#: Visible editor labels that must never reach a Japanese page in English.
CHECKED_LABELS = [
    "Panel",
    "Data",
    "Canvas",
    "Details",
    "No selection",
    "Go to Data",
    "No tables",
    "Current",
    "Preset",
    "Layout",
    "View",
    "Export",
    "Undo",
    "Redo",
    "Line",
    "Scatter",
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


def test_compiled_catalogs_match_po_sources():
    # Arrange — mtime cannot be trusted (git does not preserve it), so compare
    # content: the running app serves the .mo (via {% scitex_js_catalog %}),
    # while every other gate grades the .po. A stale .mo silently ships
    # English for every string added since the last hand recompile
    # (card figrecipe-i18n-runtime-freshness-20261026).
    from babel.messages.mofile import read_mo
    from babel.messages.pofile import read_po

    def key(msg):
        return tuple(msg.id) if isinstance(msg.id, (list, tuple)) else msg.id

    def sval(msg):
        return (
            tuple(msg.string)
            if isinstance(msg.string, (list, tuple))
            else msg.string
        )

    stale = []
    for po_path in sorted(JA_MESSAGES.glob("*.po")):
        mo_path = po_path.with_suffix(".mo")
        with po_path.open("rb") as handle:
            po = {key(m): sval(m) for m in read_po(handle) if m.id}
        if not mo_path.exists():
            stale.append(f"{mo_path.name} (missing)")
            continue
        with mo_path.open("rb") as handle:
            mo = {key(m): sval(m) for m in read_mo(handle) if m.id}
        if po != mo:
            missing = [k for k in po if k not in mo]
            changed = [k for k in po if k in mo and po[k] != mo[k]]
            stale.append(
                f"{mo_path.name} (missing={len(missing)} changed={len(changed)})"
            )
    # Act + Assert
    assert stale == []


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
