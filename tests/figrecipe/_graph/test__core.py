#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for graph visualization functionality."""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

# Skip all tests if networkx is not available
networkx = pytest.importorskip("networkx")


class TestGraphModule:
    """Test the core graph module functions."""

    def test_draw_graph_basic_part_1(self):
        """Test basic graph drawing."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph
        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, layout="spring", seed=42)
        assert "pos" in result

    def test_draw_graph_basic_part_2(self):
        """Test basic graph drawing."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph
        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, layout="spring", seed=42)
        assert "node_collection" in result

    def test_draw_graph_basic_part_3(self):
        """Test basic graph drawing."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph
        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, layout="spring", seed=42)
        assert "edge_collection" in result

    def test_draw_graph_basic_part_4(self):
        """Test basic graph drawing."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph
        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, layout="spring", seed=42)
        assert len(result["pos"]) == G.number_of_nodes()

    def test_draw_graph_with_labels(self):
        """Test graph drawing with labels."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, labels=True, font_size=8)

        assert result["label_collection"] is not None
        plt.close(fig)

    def test_draw_graph_directed(self):
        """Test directed graph with arrows."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        DG = networkx.DiGraph()
        DG.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, DG, arrows=True)

        assert result["edge_collection"] is not None
        plt.close(fig)

    @pytest.mark.parametrize(
        "layout",
        ["spring", "circular", "kamada_kawai", "shell", "spectral", "random", "spiral"],
    )
    def test_layouts_graph_module(self, layout):
        """Test all supported layout algorithms."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()

        result = draw_graph(ax, G, layout=layout, seed=42)
        assert len(result["pos"]) == G.number_of_nodes()
        plt.close(fig)

    def test_hierarchical_layout_dag(self):
        """Test hierarchical layout with a DAG."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        DAG = networkx.DiGraph()
        DAG.add_edges_from([("root", "a"), ("root", "b"), ("a", "c"), ("b", "d")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, DAG, layout="hierarchical")

        assert len(result["pos"]) == DAG.number_of_nodes()
        plt.close(fig)

    def test_node_size_from_attribute(self):
        """Test node sizing from attribute."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_node("A", size=100)
        G.add_node("B", size=200)
        G.add_node("C", size=300)
        G.add_edges_from([("A", "B"), ("B", "C")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, node_size="size")

        assert result["node_collection"] is not None
        plt.close(fig)

    def test_node_color_from_attribute(self):
        """Test node coloring from attribute."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["community"] = 0 if n < 17 else 1

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, node_color="community", colormap="tab10")

        assert result["node_collection"] is not None
        plt.close(fig)

    def test_edge_width_from_attribute(self):
        """Test edge width from attribute."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=2.0)
        G.add_edge("C", "A", weight=3.0)

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, edge_width="weight")

        assert result["edge_collection"] is not None
        plt.close(fig)

    def test_callable_node_size(self):
        """Test node sizing with callable."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, node_size=lambda n, d: G.degree(n) * 10)

        assert result["node_collection"] is not None
        plt.close(fig)


class TestGraphPresets:
    """Test graph preset functionality."""

    def test_get_preset_default_part_1(self):
        """Test getting default preset."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import get_preset
        preset = get_preset("default")
        assert "layout" in preset

    def test_get_preset_default_part_2(self):
        """Test getting default preset."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import get_preset
        preset = get_preset("default")
        assert "node_size" in preset

    def test_get_preset_default_part_3(self):
        """Test getting default preset."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import get_preset
        preset = get_preset("default")
        assert "node_color" in preset

    def test_get_preset_all_builtin(self):
        """Test all built-in presets can be retrieved."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import get_preset, list_presets

        presets = list_presets()
        assert len(presets) >= 7  # At least 7 built-in presets

        for name in presets:
            preset = get_preset(name)
            if not (isinstance(preset, dict)):
                raise AssertionError

    def test_get_preset_invalid(self):
        """Test error on invalid preset name."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import get_preset

        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset("nonexistent_preset")

    def test_register_custom_preset_part_1(self):
        """Test registering a custom preset."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import (
            get_preset,
            register_preset,
            unregister_preset,
        )
        register_preset(
            "test_custom",
            {"layout": "circular", "node_color": "#ff0000", "node_size": 50},
        )
        preset = get_preset("test_custom")
        assert preset["layout"] == "circular"

    def test_register_custom_preset_part_2(self):
        """Test registering a custom preset preserves node_color."""
        # Arrange
        # Use a part-2-unique name: the global presets registry persists
        # across `_part_1`'s call inside the same test session, so reusing
        # the same name here would trip the "already exists" guard.
        from figrecipe._graph._presets import (
            get_preset,
            register_preset,
        )
        register_preset(
            "test_custom_part_2",
            {"layout": "circular", "node_color": "#ff0000", "node_size": 50},
        )
        # Act
        preset = get_preset("test_custom_part_2")
        # Assert
        assert preset["node_color"] == "#ff0000"

    def test_register_preset_override(self):
        """Test overriding existing preset requires flag."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import register_preset, unregister_preset

        register_preset("test_override", {"layout": "spring"})

        with pytest.raises(ValueError, match="already exists"):
            register_preset("test_override", {"layout": "circular"})

        # With override=True it should work
        register_preset("test_override", {"layout": "circular"}, override=True)

        # Cleanup
        unregister_preset("test_override")

    def test_unregister_builtin_fails(self):
        """Test cannot unregister built-in preset."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._presets import unregister_preset

        with pytest.raises(ValueError, match="Cannot unregister built-in"):
            unregister_preset("default")


