#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex.stats integration."""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe import utils
from figrecipe._integrations._scitex_stats import (
    _convert_flat_format,
    _convert_nested_format,
    _p_to_stars,
    from_scitex_stats,
)


class TestPToStars:
    """Tests for p-value to stars conversion."""

    def test_three_stars(self):
        assert _p_to_stars(0.0001) == "***"

    def test_two_stars(self):
        assert _p_to_stars(0.005) == "**"

    def test_one_star(self):
        assert _p_to_stars(0.03) == "*"

    def test_not_significant(self):
        assert _p_to_stars(0.1) == "ns"

    def test_ns_symbol_false(self):
        assert _p_to_stars(0.1, ns_symbol=False) == ""


class TestConvertFlatFormat:
    """Tests for flat format conversion."""

    def test_basic_conversion(self):
        result = {
            "name": "Control vs Treatment",
            "method": "t-test",
            "p_value": 0.003,
        }
        comp = _convert_flat_format(result)
        assert comp["name"] == "Control vs Treatment"
        assert comp["method"] == "t-test"
        assert comp["p_value"] == 0.003
        assert comp["stars"] == "**"

    def test_with_effect_size_float(self):
        result = {
            "name": "A vs B",
            "p_value": 0.01,
            "effect_size": 0.8,
        }
        comp = _convert_flat_format(result)
        assert comp["effect_size"]["name"] == "d"
        assert comp["effect_size"]["value"] == 0.8

    def test_with_effect_size_and_ci(self):
        result = {
            "name": "A vs B",
            "p_value": 0.01,
            "effect_size": 0.8,
            "ci95": [0.3, 1.3],
        }
        comp = _convert_flat_format(result)
        assert comp["effect_size"]["ci_lower"] == 0.3
        assert comp["effect_size"]["ci_upper"] == 1.3

    def test_with_formatted_stars(self):
        result = {
            "name": "A vs B",
            "p_value": 0.001,
            "formatted": "**",  # From scitex.stats load_statsz
        }
        comp = _convert_flat_format(result)
        assert comp["stars"] == "**"


class TestConvertNestedFormat:
    """Tests for nested format conversion."""

    def test_basic_conversion(self):
        result = {
            "name": "comparison",
            "method": {"name": "t-test", "variant": "independent"},
            "results": {
                "statistic": 2.5,
                "statistic_name": "t",
                "p_value": 0.015,
            },
        }
        comp = _convert_nested_format(result)
        assert comp["method"] == "t-test"
        assert comp["p_value"] == 0.015
        assert comp["stars"] == "*"

    def test_with_effect_size(self):
        result = {
            "name": "test",
            "method": {"name": "anova"},
            "results": {
                "p_value": 0.001,
                "effect_size": {"name": "eta_squared", "value": 0.25},
            },
        }
        comp = _convert_nested_format(result)
        assert comp["effect_size"]["name"] == "eta_squared"
        assert comp["effect_size"]["value"] == 0.25


class TestFromScitexStats:
    """Tests for main conversion function."""

    def test_single_result(self):
        result = {
            "name": "Control vs Treatment",
            "method": "t-test",
            "p_value": 0.003,
        }
        stats = from_scitex_stats(result)
        assert "comparisons" in stats
        assert len(stats["comparisons"]) == 1
        assert stats["comparisons"][0]["name"] == "Control vs Treatment"

    def test_multiple_results(self):
        results = [
            {"name": "A vs B", "method": "t-test", "p_value": 0.01},
            {"name": "A vs C", "method": "t-test", "p_value": 0.05},
            {"name": "B vs C", "method": "t-test", "p_value": 0.2},
        ]
        stats = from_scitex_stats(results)
        assert len(stats["comparisons"]) == 3

    def test_already_converted_format(self):
        """Test that already-converted format is handled."""
        stats = {"comparisons": [{"name": "A vs B", "p_value": 0.01, "stars": "*"}]}
        result = from_scitex_stats(stats)
        assert len(result["comparisons"]) == 1


class TestIntegrationWithFigrecipe:
    """Tests for integration with figrecipe figures."""

    def test_set_stats_from_scitex(self):
        """Test setting figure stats from converted scitex result."""
        scitex_result = {
            "name": "Control vs Treatment",
            "method": "t-test",
            "p_value": 0.003,
            "effect_size": 1.21,
        }
        stats = from_scitex_stats(scitex_result)

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1])
        fig.set_stats(stats)

        assert fig.stats is not None
        assert len(fig.stats["comparisons"]) == 1
        assert fig.stats["comparisons"][0]["p_value"] == 0.003

    def test_generate_caption_from_scitex(self):
        """Test caption generation with scitex stats."""
        scitex_result = {
            "name": "Control vs Treatment",
            "method": "t-test",
            "p_value": 0.003,
        }
        stats = from_scitex_stats(scitex_result)

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1])
        fig.set_title_metadata("Effect of Treatment")
        fig.set_stats(stats)

        caption = fig.generate_caption()
        assert "Control vs Treatment" in caption

    def test_annotate_from_stats(self):
        """Test auto-annotation from stats."""
        from figrecipe._integrations import annotate_from_stats

        stats = {
            "comparisons": [{"name": "A vs B", "p_value": 0.003, "x1": 0, "x2": 1}]
        }

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1])
        artists = annotate_from_stats(ax, stats, style="stars")

        assert len(artists) > 0

    def test_annotate_with_positions(self):
        """Test annotation with group position mapping."""
        from figrecipe._integrations import annotate_from_stats

        stats = from_scitex_stats(
            {
                "name": "Control vs Treatment",
                "p_value": 0.003,
            }
        )

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1])
        artists = annotate_from_stats(
            ax, stats, positions={"Control": 0, "Treatment": 1}, style="stars"
        )

        assert len(artists) > 0


class TestScitexStatsAvailable:
    """Test availability flag."""

    def test_flag_exists(self):
        assert hasattr(utils, "SCITEX_STATS_AVAILABLE")
        # Will be True or False depending on installation
        assert isinstance(utils.SCITEX_STATS_AVAILABLE, bool)

    def test_functions_available(self):
        assert hasattr(utils, "from_scitex_stats")
        assert hasattr(utils, "annotate_from_stats")
