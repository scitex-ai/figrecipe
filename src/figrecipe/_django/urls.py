#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""URL patterns for the figrecipe editor Django app."""

from .._utils._optional import missing_extra

try:
    from django.urls import path
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

from . import views

app_name = "figrecipe"

urlpatterns = [
    path("", views.editor_page, name="editor"),
    path("<path:endpoint>", views.api_dispatch, name="api"),
]
