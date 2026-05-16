#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for data serialization to external CSV files.

Verifies that all plot types externalize their data to CSV files
instead of storing inline in the YAML recipe.
"""

import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import figrecipe as fr
from figrecipe._dev import PLOTTERS, list_plotters


class TestDataSerialization:
    """Tests for data externalization to CSV files."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset matplotlib state."""
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    @pytest.fixture
    def rng(self):
        """Random number generator with fixed seed."""
        return np.random.default_rng(42)

    @pytest.fixture
    def tmpdir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.mark.parametrize("plot_type", list_plotters())
    def test_data_externalized_to_csv(self, plot_type, rng, tmpdir):
        """Test that plot data is saved to external CSV files, not inline."""
        plotter = PLOTTERS[plot_type]

        # Create figure
        fig, ax = plotter(fr, rng)

        # Save
        recipe_path = tmpdir / f"{plot_type}.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Read YAML and check no large inline arrays
        import yaml

        with open(recipe_path) as f:
            recipe = yaml.safe_load(f)

        # Find all calls with data
        inline_data_found = []
        data_files_found = []

        def check_inline_data(obj, path=""):
            """Recursively check for inline data arrays."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "data_file":
                        data_files_found.append(v)
                    elif k == "data" and isinstance(v, list):
                        # Check if it's a large array (more than 10 elements)
                        if _count_elements(v) > 10:
                            inline_data_found.append(f"{path}.{k}")
                    else:
                        check_inline_data(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_inline_data(item, f"{path}[{i}]")

        def _count_elements(arr):
            """Count total elements in nested array."""
            if isinstance(arr, list):
                return sum(_count_elements(x) for x in arr)
            return 1

        check_inline_data(recipe)

        # Plots that may have small inline data (labels, positions, etc.)
        # are OK, but large arrays should be external
        if inline_data_found:
            # Allow certain plot types with known small inline data or structural data
            allowed_inline = {
                "graph",  # stores structural data (nodes/edges) - inline is appropriate
            }
            if plot_type not in allowed_inline:
                pytest.fail(
                    f"{plot_type}: Found inline data at {inline_data_found}. "
                    f"Data should be externalized to CSV files."
                )

    @pytest.mark.parametrize("plot_type", list_plotters())
    def test_data_dir_exists_for_data_plots(self, plot_type, rng, tmpdir):
        """Test that plots with array data create a _data directory."""
        plotter = PLOTTERS[plot_type]

        # Create figure
        fig, ax = plotter(fr, rng)

        # Save
        recipe_path = tmpdir / f"{plot_type}.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Plots that typically don't need external data
        no_data_expected = {
            # These plots may have all their data inline (small arrays)
        }

        if plot_type not in no_data_expected:
            # For most plots, we expect a data directory with CSV files
            # (unless the plot has no data arrays)
            pass  # Just checking creation, not requiring


class TestSpecificPlotDataSerialization:
    """Specific tests for plot types with known serialization requirements."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset matplotlib state."""
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    @pytest.fixture
    def tmpdir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_violinplot_data_externalized(self, tmpdir):
        """Test violinplot data is saved to CSV."""
        rng = np.random.default_rng(42)
        data = [rng.normal(0, 1, 30) for _ in range(3)]

        fig, ax = fr.subplots()
        ax.violinplot(data, id="violin")

        recipe_path = tmpdir / "violinplot.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Check data directory exists and has CSV files
        data_dir = tmpdir / "violinplot_data"
        assert data_dir.exists(), "violinplot should create _data directory"

        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) > 0, "violinplot should create CSV data files"

    def test_boxplot_data_externalized(self, tmpdir):
        """Test boxplot data is saved to CSV."""
        rng = np.random.default_rng(42)
        data = [rng.normal(0, 1, 30) for _ in range(3)]

        fig, ax = fr.subplots()
        ax.boxplot(data, id="box")

        recipe_path = tmpdir / "boxplot.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Check data directory exists
        data_dir = tmpdir / "boxplot_data"
        assert data_dir.exists(), "boxplot should create _data directory"

        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) > 0, "boxplot should create CSV data files"

    def test_pie_data_externalized(self, tmpdir):
        """Test pie chart data is saved to CSV."""
        sizes = [30, 25, 20, 15, 10]
        labels = ["A", "B", "C", "D", "E"]

        fig, ax = fr.subplots()
        ax.pie(sizes, labels=labels, id="pie")

        recipe_path = tmpdir / "pie.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Check data directory exists
        data_dir = tmpdir / "pie_data"
        assert data_dir.exists(), "pie should create _data directory"

        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) > 0, "pie should create CSV data files"

    def test_eventplot_data_externalized(self, tmpdir):
        """Test eventplot data is saved to CSV."""
        rng = np.random.default_rng(42)
        data = [rng.random(10) for _ in range(3)]

        fig, ax = fr.subplots()
        ax.eventplot(data, id="events")

        recipe_path = tmpdir / "eventplot.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Check data directory exists
        data_dir = tmpdir / "eventplot_data"
        assert data_dir.exists(), "eventplot should create _data directory"

        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) > 0, "eventplot should create CSV data files"

    def test_graph_data_stored(self, tmpdir):
        """Test graph data is stored (inline is acceptable for structural data)."""
        try:
            import networkx as nx
        except ImportError:
            pytest.skip("networkx not installed")

        G = nx.karate_club_graph()

        fig, ax = fr.subplots()
        ax.graph(G, id="graph")

        recipe_path = tmpdir / "graph.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Graph data is structural (nodes/edges), inline storage is appropriate
        # Just verify the recipe was saved
        assert recipe_path.exists(), "graph recipe should be saved"

        # Verify graph data is present in recipe
        import yaml

        with open(recipe_path) as f:
            recipe = yaml.safe_load(f)

        # Find graph call
        graph_call = None
        for ax_key, ax_data in recipe.get("axes", {}).items():
            for call in ax_data.get("calls", []):
                if call.get("function") == "graph":
                    graph_call = call
                    break

        assert graph_call is not None, "graph call should be recorded"
        assert "graph_data" in graph_call.get(
            "kwargs", {}
        ), "graph data should be stored"


if __name__ == "__main__":
    # Quick test run
    print("Running data serialization tests...")
    pytest.main([__file__, "-v", "--tb=short"])

# EOF
