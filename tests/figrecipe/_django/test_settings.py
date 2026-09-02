#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone settings default DEBUG off, and a bad-Host 400 stays a plain page.

Measured 2026-09-02 against 0.34.6 from PyPI: ``figrecipe gui serve --host
0.0.0.0`` answered a request from the container's non-loopback address with
Django's technical 400 page -- 70,205 bytes, traceback and settings included --
because ``DEBUG`` defaulted to ``"true"``. The standalone server is the one
figrecipe surface that faces a network, so the safe value is the default and
``DJANGO_DEBUG=true`` opts back in.

Every negative assertion here has a positive control beside it, so a test that
cannot fail is not mistaken for one that passed. The other half of the fix --
assets still served with DEBUG off -- is pinned in ``test_urls_standalone.py``.
"""

import importlib
import os

import django
import pytest

_ENV = "DJANGO_DEBUG"
_FOREIGN_HOST = "attacker.example.com"


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


# EOF
