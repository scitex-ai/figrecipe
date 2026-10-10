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

__all__ = ["default_app_config"]
