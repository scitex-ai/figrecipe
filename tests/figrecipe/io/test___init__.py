#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for ``figrecipe.io``.

Pins the standardized I/O namespace that every scitex / scitex-adjacent
package exposes (``scitex_stats.io``, ``figrecipe.io``, …). The top-level
``figrecipe.save_bundle`` etc. continue to work for back-compat; these
tests confirm the ``.io`` aliases resolve to the exact same callables so
the namespaces never drift.
"""

import pytest

import figrecipe
import figrecipe.io as fio


@pytest.mark.parametrize(
    "name",
    [
        # High-level save / load / reproduce.
        "save",
        "load",
        "reproduce",
        # Bundle primitives.
        "save_bundle",
        "load_bundle",
        "reproduce_bundle",
        # Path helpers.
        "bundle_exists",
        "create_bundle_structure",
        "get_bundle_paths",
        "is_bundle_path",
        # Bundle classes.
        "Figz",
        "Pltz",
    ],
)
def test_io_namespace_exposes_symbol(name):
    """``figrecipe.io`` carries every declared I/O verb."""
    # Arrange
    # Act
    attr = getattr(fio, name, None)
    # Assert
    assert attr is not None


@pytest.mark.parametrize(
    "name",
    [
        "save",
        "load",
        "reproduce",
        "save_bundle",
        "load_bundle",
        "reproduce_bundle",
        "Figz",
        "Pltz",
    ],
)
def test_io_alias_is_same_object_as_top_level(name):
    """``figrecipe.io.X is figrecipe.X`` — namespaces share callables."""
    # Arrange
    top = getattr(figrecipe, name)
    # Act
    io = getattr(fio, name)
    # Assert
    assert io is top


def test_io_all_lists_every_declared_export():
    """Every name in ``__all__`` resolves to an actual attribute."""
    # Arrange
    declared = list(fio.__all__)
    # Act
    missing = [n for n in declared if not hasattr(fio, n)]
    # Assert
    assert missing == []
