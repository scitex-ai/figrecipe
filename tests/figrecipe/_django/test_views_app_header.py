#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared SSoT header row in FigRecipe's Django templates.

Operator CCT4254 (card figrecipe-ssot-header-row-20261017): FigRecipe
templates carried only asset refs — no shared ``.stx-app-header`` row.
``figrecipe/_app_header.html`` adopts the SDK SSoT header (Storage PR #128 /
Writer editor.html shape): the leaf owns the VALUES (title + leaf version),
the SDK owns the chrome (``scitex_sdk/ui/css/app/app-header.css``).

These tests pin the template half of the contract through real renders
(``render_to_string`` with the contexts the views actually pass). One
assertion per test (STX-TQ007): exactly ONE header row, the SDK stylesheet
linked, the LEAF version on the badge (never the host's), no badge when no
version was passed, and the ``app_header_rendered`` host guard suppressing
the leaf row. The React half (InnerEditor yields its owned row + portals the
picker while a ``header[data-ssot]`` is present) is gated by
``frontend/tests/appHeaderSsot.test.ts``.
"""

import os

import django
import pytest


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _render(_django_ready, template, **context):
    from django.template.loader import render_to_string

    return render_to_string(template, context)


def _standalone_context(**overrides):
    context = {
        "app_label": "FigRecipe Editor",
        "app_version": "0.36.2",
        "working_dir": "/tmp",
        "hosted": False,
    }
    context.update(overrides)
    return context


def _partial_context(**overrides):
    context = {
        "stx_mount": "",
        "hosted": False,
        "app_label": "FigRecipe",
        "app_version": "0.36.2",
        "working_dir": "/tmp",
        "project_id": "",
        "project_name": "",
        "recipe": "",
    }
    context.update(overrides)
    return context


# ── standalone.html ──────────────────────────────────────────────────────────


def test_standalone_renders_the_ssot_header(_django_ready):
    # Arrange: the view passes the leaf label + version (never the host's).
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert 'data-ssot="sdk"' in html


def test_standalone_renders_exactly_one_header_element(_django_ready):
    # Arrange: one shared row — zero is the card defect, two is host + leaf.
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert html.count("<header") == 1


def test_standalone_links_the_sdk_header_stylesheet(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert: the chrome comes from the SDK, not a leaf fork.
    assert "scitex_sdk/ui/css/app/app-header.css" in html


def test_standalone_header_carries_the_leaf_title(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert "FigRecipe Editor" in html


def test_standalone_header_carries_the_leaf_version(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert ">v0.36.2<" in html


def test_standalone_header_hides_the_badge_when_version_unknown(_django_ready):
    # Arrange: SDK contract — an unknown version renders ABSENT, never as a
    # plausible-looking wrong badge.
    context = _standalone_context()
    del context["app_version"]
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **context)
    # Assert
    assert "stx-app-header__version" not in html


def test_standalone_header_row_survives_without_a_version(_django_ready):
    # Arrange: only the badge goes missing, never the row itself.
    context = _standalone_context()
    del context["app_version"]
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **context)
    # Assert
    assert 'data-ssot="sdk"' in html


def test_standalone_host_header_suppresses_the_leaf_row(_django_ready):
    # Arrange: a host rendering its own header sets app_header_rendered
    # (Writer precedent) so the page never carries two.
    # Act
    html = _render(
        _django_ready,
        "figrecipe/standalone.html",
        **_standalone_context(app_header_rendered=True),
    )
    # Assert
    assert 'data-ssot="sdk"' not in html


def test_standalone_host_header_leaves_no_header_element(_django_ready):
    # Arrange
    # Act
    html = _render(
        _django_ready,
        "figrecipe/standalone.html",
        **_standalone_context(app_header_rendered=True),
    )
    # Assert
    assert "<header" not in html


# ── workspace_partial.html (hub-embedded mount) ──────────────────────────────


def test_partial_renders_the_ssot_header(_django_ready):
    # Arrange: hub-embedded mount with a declared (possibly root) mount.
    # Act
    html = _render(_django_ready, "figrecipe/workspace_partial.html", **_partial_context())
    # Assert
    assert 'data-ssot="sdk"' in html


def test_partial_header_carries_the_leaf_title(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/workspace_partial.html", **_partial_context())
    # Assert
    assert "FigRecipe" in html


def test_partial_header_carries_the_leaf_version(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/workspace_partial.html", **_partial_context())
    # Assert
    assert ">v0.36.2<" in html


def test_partial_host_header_suppresses_the_leaf_row(_django_ready):
    # Arrange
    # Act
    html = _render(
        _django_ready,
        "figrecipe/workspace_partial.html",
        **_partial_context(app_header_rendered=True),
    )
    # Assert
    assert 'data-ssot="sdk"' not in html


def test_partial_still_mounts_the_editor_below_the_header(_django_ready):
    # Arrange: the header is additive — the mount container must survive it.
    # Act
    html = _render(_django_ready, "figrecipe/workspace_partial.html", **_partial_context())
    # Assert
    assert 'id="app-mount"' in html


# EOF
