#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mounting figrecipe._django takes TWO apps, and the contract says so.

Card figrecipe-django-mount-contract-under-declares-the-chat-appconfig-20260906:
the documented way to mount the editor named one app
(``INSTALLED_APPS += ["figrecipe._django"]``), but the editor's handler registry
routes ``api/chat/*`` to ``scitex_app._chat``'s views, whose MODELS are
registered by a SECOND app entry (``figrecipe._django.apps.ScitexAppChatConfig``,
label ``scitex_app``). A host that followed the documentation exactly therefore
lost chat — and learned about it from a request-time failure, not from anything
said at startup.

These tests pin the contract in all three places it can drift: the editor's own
settings, the documented mount, and the startup warning that names the omission.
Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import warnings
from pathlib import Path

from figrecipe._django.apps import FigRecipeEditorConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
SETTINGS = REPO_ROOT / "src" / "figrecipe" / "_django" / "settings.py"
DOC = REPO_ROOT / "docs" / "SCITEX_APP_INTEGRATION.md"

CHAT_APP = "figrecipe._django.apps.ScitexAppChatConfig"


class TestStartupWarning:
    def test_a_host_without_the_chat_app_is_warned_at_startup(self):
        # Arrange
        missing = lambda label: False  # noqa: E731 - the injected predicate
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(missing)
        # Assert
        assert emitted is True and CHAT_APP in str(caught[0].message)

    def test_a_registry_that_raises_lookup_error_is_missing_not_silent(self):
        # Arrange -- DJANGO'S REAL REGISTRY RAISES LookupError for an app that is
        # not installed. The first version of this fix caught that in its
        # defensive handler and therefore never warned at all; only mounting the
        # app end to end exposed it.
        def raising_registry(label):
            raise LookupError(f"No installed app with label {label!r}.")

        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(raising_registry)
        # Assert
        assert emitted is True and CHAT_APP in str(caught[0].message)

    def test_a_host_with_the_chat_app_is_not_warned(self):
        # Arrange
        present = lambda label: True  # noqa: E731
        # Act
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # any warning would raise here
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(present)
        # Assert
        assert emitted is False

    def test_the_warning_says_what_to_add_and_why(self):
        # Arrange
        missing = lambda label: False  # noqa: E731
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            FigRecipeEditorConfig._warn_if_chat_app_missing(missing)
        message = str(caught[0].message) if caught else ""
        # Assert -- a warning that does not name the fix is not a contract.
        assert "INSTALLED_APPS" in message and "chat" in message.lower()


class TestTheContractHoldsWhereItCanDrift:
    def test_the_config_is_django_default_so_ready_actually_runs(self):
        # Arrange -- apps.py defines TWO AppConfig subclasses, and Django only
        # picks one for the "figrecipe._django" INSTALLED_APPS entry when it is
        # marked default; otherwise it silently falls back to the BASE AppConfig
        # and ready() never runs. Mounting the package end to end showed exactly
        # that: no warning fired, and the Agg forcing in ready() was dead code.
        config = FigRecipeEditorConfig
        # Act
        is_default = config.default
        # Assert
        assert is_default is True

    def test_the_editors_own_settings_register_both_apps(self):
        # Arrange
        source = SETTINGS.read_text(encoding="utf-8")
        # Act
        registrations = [name for name in ("figrecipe._django", CHAT_APP) if name in source]
        # Assert
        assert registrations == ["figrecipe._django", CHAT_APP], registrations

    def test_the_documented_mount_lists_both_apps(self):
        # Arrange
        doc = DOC.read_text(encoding="utf-8")
        # Act -- the shape that shipped the defect: the editor app alone.
        single_app_mount = 'INSTALLED_APPS += ["figrecipe._django"]'
        # Assert -- the doc names the chat app, and no longer documents the form
        # that loses it.
        assert CHAT_APP in doc and single_app_mount not in doc
