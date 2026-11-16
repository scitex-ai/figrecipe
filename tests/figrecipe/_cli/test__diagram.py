"""Smoke import mirror for figrecipe._cli._diagram.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest
from click.testing import CliRunner

from figrecipe._cli._diagram import diagram
from figrecipe._diagram import GraphDiagram


def test_import__cli__diagram_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._cli._diagram"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


@pytest.mark.parametrize(
    "fmt,suffix,marker",
    [
        ("mermaid", ".mmd", "graph"),
        ("graphviz", ".dot", "digraph"),
        ("yaml", ".yaml", "type: pipeline"),
    ],
)
def test_create_writes_graph_compiler_output(tmp_path, fmt, suffix, marker):
    # Arrange
    target = tmp_path / ("pipeline" + suffix)
    # Act
    _invoke(
        [
            "create",
            str(target),
            "--type",
            "pipeline",
            "--title",
            "Pipeline",
            "--format",
            fmt,
        ],
    )
    # Assert
    assert marker in target.read_text()


def _invoke(args):
    result = CliRunner().invoke(diagram, args)
    if result.exception is not None:
        raise result.exception
    return result


def _graph_recipe(tmp_path):
    graph = GraphDiagram(type="pipeline", title="Owned graph", column="double")
    graph.add_node("input", "Input")
    graph.add_node("output", "Output")
    graph.add_edge("input", "output")
    path = tmp_path / "graph.yaml"
    graph.to_yaml(path)
    return path


def test_convert_yaml_preserves_graph_nodes_and_edges(tmp_path):
    # Arrange
    source = _graph_recipe(tmp_path)
    target = tmp_path / "converted.mmd"
    # Act
    _invoke(["convert", str(source), str(target)])
    # Assert
    loaded = GraphDiagram.from_mermaid(target)
    assert (
        {n.id for n in loaded.spec.nodes},
        [(e.source, e.target) for e in loaded.spec.edges],
    ) == ({"input", "output"}, [("input", "output")])


def test_show_info_reads_graph_spec(tmp_path):
    # Arrange
    source = _graph_recipe(tmp_path)
    # Act
    result = _invoke(["show-info", str(source), "--json"])
    # Assert
    data = json.loads(result.output)
    assert data == {
        "path": str(source),
        "type": "pipeline",
        "title": "Owned graph",
        "nodes": 2,
        "edges": 1,
        "groups": 0,
        "column": "double",
    }


def test_split_loads_graph_and_reports_single_part(tmp_path):
    # Arrange
    source = _graph_recipe(tmp_path)
    # Act
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "figrecipe",
            "diagram",
            "split",
            str(source),
            "--max-nodes",
            "12",
        ],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "SCITEX_LOGGING_LEVEL": "INFO"},
    )
    # Assert
    assert "doesn't need splitting" in result.stdout


def test_render_graphviz_uses_real_backend_or_reports_missing_binary(tmp_path):
    # Arrange: no mock or online fallback; assert the exact local outcome.
    source = _graph_recipe(tmp_path)
    target = tmp_path / "graph.svg"
    has_dot = shutil.which("dot") is not None
    # Act
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "figrecipe",
            "diagram",
            "render",
            str(source),
            str(target),
            "--backend",
            "graphviz",
        ],
        capture_output=True,
        text=True,
    )
    # Assert: absent binaries verify the error contract, not SVG acceptance.
    if has_dot:
        correct_output = target.is_file() and all(
            text in target.read_text() for text in ["<svg", "Input", "Output"]
        )
        expected_exit = 0
    else:
        correct_output = (
            not target.exists()
            and "graphviz (dot) not found" in result.stdout + result.stderr
        )
        expected_exit = 1
    assert (result.returncode, correct_output) == (expected_exit, True)
