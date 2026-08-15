"""Tests that replay announces a call it cannot make.

A recipe naming a method this version does not have used to be dropped in
silence — `if method is None: return None`. The figure came out missing
whatever that call drew, while every other signal reported success: the recipe
loaded, nothing raised, nothing warned. Only a pixel comparison could notice,
and only if the missing call moved enough pixels to clear the MSE threshold.

The sub-threshold test below is the one that matters: it is the case the pixel
backstop cannot catch, and therefore the case that justifies warning at all.

Real files, real saves, no mocks. One assertion per test, AAA markers.
"""

from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe._quality._validator import validate_recipe
from figrecipe._reproducer import reproduce
from figrecipe._reproducer._warnings import ReplayFailureWarning


def _recipe_naming_an_unknown_method(plot_fn=None):
    """Save a figure, then rename one recorded call to a nonexistent method."""
    directory = Path(tempfile.mkdtemp())
    fig, ax = fr.subplots(figsize=(3, 2))
    if plot_fn is None:
        ax.plot([0, 1, 2], [0, 1, 2])
    else:
        plot_fn(ax)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fr.save(fig, str(directory / "f.png"))
    recipe = directory / "f.yaml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace(
            "function: plot", "function: no_such_method", 1
        ),
        encoding="utf-8",
    )
    return fig, recipe


def _replay_warnings(recipe):
    """Every ReplayFailureWarning raised while reproducing ``recipe``."""
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        reproduce(str(recipe))
    return [w for w in seen if issubclass(w.category, ReplayFailureWarning)]


def test_unknown_method_raises_a_replay_failure_warning():
    # Arrange
    _, recipe = _recipe_naming_an_unknown_method()
    # Act
    hits = _replay_warnings(recipe)
    # Assert
    assert len(hits) >= 1


def test_warning_names_the_offending_method():
    # Arrange
    _, recipe = _recipe_naming_an_unknown_method()
    # Act
    hits = _replay_warnings(recipe)
    # Assert
    assert "no_such_method" in str(hits[0].message)


def test_warning_says_the_figure_is_missing_something():
    # Arrange
    _, recipe = _recipe_naming_an_unknown_method()
    # Act
    hits = _replay_warnings(recipe)
    # Assert
    assert "MISSING" in str(hits[0].message)


def test_warning_points_at_the_likely_cause():
    # Arrange
    _, recipe = _recipe_naming_an_unknown_method()
    # Act
    hits = _replay_warnings(recipe)
    # Assert
    assert "newer figrecipe" in str(hits[0].message)


def test_a_clean_recipe_raises_no_replay_failure():
    # Arrange
    directory = Path(tempfile.mkdtemp())
    fig, ax = fr.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [0, 1, 2])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fr.save(fig, str(directory / "g.png"))
    # Act
    hits = _replay_warnings(directory / "g.yaml")
    # Assert
    assert hits == []


def test_validation_reports_the_dropped_call_as_a_cause():
    # Arrange
    fig, recipe = _recipe_naming_an_unknown_method()
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = validate_recipe(fig, recipe)
    # Assert
    assert any("no_such_method" in c for c in result.replay_warnings)


def test_callers_can_make_a_dropped_call_fatal():
    # Arrange
    _, recipe = _recipe_naming_an_unknown_method()

    def strict():
        with warnings.catch_warnings():
            warnings.simplefilter("error", ReplayFailureWarning)
            reproduce(str(recipe))

    # Act
    run = strict
    # Assert
    with pytest.raises(ReplayFailureWarning):
        run()


def _recipe_dropping(method: str, plot_fn):
    """Save a figure drawn by ``plot_fn``, then rename ONE recorded ``method``.

    Dropping a call by NAME is what makes the sub-threshold case expressible.
    Renaming "the first recorded plot" instead drops whichever call happened to
    be recorded first — which here is the main visible line, so such a test
    would pass while exercising a highly-visible drop, i.e. for the wrong
    reason.
    """
    directory = Path(tempfile.mkdtemp())
    fig, ax = fr.subplots(figsize=(3, 2))
    plot_fn(ax)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fr.save(fig, str(directory / "f.png"))
    recipe = directory / "f.yaml"
    text = recipe.read_text(encoding="utf-8")
    assert f"function: {method}" in text, f"{method} was not recorded"
    recipe.write_text(
        text.replace(f"function: {method}", "function: no_such_method", 1),
        encoding="utf-8",
    )
    return fig, recipe


def _faint(ax):
    """A visible line plus a mark too faint to move the pixel metric."""
    ax.plot([0, 1, 2], [0, 1, 2])
    ax.axhline(1.0, linewidth=0.1, alpha=0.02, color="white")


def test_a_sub_threshold_dropped_call_still_passes_the_pixel_check():
    # Arrange: this establishes the PREMISE of the next test — that the pixel
    # backstop alone does NOT catch this. Measured: MSE 0.00, i.e. the recipe
    # is certified as reproducing the figure exactly while a recorded call is
    # missing from it. Without this assertion the next test would only show
    # that a warning fired, not that anything needed to fire.
    fig, recipe = _recipe_dropping("axhline", _faint)
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = validate_recipe(fig, recipe)
    # Assert
    assert result.valid is True


def test_a_sub_threshold_dropped_call_is_still_reported():
    # Arrange
    _, recipe = _recipe_dropping("axhline", _faint)
    # Act
    hits = _replay_warnings(recipe)
    # Assert
    assert len(hits) >= 1


def test_replay_failure_is_filterable_as_user_warning():
    # Arrange
    category = ReplayFailureWarning
    # Act
    compatible = issubclass(category, UserWarning)
    # Assert
    assert compatible is True


# EOF
