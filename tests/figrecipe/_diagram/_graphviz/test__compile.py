#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._diagram._graphviz._compile (Arial fontname)."""

import pytest

from figrecipe._diagram._graphviz._compile import compile_to_graphviz
from figrecipe._diagram._shared._schema import (
    DiagramSpec,
    EdgeSpec,
    NodeSpec,
)


def test_import__diagram__graphviz__compile_module():
    # Arrange
    module_path = "figrecipe._diagram._graphviz._compile"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_graphviz_dot_uses_arial_fontname():
    # Arrange
    spec = DiagramSpec(
        nodes=[NodeSpec(id="a", label="A"), NodeSpec(id="b", label="B")],
        edges=[EdgeSpec(source="a", target="b")],
    )
    # Act
    dot = compile_to_graphviz(spec)
    # Assert
    assert 'fontname="Arial"' in dot and "Helvetica" not in dot
