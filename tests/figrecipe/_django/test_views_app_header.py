#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real template renders retain SDK mount identity and host row ownership."""

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
# The shared server port owns the row. The unchanged React editor portals its
# picker into that row instead of rendering its bundled legacy SDK fallback.


def test_standalone_renders_one_shared_header_port(_django_ready):
    # Arrange / Act: render the actual standalone template.
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert: one SDK port, never a second React-owned header placeholder.
    assert html.count('id="figrecipe-app-header"') == 1


def test_standalone_renders_no_header_element_server_side(_django_ready):
    # Arrange: the SDK module creates the header inside the server-owned port.
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert html.count("<header") == 0


def test_standalone_links_the_sdk_header_stylesheet(_django_ready):
    # Arrange: the shared row takes its chrome from the SDK, not a leaf fork.
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert "scitex_sdk/ui/css/app/app-header.css" in html


def test_standalone_loads_shared_header_before_unchanged_editor(_django_ready):
    # Arrange / Act: render the executable script sequence.
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert: the public SDK mounts the port before the editor can use its fallback.
    assert html.index("scitex_sdk/ui/js/app/app-header.js") < html.index(
        "figrecipe/assets/index.js"
    )


def test_standalone_page_title_carries_the_leaf_label(_django_ready):
    # Arrange
    # Act
    html = _render(_django_ready, "figrecipe/standalone.html", **_standalone_context())
    # Assert
    assert "<title>FigRecipe Editor</title>" in html


# ── workspace_partial.html (hub-embedded mount) ──────────────────────────────


def test_partial_renders_the_ssot_header(_django_ready):
    # Arrange: hub-embedded mount with a declared (possibly root) mount.
    # Act
    html = _render(
        _django_ready, "figrecipe/workspace_partial.html", **_partial_context()
    )
    # Assert
    assert "data-figrecipe-header" in html


def test_partial_header_carries_the_leaf_title(_django_ready):
    # Arrange
    # Act
    html = _render(
        _django_ready, "figrecipe/workspace_partial.html", **_partial_context()
    )
    # Assert
    assert "FigRecipe" in html


def test_partial_header_carries_the_leaf_version(_django_ready):
    # Arrange
    # Act
    html = _render(
        _django_ready, "figrecipe/workspace_partial.html", **_partial_context()
    )
    # Assert
    assert 'data-app-version="0.36.2"' in html


def test_partial_host_header_suppresses_the_leaf_row(_django_ready):
    # Arrange
    # Act
    html = _render(
        _django_ready,
        "figrecipe/workspace_partial.html",
        **_partial_context(app_header_rendered=True),
    )
    # Assert
    assert "data-figrecipe-header" not in html


def test_partial_still_mounts_the_editor_below_the_header(_django_ready):
    # Arrange: the header is additive — the mount container must survive it.
    # Act
    html = _render(
        _django_ready, "figrecipe/workspace_partial.html", **_partial_context()
    )
    # Assert
    assert 'id="app-mount"' in html


# EOF
