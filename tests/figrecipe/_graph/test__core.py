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

    def test_draw_graph_basic(self):
        """Test basic graph drawing."""
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, layout="spring", seed=42)

        assert "pos" in result
        assert "node_collection" in result
        assert "edge_collection" in result
        assert len(result["pos"]) == G.number_of_nodes()
        plt.close(fig)

    def test_draw_graph_with_labels(self):
        """Test graph drawing with labels."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, labels=True, font_size=8)

        assert result["label_collection"] is not None
        plt.close(fig)

    def test_draw_graph_directed(self):
        """Test directed graph with arrows."""
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
    def test_layouts(self, layout):
        """Test all supported layout algorithms."""
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()
        fig, ax = plt.subplots()

        result = draw_graph(ax, G, layout=layout, seed=42)
        assert len(result["pos"]) == G.number_of_nodes()
        plt.close(fig)

    def test_hierarchical_layout_dag(self):
        """Test hierarchical layout with a DAG."""
        from figrecipe._graph._core import draw_graph

        DAG = networkx.DiGraph()
        DAG.add_edges_from([("root", "a"), ("root", "b"), ("a", "c"), ("b", "d")])

        fig, ax = plt.subplots()
        result = draw_graph(ax, DAG, layout="hierarchical")

        assert len(result["pos"]) == DAG.number_of_nodes()
        plt.close(fig)

    def test_node_size_from_attribute(self):
        """Test node sizing from attribute."""
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
        from figrecipe._graph._core import draw_graph

        G = networkx.karate_club_graph()

        fig, ax = plt.subplots()
        result = draw_graph(ax, G, node_size=lambda n, d: G.degree(n) * 10)

        assert result["node_collection"] is not None
        plt.close(fig)


class TestGraphPresets:
    """Test graph preset functionality."""

    def test_get_preset_default(self):
        """Test getting default preset."""
        from figrecipe._graph._presets import get_preset

        preset = get_preset("default")
        assert "layout" in preset
        assert "node_size" in preset
        assert "node_color" in preset

    def test_get_preset_all_builtin(self):
        """Test all built-in presets can be retrieved."""
        from figrecipe._graph._presets import get_preset, list_presets

        presets = list_presets()
        assert len(presets) >= 7  # At least 7 built-in presets

        for name in presets:
            preset = get_preset(name)
            assert isinstance(preset, dict)

    def test_get_preset_invalid(self):
        """Test error on invalid preset name."""
        from figrecipe._graph._presets import get_preset

        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset("nonexistent_preset")

    def test_register_custom_preset(self):
        """Test registering a custom preset."""
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
        assert preset["node_color"] == "#ff0000"

        # Cleanup
        unregister_preset("test_custom")

    def test_register_preset_override(self):
        """Test overriding existing preset requires flag."""
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
        from figrecipe._graph._presets import unregister_preset

        with pytest.raises(ValueError, match="Cannot unregister built-in"):
            unregister_preset("default")


class TestGraphSerialization:
    """Test graph serialization/deserialization."""

    def test_graph_to_record(self):
        """Test graph serialization."""
        from figrecipe._graph._core import graph_to_record

        G = networkx.Graph()
        G.add_node("A", label="Node A", size=100)
        G.add_node("B", label="Node B", size=200)
        G.add_edge("A", "B", weight=1.5)

        pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
        record = graph_to_record(G, pos=pos, layout="spring")

        assert record["type"] == "graph"
        assert len(record["nodes"]) == 2
        assert len(record["edges"]) == 1
        assert record["nodes"][0]["x"] == 0.0
        assert record["nodes"][0]["y"] == 0.0

    def test_record_to_graph(self):
        """Test graph deserialization."""
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
        assert G.number_of_edges() == 1
        assert "A" in G.nodes()
        assert pos["A"] == (0.0, 0.0)
        assert style["layout"] == "spring"

    def test_roundtrip_serialization(self):
        """Test graph survives serialization roundtrip."""
        from figrecipe._graph._core import graph_to_record, record_to_graph

        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)

        pos = networkx.spring_layout(G, seed=42)
        record = graph_to_record(G, pos=pos)
        G2, pos2, _ = record_to_graph(record)

        assert G2.number_of_nodes() == G.number_of_nodes()
        assert G2.number_of_edges() == G.number_of_edges()
        assert set(G2.nodes()) == set(G.nodes())

    def test_record_to_graph_no_mutation(self):
        """Test record_to_graph doesn't mutate input."""
        from figrecipe._graph._core import graph_to_record, record_to_graph

        G = networkx.Graph()
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)

        record = graph_to_record(G, pos={"A": (0, 0), "B": (1, 1)})
        original_node_keys = set(record["nodes"][0].keys())
        original_edge_keys = set(record["edges"][0].keys())

        # Call record_to_graph
        G2, pos2, style = record_to_graph(record)

        # Verify no mutation
        assert set(record["nodes"][0].keys()) == original_node_keys
        assert set(record["edges"][0].keys()) == original_edge_keys
        assert "id" in record["nodes"][0]
        assert "source" in record["edges"][0]