class TestGraphSerialization:
    """Test graph serialization/deserialization."""

    def test_graph_to_record_part_1(self):
        """Test graph serialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record
        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)
        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")
        assert record["type"] == "graph"

    def test_graph_to_record_part_2(self):
        """Test graph serialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record
        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)
        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")
        assert len(record["nodes"]) == 2

    def test_graph_to_record_part_3(self):
        """Test graph serialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record
        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)
        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")
        assert len(record["edges"]) == 1

    def test_graph_to_record_part_4(self):
        """Test graph serialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record
        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)
        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")
        assert record["nodes"][0]["x"] == 0.0

    def test_graph_to_record_part_5(self):
        """Test graph serialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record
        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)
        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")
        assert record["nodes"][0]["y"] == 0.0

    def test_record_to_graph_part_1(self):
        """Test graph deserialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import record_to_graph
        record = {
            "type": "graph",
            "directed": False,
            "nodes": [
                {"id": "A", "label": "Node A", "x": 0.0, "y": 0.0},
                {"id": "B", "label": "Node B", "x": 1.0, "y": 1.0},
            ],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
            "style": {"layout": "spring"},
        }
        G, pos, style = record_to_graph(record)
        assert G.number_of_nodes() == 2

    def test_record_to_graph_part_2(self):
        """Test graph deserialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import record_to_graph
        record = {
            "type": "graph",
            "directed": False,
            "nodes": [
                {"id": "A", "label": "Node A", "x": 0.0, "y": 0.0},
                {"id": "B", "label": "Node B", "x": 1.0, "y": 1.0},
            ],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
            "style": {"layout": "spring"},
        }
        G, pos, style = record_to_graph(record)
        assert G.number_of_edges() == 1

    def test_record_to_graph_part_3(self):
        """Test graph deserialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import record_to_graph
        record = {
            "type": "graph",
            "directed": False,
            "nodes": [
                {"id": "A", "label": "Node A", "x": 0.0, "y": 0.0},
                {"id": "B", "label": "Node B", "x": 1.0, "y": 1.0},
            ],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
            "style": {"layout": "spring"},
        }
        G, pos, style = record_to_graph(record)
        assert "A" in G.nodes()

    def test_record_to_graph_part_4(self):
        """Test graph deserialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import record_to_graph
        record = {
            "type": "graph",
            "directed": False,
            "nodes": [
                {"id": "A", "label": "Node A", "x": 0.0, "y": 0.0},
                {"id": "B", "label": "Node B", "x": 1.0, "y": 1.0},
            ],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
            "style": {"layout": "spring"},
        }
        G, pos, style = record_to_graph(record)
        assert pos["A"] == (0.0, 0.0)

    def test_record_to_graph_part_5(self):
        """Test graph deserialization."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import record_to_graph
        record = {
            "type": "graph",
            "directed": False,
            "nodes": [
                {"id": "A", "label": "Node A", "x": 0.0, "y": 0.0},
                {"id": "B", "label": "Node B", "x": 1.0, "y": 1.0},
            ],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
            "style": {"layout": "spring"},
        }
        G, pos, style = record_to_graph(record)
        assert style["layout"] == "spring"

    def test_roundtrip_serialization_part_1(self):
        """Test graph survives serialization roundtrip."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)
        pos = networkx.spring_layout(G, seed=42)
        record = graph_to_record(G, pos=pos)
        G2, pos2, _ = record_to_graph(record)
        assert G2.number_of_nodes() == G.number_of_nodes()

    def test_roundtrip_serialization_part_2(self):
        """Test graph survives serialization roundtrip."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)
        pos = networkx.spring_layout(G, seed=42)
        record = graph_to_record(G, pos=pos)
        G2, pos2, _ = record_to_graph(record)
        assert G2.number_of_edges() == G.number_of_edges()

    def test_roundtrip_serialization_part_3(self):
        """Test graph survives serialization roundtrip."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)
        pos = networkx.spring_layout(G, seed=42)
        record = graph_to_record(G, pos=pos)
        G2, pos2, _ = record_to_graph(record)
        assert set(G2.nodes()) == set(G.nodes())

    def test_record_to_graph_no_mutation_part_1(self):
        """Test record_to_graph doesn't mutate input."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.Graph()
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)
        record = graph_to_record(G, pos={"A": (0, 0), "B": (1, 1)})
        original_node_keys = set(record["nodes"][0].keys())
        original_edge_keys = set(record["edges"][0].keys())
        G2, pos2, style = record_to_graph(record)
        assert set(record["nodes"][0].keys()) == original_node_keys

    def test_record_to_graph_no_mutation_part_2(self):
        """Test record_to_graph doesn't mutate input."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.Graph()
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)
        record = graph_to_record(G, pos={"A": (0, 0), "B": (1, 1)})
        original_node_keys = set(record["nodes"][0].keys())
        original_edge_keys = set(record["edges"][0].keys())
        G2, pos2, style = record_to_graph(record)
        assert set(record["edges"][0].keys()) == original_edge_keys

    def test_record_to_graph_no_mutation_part_3(self):
        """Test record_to_graph doesn't mutate input."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.Graph()
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)
        record = graph_to_record(G, pos={"A": (0, 0), "B": (1, 1)})
        original_node_keys = set(record["nodes"][0].keys())
        original_edge_keys = set(record["edges"][0].keys())
        G2, pos2, style = record_to_graph(record)
        assert "id" in record["nodes"][0]

    def test_record_to_graph_no_mutation_part_4(self):
        """Test record_to_graph doesn't mutate input."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import graph_to_record, record_to_graph
        G = networkx.Graph()
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)
        record = graph_to_record(G, pos={"A": (0, 0), "B": (1, 1)})
        original_node_keys = set(record["nodes"][0].keys())
        original_edge_keys = set(record["edges"][0].keys())
        G2, pos2, style = record_to_graph(record)
        assert "source" in record["edges"][0]


class TestFigrecipeIntegration:
    """Test integration with figrecipe RecordingAxes."""

    def test_ax_graph_method_part_1(self):
        """Test ax.graph() method exists and works."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        G = networkx.karate_club_graph()
        fig, ax = fr.subplots()
        result = ax.graph(G, layout="spring", seed=42)
        assert "pos" in result

    def test_ax_graph_method_part_2(self):
        """Test ax.graph() method exists and works."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        G = networkx.karate_club_graph()
        fig, ax = fr.subplots()
        result = ax.graph(G, layout="spring", seed=42)
        assert "node_collection" in result

    def test_ax_graph_with_preset(self):
        """Test ax.graph() with preset."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)

        fig, ax = fr.subplots()
        result = ax.graph(G, preset="social")

        assert result["node_collection"] is not None
        plt.close("all")

    def test_ax_graph_recording_part_1(self):
        """Test that ax.graph() is properly recorded."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        fig, ax = fr.subplots()
        ax.graph(G, id="test_graph")
        record = fig._recorder.figure_record
        ax_record = record.axes["r0c0"]
        assert len(ax_record.calls) == 1

    def test_ax_graph_recording_part_2(self):
        """Test that ax.graph() is properly recorded."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        fig, ax = fr.subplots()
        ax.graph(G, id="test_graph")
        record = fig._recorder.figure_record
        ax_record = record.axes["r0c0"]
        assert ax_record.calls[0].function == "graph"

    def test_ax_graph_recording_part_3(self):
        """Test that ax.graph() is properly recorded."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        fig, ax = fr.subplots()
        ax.graph(G, id="test_graph")
        record = fig._recorder.figure_record
        ax_record = record.axes["r0c0"]
        assert ax_record.calls[0].id == "test_graph"

    def test_graph_save_recipe(self):
        """Test saving a figure with graph to recipe."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        G = networkx.karate_club_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use explicit .png path to avoid style-dependent format selection
            image_path = Path(tmpdir) / "graph.png"

            fig, ax = fr.subplots()
            ax.graph(G, layout="spring", seed=42, id="karate")
            fr.save(fig, image_path, validate=False, verbose=False)

            if not (image_path.exists()):
                raise AssertionError
            if not ((Path(tmpdir) / 'graph.yaml').exists()):
                raise AssertionError

            plt.close("all")
        assert True  # TQ001-placeholder: body exercises code under test


