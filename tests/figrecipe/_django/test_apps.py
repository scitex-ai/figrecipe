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

import subprocess
import sys
import warnings
from pathlib import Path

from figrecipe._django.apps import FigRecipeEditorConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
SETTINGS = REPO_ROOT / "src" / "figrecipe" / "_django" / "settings.py"
DOC = REPO_ROOT / "docs" / "SCITEX_APP_INTEGRATION.md"

CHAT_APP = "figrecipe._django.apps.ScitexAppChatConfig"


def test_missing_sdk_reports_gui_extra_without_losing_plugin_metadata():
    """A core install can plot; GUI discovery requires the actual SDK class."""
    # Arrange
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib.abc
import sys
class NoSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'scitex_sdk' or fullname.startswith('scitex_sdk.'):
            raise ModuleNotFoundError('SDK absent', name='scitex_sdk')
sys.meta_path.insert(0, NoSDK())
import figrecipe
from django.conf import settings
assert not settings.configured
try:
    from figrecipe._django.apps import FigRecipeEditorConfig
except ImportError as exc:
    assert 'scitex-sdk' in str(exc) and 'figrecipe[editor]' in str(exc)
else:
    raise AssertionError('GUI discovery must not fall back to plain AppConfig')
assert not settings.configured
""",
        ],
        capture_output=True,
        text=True,
    )
    # Act
    # Assert
    assert result.returncode == 0, result.stderr


class TestStartupWarning:
    def test_a_host_without_the_chat_app_is_warned_at_startup(self):
        # Arrange
        # Arrange
        missing = lambda label: False  # noqa: E731 - the injected predicate
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(missing)
        # Assert
        # Act
        # Assert
        assert emitted is True and CHAT_APP in str(caught[0].message)

    def test_a_registry_that_raises_lookup_error_is_missing_not_silent(self):
        # Arrange -- DJANGO'S REAL REGISTRY RAISES LookupError for an app that is
        # not installed. The first version of this fix caught that in its
        # defensive handler and therefore never warned at all; only mounting the
        # app end to end exposed it.
        # Arrange
        def raising_registry(label):
            raise LookupError(f"No installed app with label {label!r}.")

        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(raising_registry)
        # Assert
        # Act
        # Assert
        assert emitted is True and CHAT_APP in str(caught[0].message)

    def test_a_host_with_the_chat_app_is_not_warned(self):
        # Arrange
        # Arrange
        present = lambda label: True  # noqa: E731
        # Act
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # any warning would raise here
            emitted = FigRecipeEditorConfig._warn_if_chat_app_missing(present)
        # Assert
        # Act
        # Assert
        assert emitted is False

    def test_the_warning_says_what_to_add_and_why(self):
        # Arrange
        # Arrange
        missing = lambda label: False  # noqa: E731
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            FigRecipeEditorConfig._warn_if_chat_app_missing(missing)
        message = str(caught[0].message) if caught else ""
        # Assert -- a warning that does not name the fix is not a contract.
        # Act
        # Assert
        assert "INSTALLED_APPS" in message and "chat" in message.lower()


class TestTheContractHoldsWhereItCanDrift:
    def test_canonical_sdk_registration_preserves_the_legacy_chat_label(self):
        # Arrange
        contract = {}
        # Act
        from figrecipe._django.apps import ScitexAppChatConfig

        contract["1: ScitexAppChatConfig.name == 'scitex_sdk.app._chat'"] = bool(
            ScitexAppChatConfig.name == "scitex_sdk.app._chat"
        )
        contract["2: ScitexAppChatConfig.label == 'scitex_app'"] = bool(
            ScitexAppChatConfig.label == "scitex_app"
        )
        # Assert
        assert all(contract.values()), contract

    def test_standalone_shell_works_when_retired_distribution_imports_are_forbidden(
        self,
    ):
        # Arrange
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import importlib.abc, os, sys
class RetiredOwnerForbidden(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'scitex_app', 'scitex_ui'}:
            raise ModuleNotFoundError('retired owner forbidden', name=fullname)
sys.meta_path.insert(0, RetiredOwnerForbidden())
os.environ['DJANGO_SETTINGS_MODULE']='figrecipe._django.settings'
import django
django.setup()
from django.template.loader import render_to_string
from django.apps import apps
html=render_to_string('figrecipe/standalone.html', {'working_dir':''})
assert html.count('rel="icon"')==1
assert '/static/scitex_sdk/ui/' in html
assert apps.get_app_config('scitex_app').name=='scitex_sdk.app._chat'
assert apps.get_app_config('scitex_ui').name=='scitex_sdk.ui'
assert not {'scitex_app','scitex_ui'}.intersection(sys.modules)
""",
            ],
            capture_output=True,
            text=True,
        )
        # Act
        # Assert
        assert result.returncode == 0, result.stderr

    def test_the_config_is_django_default_so_ready_actually_runs(self):
        # Arrange -- apps.py defines TWO AppConfig subclasses, and Django only
        # picks one for the "figrecipe._django" INSTALLED_APPS entry when it is
        # marked default; otherwise it silently falls back to the BASE AppConfig
        # and ready() never runs. Mounting the package end to end showed exactly
        # that: no warning fired, and the Agg forcing in ready() was dead code.
        # Arrange
        config = FigRecipeEditorConfig
        # Act
        is_default = config.default
        # Assert
        # Act
        # Assert
        assert is_default is True

    def test_the_editors_own_settings_register_both_apps(self):
        # Arrange
        # Arrange
        source = SETTINGS.read_text(encoding="utf-8")
        # Act
        registrations = [
            name for name in ("figrecipe._django", CHAT_APP) if name in source
        ]
        # Assert
        # Act
        # Assert
        assert registrations == ["figrecipe._django", CHAT_APP], registrations

    def test_the_documented_mount_lists_both_apps(self):
        # Arrange
        # Arrange
        doc = DOC.read_text(encoding="utf-8")
        # Act -- the shape that shipped the defect: the editor app alone.
        single_app_mount = 'INSTALLED_APPS += ["figrecipe._django"]'
        # Assert -- the doc names the chat app, and no longer documents the form
        # that loses it.
        # Act
        # Assert
        assert CHAT_APP in doc and single_app_mount not in doc
