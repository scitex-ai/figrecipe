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
        # Arrange
        # Act
        # Assert
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs

        result = reconstruct_kwargs({"colors": "red"})
        assert result["colors"] == ["red"]

    def test_reconstruct_kwargs_colors_list(self):
        """Test that colors list remains unchanged."""
        # Arrange
        # Act
        # Assert
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs

        result = reconstruct_kwargs({"colors": ["red", "blue", "green"]})
        assert result["colors"] == ["red", "blue", "green"]

    def test_reconstruct_kwargs_other_params_part_1(self):
        """Test that other params are unchanged."""
        # Arrange
        # Act
        # Assert
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs
        result = reconstruct_kwargs({"color": "red", "linewidth": 2})
        assert result["color"] == "red"

    def test_reconstruct_kwargs_other_params_part_2(self):
        """Test that other params are unchanged."""
        # Arrange
        # Act
        # Assert
        from figrecipe._reproducer._reconstruct import reconstruct_kwargs
        result = reconstruct_kwargs({"color": "red", "linewidth": 2})
        assert result["linewidth"] == 2

    def test_pie_with_colors_list_succeeds(self):
        """Test that pie chart with colors list works."""
        # Arrange
        # Act
        # Assert
        fig, ax = plt.subplots()
        result = ax.pie([30, 40, 30], colors=["red"])
        wedges = result[0]  # First element is always wedges
        assert len(wedges) == 3
        # All wedges should be red (cycling through the single color)
        for wedge in wedges:
            fc = wedge.get_facecolor()
            if not (fc[0] == 1.0):
                raise AssertionError
            if not (fc[1] == 0.0):
                raise AssertionError
            if not (fc[2] == 0.0):
                raise AssertionError

    def test_pie_reproduce_with_colors_update_part_1(self):
        """Test reproducing pie chart with updated colors parameter."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        from figrecipe._reproducer import reproduce_from_record
        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], labels=["A", "B", "C"])
        record = fig.record
        for ax_record in record.axes.values():
            for call in ax_record.calls:
                if call.function == "pie":
                    call.kwargs["colors"] = "blue"  # Single string
        new_fig, new_ax = reproduce_from_record(record)
        assert new_fig is not None

    def test_pie_reproduce_with_colors_update_part_2(self):
        """Test reproducing pie chart with updated colors parameter."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        from figrecipe._reproducer import reproduce_from_record
        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], labels=["A", "B", "C"])
        record = fig.record
        for ax_record in record.axes.values():
            for call in ax_record.calls:
                if call.function == "pie":
                    call.kwargs["colors"] = "blue"  # Single string
        new_fig, new_ax = reproduce_from_record(record)
        wedges = [p for p in new_ax.ax.patches if hasattr(p, "theta1")]
        assert len(wedges) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