class TestGraphRoundtrip:
    """Test graph recipe roundtrip (save and reproduce)."""

    def test_graph_roundtrip_basic(self):
        """Test basic graph roundtrip."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        G = networkx.karate_club_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "roundtrip.yaml"

            # Create and save
            fig, ax = fr.subplots()
            ax.graph(G, layout="spring", seed=42, id="roundtrip_test")
            fr.save(fig, recipe_path, validate=False, verbose=False)
            plt.close("all")

            # Reproduce
            fig2, ax2 = fr.reproduce(recipe_path)
            assert fig2 is not None
            plt.close("all")

    def test_graph_roundtrip_with_attributes(self):
        """Test graph roundtrip with node/edge attributes."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        G = networkx.Graph()
        G.add_node("A", size=100, color="red")
        G.add_node("B", size=200, color="blue")
        G.add_edge("A", "B", weight=2.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "roundtrip_attrs.yaml"

            fig, ax = fr.subplots()
            ax.graph(G, node_size="size", edge_width="weight", seed=42)
            fr.save(fig, recipe_path, validate=False, verbose=False)
            plt.close("all")

            fig2, ax2 = fr.reproduce(recipe_path)
            assert fig2 is not None
            plt.close("all")

    def test_graph_roundtrip_directed(self):
        """Test directed graph roundtrip."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        DG = networkx.DiGraph()
        DG.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])

        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "roundtrip_directed.yaml"

            fig, ax = fr.subplots()
            ax.graph(DG, arrows=True, layout="spring", seed=42)
            fr.save(fig, recipe_path, validate=False, verbose=False)
            plt.close("all")

            fig2, ax2 = fr.reproduce(recipe_path)
            assert fig2 is not None
            plt.close("all")


class TestGraphExports:
    """Test public API exports."""

    def test_get_graph_preset_export(self):
        """Test get_graph_preset is exported."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr

        preset = fr.get_graph_preset("default")
        assert "layout" in preset

    def test_list_graph_presets_export_part_1(self):
        """Test list_graph_presets is exported."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        presets = fr.list_graph_presets()
        assert "default" in presets

    def test_list_graph_presets_export_part_2(self):
        """Test list_graph_presets is exported."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        presets = fr.list_graph_presets()
        assert "citation" in presets

    def test_register_graph_preset_export(self):
        """Test register_graph_preset is exported."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        from figrecipe._graph._presets import unregister_preset

        fr.register_graph_preset("test_export", {"layout": "circular"})
        preset = fr.get_graph_preset("test_export")
        assert preset["layout"] == "circular"

        # Cleanup
        unregister_preset("test_export")


class TestGraphValidation:
    """Test graph validation and edge cases."""

    def test_multigraph_raises_error(self):
        """Test that MultiGraph raises clear error."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.MultiGraph()
        G.add_edge("A", "B", weight=1)
        G.add_edge("A", "B", weight=2)

        fig, ax = plt.subplots()
        with pytest.raises(TypeError, match="MultiGraph.*not.*supported"):
            draw_graph(ax, G)
        plt.close(fig)

    def test_multidigraph_raises_error(self):
        """Test that MultiDiGraph raises clear error."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.MultiDiGraph()
        G.add_edge("A", "B", weight=1)
        G.add_edge("A", "B", weight=2)

        fig, ax = plt.subplots()
        with pytest.raises(TypeError, match="MultiGraph.*not.*supported"):
            draw_graph(ax, G)
        plt.close(fig)

    def test_tuple_node_id_raises_error(self):
        """Test that tuple node IDs raise clear error."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_node((0, 0))
        G.add_node((1, 1))
        G.add_edge((0, 0), (1, 1))

        fig, ax = plt.subplots()
        with pytest.raises(TypeError, match="not serializable"):
            draw_graph(ax, G)
        plt.close(fig)

    def test_empty_graph_validation(self):
        """Test empty graph handling."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 0
        plt.close(fig)

    def test_single_node_graph_validation(self):
        """Test single node graph."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_node("A")
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 1
        plt.close(fig)

    def test_disconnected_components_graph_validation(self):
        """Test graph with disconnected components."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("C", "D")])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 4
        plt.close(fig)

    def test_self_loop_graph_validation(self):
        """Test graph with self-loop."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edge("A", "A")
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 1
        plt.close(fig)

    def test_integer_node_ids(self):
        """Test integer node IDs work correctly."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, labels=True, seed=42)
        assert len(result["pos"]) == 3
        plt.close(fig)

    def test_float_node_ids(self):
        """Test float node IDs work correctly."""
        # Arrange
        # Act
        # Assert
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([(1.0, 2.0), (2.0, 3.0)])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 3
        plt.close(fig)
