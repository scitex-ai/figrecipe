#!/usr/bin/env python3
# -*- coding: utf-8 -*-
try:
    from scitex_app._django import ScitexAppConfig
except ImportError:
    from django.apps import AppConfig as ScitexAppConfig


class FigRecipeEditorConfig(ScitexAppConfig):
    name = "figrecipe._django"
    label = "figrecipe_editor"
    verbose_name = "FigRecipe Editor"

    def ready(self):
        # The editor server renders figures in Django worker threads. Force the
        # headless Agg backend so no reproduce/render path can pull in a GUI
        # backend (tkinter) off the main thread and crash. Best-effort.
        try:
            import matplotlib

            matplotlib.use("Agg", force=True)
        except Exception:
            pass
        super_ready = getattr(super(), "ready", None)
        if callable(super_ready):
            super_ready()


class ScitexAppChatConfig(ScitexAppConfig):
    """AppConfig that registers scitex_app._chat models under 'scitex_app' label.

    The ChatSession and ChatMessage models declare app_label='scitex_app',
    so this config uses that label for Django model discovery.
    """

    name = "scitex_app._chat"
    label = "scitex_app"
    verbose_name = "SciTeX Chat Sessions"
