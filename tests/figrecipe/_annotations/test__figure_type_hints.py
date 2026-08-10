#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the per-figure-type annotation hints."""

import pytest

from figrecipe._annotations._figure_type_hints import (
    ComparisonGeometry,
    hints_for,
    known_figure_types,
)


class TestLookup:
    """Resolving a figure type to its hint."""

    def test_bar_chart_has_a_hint(self):
        # Arrange
        figure_type = "bar"
        # Act
        hint = hints_for(figure_type)
        # Assert
        assert hint.figure_type == "bar"

    def test_lookup_is_case_insensitive(self):
        # Arrange
        figure_type = "BoxPlot"
        # Act
        hint = hints_for(figure_type)
        # Assert
        assert hint.figure_type == "box"

    def test_alias_resolves_to_its_target_entry(self):
        # Arrange: pcolormesh draws the same shape of thing as imshow.
        figure_type = "pcolormesh"
        # Act
        hint = hints_for(figure_type)
        # Assert
        assert hint.figure_type == "imshow"

    def test_unknown_figure_type_returns_none_not_an_error(self):
        # Arrange: the registry is a short list of cases that came up, not a closed
        # world. Silence is the correct answer for anything not in it.
        figure_type = "streamplot"
        # Act
        hint = hints_for(figure_type)
        # Assert
        assert hint is None

    def test_known_types_include_the_aliases(self):
        # Arrange
        expected = {"bar", "box", "violin", "scatter", "imshow", "pcolormesh", "barh"}
        # Act
        known = set(known_figure_types())
        # Assert
        assert expected <= known


class TestComparisonGeometry:
    """Where a comparison line goes, per figure type."""

    def test_categorical_plot_uses_a_bracket(self):
        # Arrange: discrete x positions give a bracket two endpoints to span.
        hint = hints_for("bar")
        # Act
        geometry = hint.geometry
        # Assert
        assert geometry is ComparisonGeometry.BRACKET_ABOVE

    def test_scatter_writes_inline_instead_of_bracketing(self):
        # Arrange: a correlation is a property of the whole cloud, so a bracket
        # would have nothing to point at.
        hint = hints_for("scatter")
        # Act
        geometry = hint.geometry
        # Assert
        assert geometry is ComparisonGeometry.INLINE_TEXT

    def test_heatmap_marks_cells_rather_than_bracketing(self):
        # Arrange: one statistic per cell, not one per pair.
        hint = hints_for("imshow")
        # Act
        geometry = hint.geometry
        # Assert
        assert geometry is ComparisonGeometry.COLORBAR_ANNOTATION

    def test_draws_bracket_is_true_only_for_bracket_geometry(self):
        # Arrange
        categorical, continuous = hints_for("violin"), hints_for("scatter")
        # Act
        flags = (categorical.draws_bracket, continuous.draws_bracket)
        # Assert
        assert flags == (True, False)


class TestMethodHints:
    """The candidate-method list is advisory, never a whitelist."""

    def test_scatter_suggests_correlation_methods(self):
        # Arrange
        hint = hints_for("scatter")
        # Act
        methods = hint.methods
        # Assert
        assert "Pearson correlation" in methods

    def test_every_entry_carries_a_note_on_the_remaining_judgement(self):
        # Arrange: the plot type hints at the data's shape but cannot decide the
        # test, so each entry must say what the caller still has to decide.
        entries = [hints_for(name) for name in known_figure_types()]
        # Act
        noteless = [entry.figure_type for entry in entries if not entry.note]
        # Assert
        assert noteless == []

    def test_hints_are_immutable(self):
        # Arrange: a shared registry entry must not be mutable by one caller.
        hint = hints_for("bar")
        # Act
        rejects_mutation = pytest.raises(AttributeError)
        # Assert
        with rejects_mutation:
            hint.figure_type = "box"


# EOF
