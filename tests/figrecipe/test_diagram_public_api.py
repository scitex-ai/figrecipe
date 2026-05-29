#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the public ``figrecipe.diagram`` API surface.

``figrecipe.diagram`` is the public face of the private ``figrecipe._diagram``
implementation, mirroring how ``figrecipe.pyplot`` exposes the recording
internals. These tests pin the public contract the umbrella aliases to
(``scitex.diagram`` -> ``figrecipe.diagram``).
"""

import importlib

import pytest

# The public diagram API the umbrella aliases against.
PUBLIC_NAMES = [
    "Diagram",
    "GraphDiagram",
    "DiagramSpec",
    "DiagramType",
    "NodeSpec",
    "EdgeSpec",
    "PaperConstraints",
    "LayoutHints",
    "ColumnLayout",
    "SpacingLevel",
    "PaperMode",
    "compile_to_mermaid",
    "compile_to_graphviz",
    "DiagramPreset",
    "get_preset",
    "list_presets",
    "WORKFLOW_PRESET",
    "DECISION_PRESET",
    "PIPELINE_PRESET",
    "SCIENTIFIC_PRESET",
    "SplitConfig",
    "SplitResult",
    "SplitStrategy",
    "get_available_backends",
]


def test_import_figrecipe_diagram_module_succeeds():
    # Arrange
    module_name = "figrecipe.diagram"
    # Act
    module = importlib.import_module(module_name)
    # Assert
    assert module.__name__ == module_name


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_public_name_is_attribute(name):
    # Arrange
    import figrecipe.diagram as diagram

    # Act
    has_attr = hasattr(diagram, name)
    # Assert
    assert has_attr, f"figrecipe.diagram.{name} missing"


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_public_name_is_in_all(name):
    # Arrange
    import figrecipe.diagram as diagram

    # Act
    in_all = name in diagram.__all__
    # Assert
    assert in_all, f"figrecipe.diagram.{name} not in __all__"


def test_from_import_exposes_callable_diagram():
    # Arrange
    import figrecipe.diagram  # noqa: F401

    # Act
    from figrecipe.diagram import Diagram

    # Assert
    assert callable(Diagram)


def test_from_import_exposes_callable_compile_to_mermaid():
    # Arrange
    import figrecipe.diagram  # noqa: F401

    # Act
    from figrecipe.diagram import compile_to_mermaid

    # Assert
    assert callable(compile_to_mermaid)


def _build_workflow_spec():
    """Build a minimal two-node workflow DiagramSpec."""
    from figrecipe.diagram import (
        DiagramSpec,
        DiagramType,
        EdgeSpec,
        NodeSpec,
    )

    return DiagramSpec(
        type=DiagramType.WORKFLOW,
        nodes=[
            NodeSpec(id="a", label="Start"),
            NodeSpec(id="b", label="End"),
        ],
        edges=[EdgeSpec(source="a", target="b")],
    )


def test_compile_spec_to_mermaid_declares_graph():
    # Arrange
    from figrecipe.diagram import compile_to_mermaid

    spec = _build_workflow_spec()
    # Act
    mermaid = compile_to_mermaid(spec)
    # Assert
    assert "graph" in mermaid


def test_compile_spec_to_mermaid_renders_edge():
    # Arrange
    from figrecipe.diagram import compile_to_mermaid

    spec = _build_workflow_spec()
    # Act
    mermaid = compile_to_mermaid(spec)
    # Assert
    assert "a --> b" in mermaid


def test_diagram_builder_records_box_text():
    # Arrange
    from figrecipe.diagram import Diagram

    diagram = Diagram(title="Public API")
    # Act
    diagram.add_box("step", "Step", x_mm=10, y_mm=10)
    # Assert
    spec = diagram.to_dict()
    assert any(box.get("title") == "Step" for box in spec.get("boxes", []))


# EOF
