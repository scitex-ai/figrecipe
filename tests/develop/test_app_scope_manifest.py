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

import json
from pathlib import Path

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
