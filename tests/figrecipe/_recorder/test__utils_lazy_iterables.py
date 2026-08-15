"""Tests for recording lazy iterables (range, dict views, one-shot iterators).

A `range` used to reach the recorder's ``str(value)`` fallback and land in the
recipe as the TEXT "range(0, 10)", so `ax.plot(range(10), ys)` could not be
saved at all. These tests pin both halves of the fix: re-iterables are
materialised, and one-shot iterators are refused rather than recorded as an
unusable placeholder.

Real figures and real saves, no mocks — the bug was invisible at the object
level and only showed up in the artifact. One assertion per test, AAA markers.
"""

from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe._recorder._utils import (
    RE_ITERABLE_SEQUENCES,
    UnrecordableArgumentError,
    _refuse_one_shot_iterator,
)


def _save(plot_fn):
    """Draw via ``plot_fn(ax)``, save, and return the recipe text.

    Returns "" if the save raised — the caller asserts on that separately.
    """
    directory = Path(tempfile.mkdtemp())
    fig, ax = fr.subplots(figsize=(3, 2))
    plot_fn(ax)
    target = directory / "f.png"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fr.save(fig, str(target))
    return (directory / "f.yaml").read_text(encoding="utf-8")


def _refusal(value):
    """The refusal message for ``value``, or "" if it was allowed through."""
    try:
        _refuse_one_shot_iterator("ys", value)
    except UnrecordableArgumentError as exc:
        return str(exc)
    return ""


def test_range_x_and_y_saves_without_raising():
    # Arrange
    plot = lambda ax: ax.plot(range(10), range(10))  # noqa: E731
    # Act
    recipe = _save(plot)
    # Assert
    assert recipe != ""


def test_range_is_not_recorded_as_its_repr():
    # Arrange
    plot = lambda ax: ax.plot(range(10), range(10))  # noqa: E731
    # Act
    recipe = _save(plot)
    # Assert
    assert "range(" not in recipe


def test_range_x_with_list_y_saves():
    # Arrange
    plot = lambda ax: ax.plot(range(5), [i * 2 for i in range(5)])  # noqa: E731
    # Act
    recipe = _save(plot)
    # Assert
    assert "range(" not in recipe


def test_range_survives_a_bar_call():
    # Arrange
    plot = lambda ax: ax.bar(range(4), [1.0, 2.0, 3.0, 4.0])  # noqa: E731
    # Act
    recipe = _save(plot)
    # Assert
    assert "range(" not in recipe


def test_range_survives_set_xticks():
    # Arrange
    def plot(ax):
        ax.plot([0, 1], [0, 1])
        ax.set_xticks(range(2))

    # Act
    recipe = _save(plot)
    # Assert
    assert "range(" not in recipe


def test_dict_keys_are_materialised_not_stringified():
    # Arrange
    mapping = {"a": 1, "b": 2}
    plot = lambda ax: ax.bar(list(mapping.keys()), list(mapping.values()))  # noqa: E731
    # Act
    recipe = _save(plot)
    # Assert
    assert "dict_keys" not in recipe


def test_range_is_declared_re_iterable():
    # Arrange
    declared = RE_ITERABLE_SEQUENCES
    # Act
    covered = isinstance(range(3), declared)
    # Assert
    assert covered is True


def test_dict_keys_is_declared_re_iterable():
    # Arrange
    declared = RE_ITERABLE_SEQUENCES
    # Act
    covered = isinstance({}.keys(), declared)
    # Assert
    assert covered is True


def test_generator_is_refused():
    # Arrange
    value = (i for i in range(3))
    # Act
    message = _refusal(value)
    # Assert
    assert message != ""


def test_map_is_refused():
    # Arrange
    value = map(float, [1, 2, 3])
    # Act
    message = _refusal(value)
    # Assert
    assert message != ""


def test_zip_is_refused():
    # Arrange
    value = zip([1, 2], [3, 4])
    # Act
    message = _refusal(value)
    # Assert
    assert message != ""


def test_refusal_names_the_argument():
    # Arrange
    value = map(float, [1, 2])
    # Act
    message = _refusal(value)
    # Assert
    assert "'ys'" in message


def test_refusal_suggests_the_remedy():
    # Arrange
    value = map(float, [1, 2])
    # Act
    message = _refusal(value)
    # Assert
    assert "list(ys)" in message


def test_a_list_is_not_refused():
    # Arrange
    value = [1, 2, 3]
    # Act
    message = _refusal(value)
    # Assert
    assert message == ""


def test_a_string_is_not_refused():
    # Arrange
    value = "solid"
    # Act
    message = _refusal(value)
    # Assert
    assert message == ""


def test_a_range_is_not_refused():
    # Arrange
    value = range(3)
    # Act
    message = _refusal(value)
    # Assert
    assert message == ""


def test_a_scalar_is_not_refused():
    # Arrange
    value = 3.5
    # Act
    message = _refusal(value)
    # Assert
    assert message == ""


def test_one_shot_iterator_in_a_kwarg_is_refused():
    # Arrange
    fig, ax = fr.subplots(figsize=(2, 2))
    ax.plot([0, 1], [0, 1])
    # Act
    call = lambda: ax.legend(labels=map(str, range(1)))  # noqa: E731
    # Assert
    with pytest.raises(UnrecordableArgumentError):
        call()


# EOF
