#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import warnings

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
        self._warn_if_chat_app_missing()
        super_ready = getattr(super(), "ready", None)
        if callable(super_ready):
            super_ready()

    @staticmethod
    def _warn_if_chat_app_missing(is_installed=None) -> bool:
        """Say so when a host mounted the editor WITHOUT the chat app.

        The handler registry routes ``api/chat/*`` to ``scitex_app._chat``'s
        views, and those MODELS are registered by a second app entry
        (``figrecipe._django.apps.ScitexAppChatConfig``, label ``scitex_app``).
        The documented mount named only ``figrecipe._django``, so a host could
        follow the docs exactly and still lose chat — discovered as a
        request-time failure, with nothing said at startup. A warning rather
        than an error: the rest of the editor works without chat, and failing
        boot for a feature the host may not want would be worse.

        ``is_installed`` is injectable so the contract can be executed without a
        fake app registry (no mocks): pass ``lambda label: False`` to see the
        missing-app path. Returns whether the warning was emitted.
        """
        try:
            from django.apps import apps as django_apps

            check = is_installed or django_apps.is_installed
            if check("scitex_app"):
                return False
        except Exception:
            # No app registry yet (apps.py imported outside Django): there is no
            # host mount to warn about here.
            return False
        warnings.warn(
            "figrecipe._django is mounted without "
            "'figrecipe._django.apps.ScitexAppChatConfig': the chat models are "
            "not registered, so api/chat/* will fail at request time. Add that "
            "entry to INSTALLED_APPS (docs/SCITEX_APP_INTEGRATION.md).",
            UserWarning,
            stacklevel=2,
        )
        return True


class ScitexAppChatConfig(ScitexAppConfig):
    """AppConfig that registers scitex_app._chat models under 'scitex_app' label.

    The ChatSession and ChatMessage models declare app_label='scitex_app',
    so this config uses that label for Django model discovery.
    """

    name = "scitex_app._chat"
    label = "scitex_app"
    verbose_name = "SciTeX Chat Sessions"
