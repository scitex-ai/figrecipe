#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone settings default DEBUG off, and the editor still gets its assets.

Measured 2026-09-02 against 0.34.6 from PyPI: ``figrecipe gui serve --host
0.0.0.0`` answered a request from the container's non-loopback address with
Django's technical 400 page -- 70,205 bytes, traceback and settings included --
because ``DEBUG`` defaulted to ``"true"``. The fix is two-sided, and so is this
file: the default flips, AND the GUI's own assets stay served, because Django's
dev server stops serving ``/static/`` the moment DEBUG is off.

Every negative assertion here has a positive control beside it, so a test that
cannot fail is not mistaken for one that passed.
"""

import importlib
import os

import django
import pytest

_ENV = "DJANGO_DEBUG"
_FOREIGN_HOST = "attacker.example.com"
_OWN_HOST = "127.0.0.1"
_SHIPPED_ASSET = "/static/figrecipe/assets/index.js"
_MISSING_ASSET = "/static/figrecipe/assets/does-not-exist.js"


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


# ── the default: the settings MODULE read under a controlled environment ──────
#
# ``django.conf.settings`` copied the module's values at setup and is not
# touched by a reload, so reloading the module isolates the default-value logic
# without disturbing the configured runtime the HTTP tests below use.


@pytest.fixture
def _settings_with_env_unset(_django_ready):
    import figrecipe._django.settings as settings_module

    saved = os.environ.pop(_ENV, None)
    yield importlib.reload(settings_module)
    if saved is not None:
        os.environ[_ENV] = saved
    importlib.reload(settings_module)


@pytest.fixture
def _settings_with_env_true(_django_ready):
    import figrecipe._django.settings as settings_module

    saved = os.environ.get(_ENV)
    os.environ[_ENV] = "true"
    yield importlib.reload(settings_module)
    if saved is None:
        os.environ.pop(_ENV, None)
    else:
        os.environ[_ENV] = saved
    importlib.reload(settings_module)


def test_debug_defaults_off_when_env_unset(_settings_with_env_unset):
    # Arrange
    module = _settings_with_env_unset
    # Act
    debug = module.DEBUG
    # Assert
    assert debug is False


def test_debug_opts_in_with_env_true(_settings_with_env_true):
    """Positive control: the switch still works, so the default is a default
    and not a dead knob."""
    # Arrange
    module = _settings_with_env_true
    # Act
    debug = module.DEBUG
    # Assert
    assert debug is True


# ── the symptom: what a network client receives on a bad Host ─────────────────


def _bad_host_response(debug):
    from django.test import Client, override_settings

    with override_settings(DEBUG=debug):
        # A host that is NOT in ALLOWED_HOSTS -> CommonMiddleware raises
        # DisallowedHost -> Django answers 400. Which 400 depends on DEBUG.
        return Client().get("/", HTTP_HOST=_FOREIGN_HOST)


@pytest.fixture
def _bad_host_debug_off(_django_ready):
    return _bad_host_response(debug=False)


@pytest.fixture
def _bad_host_debug_on(_django_ready):
    return _bad_host_response(debug=True)


def test_bad_host_is_still_refused_with_debug_off(_bad_host_debug_off):
    # Arrange
    response = _bad_host_debug_off
    # Act
    status = response.status_code
    # Assert
    assert status == 400


def test_bad_host_400_carries_no_traceback_with_debug_off(_bad_host_debug_off):
    # Arrange
    response = _bad_host_debug_off
    # Act
    body = response.content
    # Assert
    assert b"Traceback" not in body


def test_bad_host_400_does_not_name_the_exception_with_debug_off(
    _bad_host_debug_off,
):
    # Arrange
    response = _bad_host_debug_off
    # Act
    body = response.content
    # Assert
    assert b"DisallowedHost" not in body


def test_bad_host_400_is_a_plain_page_with_debug_off(_bad_host_debug_off):
    # Arrange: the technical page measured 70,205 bytes; the plain one is a
    # few hundred.
    response = _bad_host_debug_off
    # Act
    size = len(response.content)
    # Assert
    assert size < 4000


def test_positive_control_bad_host_is_400_with_debug_on(_bad_host_debug_on):
    # Arrange
    response = _bad_host_debug_on
    # Act
    status = response.status_code
    # Assert
    assert status == 400


def test_positive_control_debug_on_leaks_the_exception_name(_bad_host_debug_on):
    """The negative assertions above CAN fail: with DEBUG on the same request
    does leak."""
    # Arrange
    response = _bad_host_debug_on
    # Act
    body = response.content
    # Assert
    assert b"DisallowedHost" in body


# ── the second-order effect: assets with DEBUG off ───────────────────────────


def _asset_status_with_debug_off(path):
    from django.test import Client, override_settings

    with override_settings(DEBUG=False):
        return Client().get(path, HTTP_HOST=_OWN_HOST).status_code


def test_shipped_asset_is_served_with_debug_off(_django_ready):
    # Arrange
    path = _SHIPPED_ASSET
    # Act
    status = _asset_status_with_debug_off(path)
    # Assert
    assert status == 200


def test_control_missing_asset_is_404_with_debug_off(_django_ready):
    """Control: the route discriminates, so the 200 above is not
    'everything is 200'."""
    # Arrange
    path = _MISSING_ASSET
    # Act
    status = _asset_status_with_debug_off(path)
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
    from django.test import Client, override_settings

    # Act
    with override_settings(DEBUG=False):
        status = Client().get("/", HTTP_HOST=_OWN_HOST).status_code
    # Assert
    assert status == 200


# EOF
