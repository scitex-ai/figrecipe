#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe's standalone.html shell template.

figrecipe prototyped the ``favicon_href`` context var and scitex-ui adopted it as
the shared contract (0.6.4), where ``standalone_shell.html`` renders the
``<link rel="icon">`` itself. figrecipe's own override was removed; these tests
pin that the favicon still renders — exactly ONCE, not zero times (override
removed and parent doesn't render it) and not twice (both render it).

Since scitex-ui 0.10.0 the shell brands the tab by DEFAULT: with no
``favicon_href`` supplied it renders the shared scitex-ui favicon partial
(``scitex_ui/img/scitex-favicon.svg``) instead of an unbranded tab, so the
no-favicon pin is "default brand icon exactly once", no longer "no icon link".
"""

import os

import django
import pytest


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _render(_django_ready, **context):
    from django.template.loader import render_to_string

    return render_to_string("figrecipe/standalone.html", context)


def test_favicon_renders_exactly_once(_django_ready):
    # Arrange: the parent shell renders the icon link in <head>, outside the
    # extra_css block, so a figrecipe override would DUPLICATE it, not replace it.
    href = "data:image/svg+xml,<svg/>"
    # Act
    html = _render(_django_ready, favicon_href=href, working_dir="/tmp")
    # Assert
    assert html.count('rel="icon"') == 1


def test_favicon_href_reaches_the_markup(_django_ready):
    # Arrange
    href = "data:image/svg+xml,<svg/>"
    # Act
    html = _render(_django_ready, favicon_href=href, working_dir="/tmp")
    # Assert
    assert "data:image/svg+xml" in html


def test_default_favicon_renders_once_when_none_supplied(_django_ready):
    # Arrange: since scitex-ui 0.10.0 the shell's documented default is the
    # shared SciTeX brand favicon, rendered by the parent shell exactly once
    # (a figrecipe override would duplicate it, an unbranded tab would drop it).
    # Act
    html = _render(_django_ready, working_dir="/tmp")
    # Assert
    assert html.count('rel="icon"') == 1


def test_app_stylesheet_survives_the_override_removal(_django_ready):
    # Arrange: the extra_css block still carries figrecipe's own stylesheet — only
    # the duplicate favicon link was removed from it.
    # Act
    html = _render(_django_ready, working_dir="/tmp")
    # Assert
    assert "index.css" in html


# EOF
