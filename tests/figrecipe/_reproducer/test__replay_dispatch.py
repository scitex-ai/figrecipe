#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``_reproducer/_replay_dispatch`` (the per-call replay dispatcher).

Extracted from ``_reproducer/_core`` (line-limit split); these guard the module
imports and still exposes ``_replay_call`` so ``_core`` / ``_compose`` /
``_mm_compose`` keep resolving it.
"""

import pytest


def test_import__reproducer__replay_dispatch_module():
    # Arrange
    module_path = "figrecipe._reproducer._replay_dispatch"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_replay_dispatch_exports_replay_call():
    # Arrange
    mod = pytest.importorskip("figrecipe._reproducer._replay_dispatch")
    # Act
    exported = getattr(mod, "__all__", [])
    # Assert
    assert "_replay_call" in exported


def test_core_reexports_replay_call_from_dispatch():
    # Arrange
    core = pytest.importorskip("figrecipe._reproducer._core")
    dispatch = pytest.importorskip("figrecipe._reproducer._replay_dispatch")
    # Act
    same = core._replay_call is dispatch._replay_call
    # Assert -- _compose / _mm_compose import _replay_call from _core
    assert same is True
