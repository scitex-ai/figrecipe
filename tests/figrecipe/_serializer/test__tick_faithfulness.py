"""Tests for the record-time tick guards (refuse to save an unroundtrippable recipe).

Plain dicts in the recorded-call shape, no mocks. One assertion per test.
"""

from __future__ import annotations

import pytest

from figrecipe._serializer._tick_faithfulness import (
    assert_tick_call_faithful,
    assert_ticklabel_calls_faithful,
)


def _ticks(axis: str, positions, labels=None, call_id="set_ticks_000"):
    """A recorded set_[xy]ticks call."""
    call = {
        "function": f"set_{axis}ticks",
        "id": call_id,
        "args": [{"name": "ticks", "data": list(positions)}],
        "kwargs": {},
    }
    if labels is not None:
        call["kwargs"]["labels"] = list(labels)
    return call


def _ticklabels(axis: str, labels, call_id="set_ticklabels_000"):
    """A recorded set_[xy]ticklabels call."""
    return {
        "function": f"set_{axis}ticklabels",
        "id": call_id,
        "args": [{"name": "labels", "data": list(labels)}],
        "kwargs": {},
    }


# ---------------------------------------------------------------------------
# FR-FAITHFUL-TICKS — the existing per-call guard, still honoured
# ---------------------------------------------------------------------------


def test_mismatched_positions_and_labels_are_refused():
    # Arrange
    call = _ticks("x", [0, 1], labels=["8", "16", "24"])
    # Act
    # Assert
    with pytest.raises(ValueError, match="FR-FAITHFUL-TICKS"):
        assert_tick_call_faithful(call)


def test_matched_positions_and_labels_pass():
    # Arrange
    call = _ticks("x", [8, 16, 24], labels=["8", "16", "24"])
    # Act
    result = assert_tick_call_faithful(call)
    # Assert
    assert result is None


def test_positions_without_labels_pass():
    # Arrange: no labels kwarg means nothing to disagree with.
    call = _ticks("x", [0, 1, 2])
    # Act
    result = assert_tick_call_faithful(call)
    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# FR-FAITHFUL-TICKLABELS — the cross-call hole this change closes
# ---------------------------------------------------------------------------


def test_ticklabels_disagreeing_with_pinned_positions_are_refused():
    # Arrange: 3 positions pinned, then 19 labels handed to the same axis.
    calls = [_ticks("x", [0, 1, 2]), _ticklabels("x", [f"C{i}" for i in range(19)])]
    # Act
    # Assert
    with pytest.raises(ValueError, match="FR-FAITHFUL-TICKLABELS"):
        assert_ticklabel_calls_faithful(calls)


def test_the_refusal_names_the_reproduction_consequence():
    # Arrange
    calls = [_ticks("y", [0, 1]), _ticklabels("y", ["a", "b", "c"])]
    # Act
    # Assert
    with pytest.raises(ValueError, match="reproduces WITHOUT its y-axis labels"):
        assert_ticklabel_calls_faithful(calls)


def test_ticklabels_matching_pinned_positions_pass():
    # Arrange
    calls = [_ticks("x", [0, 1, 2]), _ticklabels("x", ["A", "B", "C"])]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


def test_a_later_set_ticks_supersedes_an_earlier_one():
    # Arrange: the axis is re-pinned to 2 before the labels arrive, so 2 labels
    # is correct even though an earlier call pinned 3.
    calls = [
        _ticks("x", [0, 1, 2], call_id="first"),
        _ticks("x", [0, 1], call_id="second"),
        _ticklabels("x", ["A", "B"]),
    ]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


def test_the_x_axis_does_not_constrain_the_y_axis():
    # Arrange: pinning x must not be compared against y's labels.
    calls = [_ticks("x", [0, 1, 2]), _ticklabels("y", ["a", "b"])]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# The case deliberately LEFT ALONE. Raising here would reject correct recipes:
# a bar chart's categorical positions or imshow's extent come from the PLOTTER,
# not from a recorded set_[xy]ticks, and a count comparison cannot tell that
# apart from a broken recipe.
# ---------------------------------------------------------------------------


def test_ticklabels_with_no_recorded_set_ticks_are_left_alone():
    # Arrange
    calls = [_ticklabels("x", [f"C{i}" for i in range(19)])]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


def test_ticklabels_after_an_unreadable_positions_arg_are_left_alone():
    # Arrange: a positions arg whose length cannot be determined must make the
    # guard silent, not make it guess.
    opaque = {"function": "set_xticks", "id": "opaque", "args": [{"ref": "x"}], "kwargs": {}}
    calls = [opaque, _ticklabels("x", ["a", "b", "c"])]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


def test_an_empty_call_list_passes():
    # Arrange
    calls = []
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


def test_unrelated_calls_are_ignored():
    # Arrange
    calls = [{"function": "plot", "id": "p", "args": [], "kwargs": {}}]
    # Act
    result = assert_ticklabel_calls_faithful(calls)
    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# Back-compat: the old private name must keep resolving from ._save, because
# tests/integration/test_tick_roundtrip.py imports it from there.
# ---------------------------------------------------------------------------


def test_the_old_private_name_still_imports_from_save():
    # Arrange
    from figrecipe._serializer._save import _assert_tick_call_faithful
    # Act
    actual = _assert_tick_call_faithful
    # Assert
    assert actual is assert_tick_call_faithful
