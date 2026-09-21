#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import warnings

from .._utils._optional import missing_extra

try:
    from scitex_app._django import ScitexAppConfig
except ImportError:
    try:
        from django.apps import AppConfig as ScitexAppConfig
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc


class FigRecipeEditorConfig(ScitexAppConfig):
    name = "figrecipe._django"
    label = "figrecipe_editor"
    verbose_name = "FigRecipe Editor"
    # REQUIRED, not decoration: apps.py defines TWO AppConfig subclasses, and
    # Django's auto-detection for the "figrecipe._django" INSTALLED_APPS entry
    # only picks one when it is marked default. Without this it silently falls
    # back to the BASE AppConfig, so ready() never runs — which is why the
    # chat-contract warning did not fire when the app was mounted the documented
    # way, and why the Agg forcing below was dead code too (both measured by
    # mounting the app end to end, not by unit tests).
    default = True

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
        except Exception:
            return False
        if is_installed is None:
            # Read the registry DIRECTLY rather than through
            # django.apps.apps.is_installed(): that helper RAISES
            # ImproperlyConfigured for an app that is not installed, and the
            # first two versions of this fix let that land in a defensive
            # handler and never warned at all. Both failures were invisible to
            # unit tests that inject the predicate and appeared only when the app
            # was actually mounted (docs/SCITEX_APP_INTEGRATION.md's one-app
            # shape).
            try:
                django_apps.check_apps_ready()
            except Exception:
                # No usable registry (apps.py imported outside Django): there is
                # no host mount to judge here.
                return False
            installed = any(
                config.label == "scitex_app"
                for config in django_apps.get_app_configs()
            )
        else:
            try:
                installed = bool(is_installed("scitex_app"))
            except Exception:
                # A raising predicate models Django's own is_installed(): the app
                # is missing, so warn rather than swallow.
                installed = False
        if installed:
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
