#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Django app for the figrecipe editor.

Usage (standalone):
    python -m figrecipe._django.management.commands.figrecipe_editor [recipe.yaml]

Usage (integrated into Django project):
    # settings.py
    from figrecipe._django import INSTALLED_APPS_ENTRIES
    INSTALLED_APPS = [..., *INSTALLED_APPS_ENTRIES, ...]

    # urls.py
    path("figrecipe/", include("figrecipe._django.urls")),
"""

default_app_config = "figrecipe._django.apps.FigRecipeEditorConfig"

# Explicit mounts and standalone settings share the existing registrations.
# These strings can be read before Django setup without importing AppConfig or
# models. Automatic plugin discovery must separately consume this declaration.
INSTALLED_APPS_ENTRIES = (
    "figrecipe._django",
    "figrecipe._django.apps.ScitexAppChatConfig",
)

# Generic consumers read these strings without importing views at discovery.
# Resolve callables at request time; declarations do not authorize requests.
context_builder = "figrecipe._django.workspace.build_workspace_context"
partial_template = "figrecipe/workspace_partial.html"
content_renderer = "figrecipe._django.workspace.render_workspace_content"
# Avoid the api_policy submodule name, which Python binds on this package.
api_policy_module = "figrecipe._django.api_policy"
hosted_api_dispatcher = "figrecipe._django.views._hosted_api_dispatch"

__all__ = [
    "default_app_config",
    "INSTALLED_APPS_ENTRIES",
    "context_builder",
    "partial_template",
    "content_renderer",
    "api_policy_module",
    "hosted_api_dispatcher",
]
