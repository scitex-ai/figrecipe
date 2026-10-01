#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The standalone URLconf keeps serving the editor's assets with DEBUG off.

Django's dev server serves ``/static/`` only while ``DEBUG`` is on, and the
standalone settings now default DEBUG off (see ``test_settings.py``). Without
``urls_standalone.py`` that flip would turn the editor into a blank page with
two 404s. These tests pin the second half of the fix, and that the splice kept
the app's own routes at the root, un-namespaced.
"""

import os

import django
import pytest

_OWN_HOST = "127.0.0.1"
_SHIPPED_ASSET = "/static/figrecipe/assets/index.js"
_MISSING_ASSET = "/static/figrecipe/assets/does-not-exist.js"


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _status_with_debug_off(path):
    from django.test import Client, override_settings

    with override_settings(DEBUG=False):
        return Client().get(path, HTTP_HOST=_OWN_HOST).status_code


# ── assets with DEBUG off ────────────────────────────────────────────────────


def test_shipped_asset_is_served_with_debug_off(_django_ready):
    # Arrange
    path = _SHIPPED_ASSET
    # Act
    status = _status_with_debug_off(path)
    # Assert
    assert status == 200


def test_control_missing_asset_is_404_with_debug_off(_django_ready):
    """Control: the route discriminates, so the 200 above is not
    'everything is 200'."""
    # Arrange
    path = _MISSING_ASSET
    # Act
    status = _status_with_debug_off(path)
    # Assert
    assert status == 404


# ── the splice: the app's own routes stay at the root, un-namespaced ─────────


def test_editor_route_name_is_still_unnamespaced(_django_ready):
    # Arrange
    from django.urls import reverse

    # Act
    url = reverse("editor")
    # Assert
    assert url == "/"


def test_editor_page_still_serves_with_debug_off(_django_ready):
    # Arrange
    path = "/"
    # Act
    status = _status_with_debug_off(path)
    # Assert
    assert status == 200


# EOF
