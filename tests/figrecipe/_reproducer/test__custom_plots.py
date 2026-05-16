#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for pie chart colors handling in reproducer."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up matplotlib figures after each test."""
    yield
    plt.close("all")


class TestReproducerPieColors:
    """Test pie chart colors parameter handling."""

    def test_reconstruct_kwargs_colors_string(self):
        """Test that colors string is wrapped in list."""
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs

        result = reconstruct_kwargs({"colors": "red"})
        assert result["colors"] == ["red"]

    def test_reconstruct_kwargs_colors_list(self):
        """Test that colors list remains unchanged."""
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs

        result = reconstruct_kwargs({"colors": ["red", "blue", "green"]})
        assert result["colors"] == ["red", "blue", "green"]

    def test_reconstruct_kwargs_other_params(self):
        """Test that other params are unchanged."""
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs

        result = reconstruct_kwargs({"color": "red", "linewidth": 2})
        assert result["color"] == "red"
        assert result["linewidth"] == 2

    def test_pie_with_colors_list_succeeds(self):
        """Test that pie chart with colors list works."""
        fig, ax = plt.subplots()
        result = ax.pie([30, 40, 30], colors=["red"])
        wedges = result[0]  # First element is always wedges
        assert len(wedges) == 3
        # All wedges should be red (cycling through the single color)
        for wedge in wedges:
            fc = wedge.get_facecolor()
            assert fc[0] == 1.0  # Red channel
            assert fc[1] == 0.0  # Green channel
            assert fc[2] == 0.0  # Blue channel

    def test_pie_reproduce_with_colors_update(self):
        """Test reproducing pie chart with updated colors parameter."""
        import figrecipe as fr
        from figrecipe._reproducer import reproduce_from_record

        # Create original figure
        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], labels=["A", "B", "C"])

        # Modify colors in record
        record = fig.record
        for ax_record in record.axes.values():
            for call in ax_record.calls:
                if call.function == "pie":
                    call.kwargs["colors"] = "blue"  # Single string

        # Reproduce - should convert 'blue' to ['blue']
        new_fig, new_ax = reproduce_from_record(record)

        # Verify no errors and figure renders
        assert new_fig is not None
        wedges = [p for p in new_ax.ax.patches if hasattr(p, "theta1")]
        assert len(wedges) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
