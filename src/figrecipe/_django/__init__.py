#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Django app for the figrecipe editor.

Usage (standalone):
    python -m figrecipe._django.management.commands.figrecipe_editor [recipe.yaml]

Usage (integrated into Django project):
    # settings.py
    INSTALLED_APPS = [
        ...,
        "figrecipe._django",
        "figrecipe._django.apps.ScitexAppChatConfig",  # chat models (api/chat/*)
        ...,
    ]

    # urls.py
    path("figrecipe/", include("figrecipe._django.urls")),
"""

default_app_config = "figrecipe._django.apps.FigRecipeEditorConfig"

# Hosts using scitex-sdk plugin discovery consume both the editor and its
# shared chat-model registration from this leaf-owned declaration.
INSTALLED_APPS_ENTRIES = (
    "figrecipe._django.apps.FigRecipeEditorConfig",
    "figrecipe._django.apps.ScitexAppChatConfig",
)

__all__ = ["default_app_config", "INSTALLED_APPS_ENTRIES"]