class TestFigrecipeIntegration:
    """Test integration with figrecipe RecordingAxes."""

    def test_ax_graph_method(self):
        """Test ax.graph() method exists and works."""
        import figrecipe as fr

        G = networkx.karate_club_graph()

        fig, ax = fr.subplots()
        result = ax.graph(G, layout="spring", seed=42)

        assert "pos" in result
        assert "node_collection" in result
        plt.close("all")

    def test_ax_graph_with_preset(self):
        """Test ax.graph() with preset."""
        import figrecipe as fr

        G = networkx.karate_club_graph()
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)

        fig, ax = fr.subplots()
        result = ax.graph(G, preset="social")

        assert result["node_collection"] is not None
        plt.close("all")

    def test_ax_graph_recording(self):
        """Test that ax.graph() is properly recorded."""
        import figrecipe as fr

        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])

        fig, ax = fr.subplots()
        ax.graph(G, id="test_graph")

        # Check recording
        record = fig._recorder.figure_record
        ax_record = record.axes["ax_0_0"]
        assert len(ax_record.calls) == 1
        assert ax_record.calls[0].function == "graph"
        assert ax_record.calls[0].id == "test_graph"
        plt.close("all")

    def test_graph_save_recipe(self):
        """Test saving a figure with graph to recipe."""
        import figrecipe as fr

        G = networkx.karate_club_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use explicit .png path to avoid style-dependent format selection
            image_path = Path(tmpdir) / "graph.png"

            fig, ax = fr.subplots()
            ax.graph(G, layout="spring", seed=42, id="karate")
            fr.save(fig, image_path, validate=False, verbose=False)

            assert image_path.exists()
            assert (Path(tmpdir) / "graph.yaml").exists()

            plt.close("all")


class TestGraphRoundtrip:
    """Test graph recipe roundtrip (save and reproduce)."""

    def test_graph_roundtrip_basic(self):
        """Test basic graph roundtrip."""
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
        import figrecipe as fr

        preset = fr.get_graph_preset("default")
        assert "layout" in preset

    def test_list_graph_presets_export(self):
        """Test list_graph_presets is exported."""
        import figrecipe as fr

        presets = fr.list_graph_presets()
        assert "default" in presets
        assert "citation" in presets

    def test_register_graph_preset_export(self):
        """Test register_graph_preset is exported."""
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
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_node((0, 0))
        G.add_node((1, 1))
        G.add_edge((0, 0), (1, 1))

        fig, ax = plt.subplots()
        with pytest.raises(TypeError, match="not serializable"):
            draw_graph(ax, G)
        plt.close(fig)

    def test_empty_graph(self):
        """Test empty graph handling."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 0
        plt.close(fig)

    def test_single_node(self):
        """Test single node graph."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_node("A")
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 1
        plt.close(fig)

    def test_disconnected_components(self):
        """Test graph with disconnected components."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([("A", "B"), ("C", "D")])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 4
        plt.close(fig)

    def test_self_loop(self):
        """Test graph with self-loop."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edge("A", "A")
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 1
        plt.close(fig)

    def test_integer_node_ids(self):
        """Test integer node IDs work correctly."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, labels=True, seed=42)
        assert len(result["pos"]) == 3
        plt.close(fig)

    def test_float_node_ids(self):
        """Test float node IDs work correctly."""
        from figrecipe._graph._core import draw_graph

        G = networkx.Graph()
        G.add_edges_from([(1.0, 2.0), (2.0, 3.0)])
        fig, ax = plt.subplots()
        result = draw_graph(ax, G, seed=42)
        assert len(result["pos"]) == 3
        plt.close(fig)
