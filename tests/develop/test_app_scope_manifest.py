#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe declares it is PROJECT-scoped in its manifest.

The app-scope contract (operator ledger #48, #140-149; scitex-app PR #185 /
scitex-ui PR #227) works by the leaf app declaring its scope in its manifest;
the scitex-app host then stamps ``<meta name="stx-app-scope" content="project">``
into the embedded workspace page only for project-scoped apps. The figrecipe
editor operates on a working dir = a project, so it must declare
``"scope": "project"`` -- omitting it would silently render with NO project
selector (the SDK's safe user-scoped default), half-dead for an app that needs
one.

Lives in ``tests/develop/`` next to the other source-conformance gates: this
reads the manifest (a data file, not a module) and asks "did the declaration
land?", so it is exempt from the src<->tests mirror rule.

Value set is a CLOSED enum on the host side (scitex-app ``normalize_scope``):
anything but "user"/"project" raises. So the assertion is exact, not
startswith.
"""

import importlib
import json

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support declared by the package.
    import tomli as tomllib

from pathlib import Path

import pytest
from packaging.requirements import Requirement

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST = _REPO_ROOT / "src" / "figrecipe" / "_django" / "manifest.json"


def test_manifest_declares_project_scope():
    # Arrange
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    # Act
    scope = manifest.get("scope")
    # Assert: exactly the host-accepted project value (closed enum).
    assert scope == "project"


def test_manifest_is_valid_json_with_scope_key():
    # Arrange
    raw = _MANIFEST.read_text(encoding="utf-8")
    # Act
    manifest = json.loads(raw)
    # Assert
    assert "scope" in manifest and isinstance(manifest["scope"], str)


def test_plugin_companion_entries_register_editor_and_chat_models():
    # Arrange: use the real AppConfig classes and SDK plugin partitioning.
    from django.utils.module_loading import import_string
    from scitex_sdk.app.plugins import PluginApp, partition_companions

    from figrecipe._django import INSTALLED_APPS_ENTRIES

    plugin = PluginApp(
        "figrecipe", "figrecipe._django.apps.FigRecipeEditorConfig", "figrecipe"
    )
    # Act
    companions = partition_companions(INSTALLED_APPS_ENTRIES, [plugin])
    configs = [import_string(path) for path in INSTALLED_APPS_ENTRIES]
    # Assert: discovery retains the primary once and adds the actual chat app.
    assert (
        [(config.name, config.label) for config in configs],
        companions,
    ) == (
        [
            ("figrecipe._django", "figrecipe_editor"),
            ("scitex_sdk.app._chat", "scitex_app"),
        ],
        ["figrecipe._django.apps.ScitexAppChatConfig"],
    )


def test_sdk_consumes_the_actual_operational_project_declaration():
    # Arrange
    from scitex_sdk.app.embed import normalize_scope_capabilities

    from figrecipe._django.apps import FigRecipeEditorConfig

    config = FigRecipeEditorConfig(
        "figrecipe._django", importlib.import_module("figrecipe._django")
    )
    # Act
    support = normalize_scope_capabilities(config.scope_capabilities)
    # Assert
    assert support == {"user": False, "project": True}


@pytest.mark.parametrize("extra", ("core", "dev", "scitex", "editor", "app", "desktop"))
def test_dependencies_reject_sdk_without_operational_scope_support(extra):
    # Arrange
    project = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text())["project"]
    dependencies = (
        project["dependencies"]
        if extra == "core"
        else project["optional-dependencies"][extra]
    )
    sdk = next(
        Requirement(value)
        for value in dependencies
        if Requirement(value).name == "scitex-sdk"
    )
    # Act
    unsupported_allowed = sdk.specifier.contains("0.3.16")
    # Assert
    assert not unsupported_allowed
