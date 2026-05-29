#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public diagram API for figrecipe.

This module is the public face of figrecipe's diagram subsystem. The
implementation lives in the private ``figrecipe._diagram`` package; this
module re-exports the stable, public diagram API so consumers can write::

    import figrecipe.diagram
    from figrecipe.diagram import Diagram, compile_to_mermaid

It mirrors how ``figrecipe.pyplot`` is exposed as a public submodule on top
of the recording internals.

Examples
--------
Box-and-arrow diagram (the primary ``Diagram`` builder)::

    >>> from figrecipe.diagram import Diagram
    >>> d = Diagram(title="Pipeline")
    >>> d.add_box("Load", x_mm=10, y_mm=10)  # doctest: +SKIP

Mermaid / Graphviz compilation from a semantic ``DiagramSpec``::

    >>> from figrecipe.diagram import (
    ...     DiagramSpec, DiagramType, NodeSpec, EdgeSpec, compile_to_mermaid
    ... )
    >>> spec = DiagramSpec(
    ...     type=DiagramType.WORKFLOW,
    ...     nodes=[NodeSpec(id="a", label="Start"),
    ...            NodeSpec(id="b", label="End")],
    ...     edges=[EdgeSpec(source="a", target="b")],
    ... )
    >>> mermaid = compile_to_mermaid(spec)
"""

from __future__ import annotations

# Box-and-arrow Diagram builder + graph-compilation schema/presets/split.
from ._diagram import (
    DECISION_PRESET,
    PIPELINE_PRESET,
    SCIENTIFIC_PRESET,
    WORKFLOW_PRESET,
    ColumnLayout,
    Diagram,
    DiagramPreset,
    DiagramSpec,
    DiagramType,
    EdgeSpec,
    GraphDiagram,
    LayoutHints,
    NodeSpec,
    PaperConstraints,
    PaperMode,
    SpacingLevel,
    SplitConfig,
    SplitResult,
    SplitStrategy,
    get_available_backends,
    get_preset,
    list_presets,
)

# Backend compilers (public entry points for Mermaid / Graphviz workflows).
from ._diagram._graphviz._compile import compile_to_graphviz
from ._diagram._mermaid._compile import compile_to_mermaid

__all__ = [
    # Box-and-arrow builder
    "Diagram",
    # Graph compilation
    "GraphDiagram",
    # Schema
    "DiagramSpec",
    "DiagramType",
    "NodeSpec",
    "EdgeSpec",
    "PaperConstraints",
    "LayoutHints",
    "ColumnLayout",
    "SpacingLevel",
    "PaperMode",
    # Backend compilers
    "compile_to_mermaid",
    "compile_to_graphviz",
    # Presets
    "DiagramPreset",
    "get_preset",
    "list_presets",
    "WORKFLOW_PRESET",
    "DECISION_PRESET",
    "PIPELINE_PRESET",
    "SCIENTIFIC_PRESET",
    # Split
    "SplitConfig",
    "SplitResult",
    "SplitStrategy",
    # Render
    "get_available_backends",
]

# EOF
