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
# Compatibility owned by this leaf; generic SDK mounting preserves both names.
namespace_aliases = ("figrecipe_app",)

urlpatterns = [
    path("", views.editor_page, name="editor"),
    path("", views.editor_page, name="figure_editor"),
    path("workspace/", views.workspace_page, name="workspace"),
    # Preserve the established hosted FigRecipe URL names and nested API path.
    path("figrecipe/", views.editor_page, {"view_path": "figrecipe/"}, name="figrecipe_editor"),
    path("figrecipe/<path:endpoint>", views.api_dispatch, name="figrecipe_api"),
    path("<path:endpoint>", views.api_dispatch, name="api"),
]
