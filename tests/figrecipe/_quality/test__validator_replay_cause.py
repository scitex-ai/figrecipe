"""Tests that a failed validation names WHY, not just that pixels differ.

A pixel diff reports THAT the figure changed; replay already knows WHY. These
pin that the cause travels into the result, that only real replay failures are
quoted (a font fallback is not a cause), and that capturing them does not
silence the warnings a caller may already be watching for.

The failure trigger is a deliberately corrupted recipe, NOT a live bug — a
fixture that depends on some other defect stops testing anything the day that
defect is fixed. Real files, real saves, no mocks. One assertion per test, AAA
markers.
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
from figrecipe._reproducer._warnings import ReplayFailureWarning

#: Inserted under a call's ``kwargs:`` block (which sits at 8 spaces, so its
#: children sit at 10). matplotlib rejects the unknown key, the replay of that
#: one call raises, and figrecipe warns — which is exactly the situation whose
#: reporting is under test.
BAD_KWARG = "        kwargs:\n          nonexistent_kw: 3"


def _saved_figure():
    """A saved, cleanly-reproducing figure. Returns (fig, recipe_path)."""
    directory = Path(tempfile.mkdtemp())
    fig, ax = fr.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [0, 1, 2])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fr.save(fig, str(directory / "f.png"))
    return fig, directory / "f.yaml"


def _validate_with_broken_replay():
    """Validate a figure whose recipe has one un-replayable call."""
    fig, recipe = _saved_figure()
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace("        kwargs:", BAD_KWARG, 1),
        encoding="utf-8",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return validate_recipe(fig, recipe)


def _validate_clean():
    """Validate a figure whose recipe replays correctly."""
    fig, recipe = _saved_figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return validate_recipe(fig, recipe)


def test_replay_failure_is_a_user_warning_subclass():
    # Arrange
    category = ReplayFailureWarning
    # Act
    compatible = issubclass(category, UserWarning)
    # Assert
    assert compatible is True


def test_broken_replay_fails_validation():
    # Arrange
    result = _validate_with_broken_replay()
    # Act
    valid = result.valid
    # Assert
    assert valid is False


def test_broken_replay_records_a_cause():
    # Arrange
    result = _validate_with_broken_replay()
    # Act
    causes = result.replay_warnings
    # Assert
    assert len(causes) >= 1


def test_recorded_cause_names_the_failing_call():
    # Arrange
    result = _validate_with_broken_replay()
    # Act
    causes = result.replay_warnings
    # Assert
    assert "Failed to replay plot" in causes[0]


def test_message_carries_the_cause():
    # Arrange
    result = _validate_with_broken_replay()
    # Act
    message = result.message
    # Assert
    assert "cause:" in message


def test_message_still_reports_the_pixel_symptom():
    # Arrange
    result = _validate_with_broken_replay()
    # Act
    message = result.message
    # Assert
    assert "MSE" in message


def test_clean_replay_records_no_causes():
    # Arrange
    result = _validate_clean()
    # Act
    causes = result.replay_warnings
    # Assert
    assert causes == ()


def test_clean_validation_message_has_no_cause_line():
    # Arrange
    result = _validate_clean()
    # Act
    message = result.message
    # Assert
    assert "cause:" not in message


def test_unrelated_warnings_are_not_reported_as_causes():
    # Arrange: a font fallback fires during replay on hosts without Arial, and
    # is not a reason the figure failed to reproduce.
    result = _validate_with_broken_replay()
    # Act
    fonty = [text for text in result.replay_warnings if "Font" in text]
    # Assert
    assert fonty == []


def test_capturing_causes_does_not_silence_the_warning():
    # Arrange
    fig, recipe = _saved_figure()
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace("        kwargs:", BAD_KWARG, 1),
        encoding="utf-8",
    )
    # Act
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        validate_recipe(fig, recipe)
    # Assert
    assert any(issubclass(w.category, ReplayFailureWarning) for w in seen)


def test_callers_can_make_replay_failures_fatal():
    # Arrange
    fig, recipe = _saved_figure()
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace("        kwargs:", BAD_KWARG, 1),
        encoding="utf-8",
    )

    def strict():
        with warnings.catch_warnings():
            warnings.simplefilter("error", ReplayFailureWarning)
            validate_recipe(fig, recipe)

    # Act
    run = strict
    # Assert
    with pytest.raises(ReplayFailureWarning):
        run()


# EOF
