#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``StatResult`` — the six-stat display port."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from figrecipe._annotations import StatResult


def _complete_result() -> StatResult:
    """A result carrying all six doctrine fields."""
    return StatResult(
        p_value=0.0004,
        method="Pearson correlation",
        statistic=5.1,
        statistic_name="t",
        dof=338,
        effect_size=0.42,
        effect_name="r",
        ci=(0.21, 0.60),
        n=340,
        n_subjects=12,
    )


class TestMissingFields:
    """The doctrine's completeness check."""

    def test_complete_result_reports_nothing_missing(self):
        # Arrange
        result = _complete_result()
        # Act
        missing = result.missing_fields()
        # Assert
        assert missing == []

    def test_bare_p_value_reports_all_five_others_missing(self):
        # Arrange
        result = StatResult(p_value=0.03)
        # Act
        missing = result.missing_fields()
        # Assert
        assert missing == ["n", "CI", "method", "effect size", "test statistic"]

    def test_subject_count_alone_satisfies_sample_size(self):
        # Arrange
        result = StatResult(p_value=0.03, n_subjects=12)
        # Act
        missing = result.missing_fields()
        # Assert
        assert "n" not in missing


class TestAnnotationRendering:
    """The rendered mathtext string."""

    def test_annotation_contains_every_doctrine_field(self):
        # Arrange
        result = _complete_result()
        expected = ["12", "340", "Pearson correlation", "338", "5.10", "0.42", "95% CI"]
        # Act
        text = result.annotation()
        # Assert
        assert all(fragment in text for fragment in expected)

    def test_statistical_symbols_render_in_italic(self):
        # Arrange
        result = _complete_result()
        # Act
        text = result.annotation()
        # Assert
        assert all(symbol in text for symbol in (r"$\it{p}$", r"$\it{t}$", r"$\it{r}$"))

    def test_subject_and_sample_counts_stay_distinct(self):
        # Arrange
        result = _complete_result()
        # Act
        text = result.annotation()
        # Assert
        assert r"$\it{N}$ = 12" in text and r"$\it{n}$ = 340" in text

    def test_tiny_p_value_collapses_below_precision(self):
        # Arrange
        result = StatResult(p_value=1e-9)
        # Act
        text = result.annotation(require_complete=False)
        # Assert
        assert r"$\it{p}$ < 0.001" in text

    def test_large_sample_size_gets_comma_grouping(self):
        # Arrange
        result = StatResult(p_value=0.01, n=12340)
        # Act
        text = result.annotation(require_complete=False)
        # Assert
        assert "12,340" in text

    def test_paired_dof_renders_two_values(self):
        # Arrange
        result = StatResult(
            p_value=0.01, statistic=4.2, statistic_name="F", dof=(2, 57)
        )
        # Act
        text = result.annotation(require_complete=False)
        # Assert
        assert r"$\it{F}$(2, 57) = 4.20" in text

    def test_chi_square_uses_greek_symbol(self):
        # Arrange
        result = StatResult(p_value=0.01, statistic=9.1, statistic_name="chi2", dof=2)
        # Act
        text = result.annotation(require_complete=False)
        # Assert
        assert r"$\chi^2$(2) = 9.10" in text

    def test_separator_is_configurable_for_wrapping(self):
        # Arrange
        result = _complete_result()
        # Act
        text = result.annotation(sep=",\n")
        # Assert
        assert "\n" in text

    def test_stars_option_keeps_the_exact_p_value(self):
        # Arrange: stars are a convenience, never a replacement for the number.
        result = _complete_result()
        # Act
        text = result.annotation(stars=True)
        # Assert
        assert text.startswith("***\n") and r"$\it{p}$ < 0.001" in text

    def test_incomplete_result_warns_instead_of_rendering_silently(self):
        # Arrange
        result = StatResult(p_value=0.03)
        # Act
        warns_on_incomplete = pytest.warns(UserWarning, match="missing required field")
        # Assert
        with warns_on_incomplete:
            result.annotation()

    def test_require_complete_false_suppresses_the_warning(self):
        # Arrange
        import warnings

        result = StatResult(p_value=0.03)
        # Act
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            result.annotation(require_complete=False)
        # Assert
        assert recorded == []


class TestStars:
    """p-value to significance stars."""

    def test_highly_significant_p_gets_three_stars(self):
        # Arrange
        result = StatResult(p_value=0.0004)
        # Act
        stars = result.stars
        # Assert
        assert stars == "***"

    def test_non_significant_p_is_marked_ns(self):
        # Arrange
        result = StatResult(p_value=0.4)
        # Act
        stars = result.stars
        # Assert
        assert stars == "n.s."


class TestFromMapping:
    """The adapter seam: a producer's result dict becomes a StatResult."""

    def test_common_key_aliases_are_accepted(self):
        # Arrange
        mapping = {"pval": 0.03, "test": "Welch's t-test", "nobs": 60}
        # Act
        result = StatResult.from_mapping(mapping)
        # Assert
        assert (result.p_value, result.method, result.n) == (0.03, "Welch's t-test", 60)

    def test_split_confidence_interval_keys_are_paired(self):
        # Arrange
        mapping = {"p": 0.01, "ci_lower": 0.1, "ci_upper": 1.1}
        # Act
        result = StatResult.from_mapping(mapping)
        # Assert
        assert result.ci == (0.1, 1.1)

    def test_unrecognised_keys_are_preserved_in_extras(self):
        # Arrange
        mapping = {"p_value": 0.01, "alternative": "two-sided"}
        # Act
        result = StatResult.from_mapping(mapping)
        # Assert
        assert result.extras == {"alternative": "two-sided"}

    def test_mapping_without_p_value_fails_loudly(self):
        # Arrange
        mapping = {"statistic": 2.4, "nobs": 60}
        # Act
        raises_on_missing_p = pytest.raises(KeyError, match="requires a p-value")
        # Assert
        with raises_on_missing_p:
            StatResult.from_mapping(mapping)


class TestAxesIntegration:
    """``ax.add_stat_annotation(stat=...)`` on a recording axes."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        plt.close("all")
        yield
        plt.close("all")

    def test_stat_renders_full_annotation_by_default(self):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5], id="bars")
        # Act
        artists = ax.add_stat_annotation(0, 1, stat=_complete_result(), y=6)
        # Assert
        assert "Pearson correlation" in artists[-1].get_text()

    def test_explicit_stars_style_overrides_full_render(self):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5], id="bars")
        # Act
        artists = ax.add_stat_annotation(
            0, 1, stat=_complete_result(), y=6, style="stars"
        )
        # Assert
        assert artists[-1].get_text() == "***"

    def test_plain_p_value_call_still_shows_stars(self):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5], id="bars")
        # Act
        artists = ax.add_stat_annotation(0, 1, p_value=0.0004, y=6)
        # Assert
        assert artists[-1].get_text() == "***"

    def test_stat_annotation_survives_save_and_reproduce(self, tmp_path):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5], id="bars")
        ax.add_stat_annotation(0, 1, stat=_complete_result(), y=6, id="stat")
        recipe = tmp_path / "stat.yaml"
        fr.save(fig, recipe)
        plt.close("all")
        # Act
        fig2, ax2 = fr.reproduce(recipe)
        # Assert
        assert any("Pearson correlation" in t.get_text() for t in ax2.texts)


# EOF
