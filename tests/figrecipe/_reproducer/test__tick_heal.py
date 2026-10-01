"""Tests for figrecipe._reproducer._tick_heal (legacy mismatched-tick heal)."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from figrecipe._recorder import CallRecord
from figrecipe._reproducer._core import _replay_call
from figrecipe._reproducer._replay_action import ReplayAction, ReplayArgs
from figrecipe._reproducer._tick_heal import heal_tick_call

CATEGORY_LABELS = [f"CAT{i:02d}" for i in range(19)]


@pytest.fixture
def ax():
    """A default axes, whose automatic tick count differs from 19."""
    fig, axes = plt.subplots()
    yield axes
    plt.close(fig)


def _heal_quietly(ax, method_name, args, kwargs=None):
    """Call heal_tick_call without letting its warning escape.

    Tests that assert on the RESULT must not also assert on the warning —
    the repo allows one assertion per test — so the warning is swallowed
    here and verified by its own dedicated test instead.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return heal_tick_call(ax, method_name, args, kwargs or {})


# --------------------------------------------------------------------------
# set_[xy]ticks: positions and labels are index-paired, so truncation keeps
# every surviving label on a position the recipe authored.
# --------------------------------------------------------------------------
def test_set_xticks_mismatch_warns_about_truncation():
    # Arrange
    args = ([0, 1],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    # Assert
    with pytest.warns(UserWarning, match="truncated to 2"):
        heal_tick_call(None, "set_xticks", args, kwargs)


def test_set_xticks_mismatch_truncates_positions():
    # Arrange
    args = ([0, 1],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert len(result.args[0]) == 2


def test_set_xticks_mismatch_truncates_labels():
    # Arrange
    args = ([0, 1],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert len(result.kwargs["labels"]) == 2


def test_set_xticks_truncation_keeps_leading_positions():
    # Arrange
    args = ([10, 20, 30],)
    kwargs = {"labels": ["ten", "twenty", "thirty", "forty", "fifty"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert list(result.args[0]) == [10, 20, 30]


def test_set_xticks_truncation_keeps_leading_labels_in_order():
    # Arrange: a truncation that reordered or reindexed the survivors would
    # mislabel the axis just as surely as pinning to automatic ticks does.
    args = ([10, 20, 30],)
    kwargs = {"labels": ["ten", "twenty", "thirty", "forty", "fifty"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert list(result.kwargs["labels"]) == ["ten", "twenty", "thirty"]


def test_set_xticks_matched_counts_pass_through_unchanged():
    # Arrange
    args = ([8, 16, 24],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert (result.args[0], result.kwargs["labels"]) == ([8, 16, 24], ["8", "16", "24"])


def test_set_xticks_matched_counts_record_no_reason():
    # Arrange
    args = ([8, 16, 24],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    result = _heal_quietly(None, "set_xticks", args, kwargs)
    # Assert
    assert result.reason is None


def test_non_tick_method_passes_arguments_through():
    # Arrange
    args = ([1, 2, 3],)
    kwargs = {"color": "red"}
    # Act
    result = _heal_quietly(None, "plot", args, kwargs)
    # Assert
    assert (result.args, result.kwargs) == (args, kwargs)


def test_non_tick_method_is_applied():
    # Arrange
    args = ([1, 2, 3],)
    kwargs = {"color": "red"}
    # Act
    result = _heal_quietly(None, "plot", args, kwargs)
    # Assert
    assert result.action is ReplayAction.APPLY


# --------------------------------------------------------------------------
# set_[xy]ticklabels: only the labels are authored, so a count mismatch means
# the recipe does not say where they belong. Dropping beats inventing.
# --------------------------------------------------------------------------
def test_set_xticklabels_mismatch_warns_that_it_is_dropping(ax):
    # Arrange
    labels = CATEGORY_LABELS
    # Act
    # Assert
    with pytest.warns(UserWarning, match="DROPPING"):
        heal_tick_call(ax, "set_xticklabels", (labels,), {})


def test_set_xticklabels_mismatch_is_skipped(ax):
    # Arrange
    labels = CATEGORY_LABELS
    # Act
    result = _heal_quietly(ax, "set_xticklabels", (labels,))
    # Assert
    assert result.action is ReplayAction.SKIP


def test_set_xticklabels_mismatch_reason_names_the_mislabeling(ax):
    # Arrange
    labels = CATEGORY_LABELS
    # Act
    result = _heal_quietly(ax, "set_xticklabels", (labels,))
    # Assert
    assert "MISLABEL" in result.reason


def test_set_yticklabels_mismatch_reason_names_the_y_axis(ax):
    # Arrange: the message must name the axis it is about, not a hardcoded x.
    labels = ["a", "b"] * 9
    # Act
    result = _heal_quietly(ax, "set_yticklabels", (labels,))
    # Assert
    assert "MISLABEL the y axis" in result.reason


def test_set_xticklabels_matching_count_is_applied(ax):
    # Arrange: pin 3 positions so the counts agree — the normal path for a
    # recipe written by a current figrecipe.
    ax.set_xticks([0, 1, 2])
    # Act
    result = _heal_quietly(ax, "set_xticklabels", (["A", "B", "C"],))
    # Assert
    assert result.action is ReplayAction.APPLY


def test_set_xticklabels_matching_count_leaves_arguments_untouched(ax):
    # Arrange
    ax.set_xticks([0, 1, 2])
    labels = ["A", "B", "C"]
    # Act
    result = _heal_quietly(ax, "set_xticklabels", (labels,))
    # Assert
    assert result.args == (labels,)


# --------------------------------------------------------------------------
# End to end through _replay_call. The unit tests above can pass while the
# CALLER ignores `action` and replays the call anyway — which is precisely the
# bug being fixed — so this asserts on the rendered axis, not on the verdict.
# --------------------------------------------------------------------------
def test_replay_warns_when_dropping_legacy_ticklabels(ax):
    # Arrange
    call = CallRecord(
        id="legacy-1",
        function="set_xticklabels",
        args=[{"data": CATEGORY_LABELS}],
        kwargs={},
    )
    # Act
    # Assert
    with pytest.warns(UserWarning, match="DROPPING"):
        _replay_call(ax, call)


def test_replay_does_not_mislabel_axis_for_legacy_ticklabels(ax):
    # Arrange: a legacy recipe holding 19 labels and no positions. Before this
    # fix the leading labels were pinned onto matplotlib's automatic positions,
    # producing an axis that looked right and was not.
    call = CallRecord(
        id="legacy-1",
        function="set_xticklabels",
        args=[{"data": CATEGORY_LABELS}],
        kwargs={},
    )
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _replay_call(ax, call)
    ax.figure.canvas.draw()
    # Assert
    assert not any(
        t.get_text().startswith("CAT") for t in ax.get_xticklabels()
    )


def test_replay_applies_ticklabels_when_counts_agree(ax):
    # Arrange: the honest path must be untouched by the fix.
    ax.set_xticks([0, 1, 2])
    call = CallRecord(
        id="current-1",
        function="set_xticklabels",
        args=[{"data": ["A", "B", "C"]}],
        kwargs={},
    )
    # Act
    _replay_call(ax, call)
    ax.figure.canvas.draw()
    # Assert
    assert [t.get_text() for t in ax.get_xticklabels()] == ["A", "B", "C"]


# --------------------------------------------------------------------------
# The declared shape itself. A SKIP with no reason, or a bare string in
# `action`, must fail where it is built rather than three layers downstream.
# --------------------------------------------------------------------------
def test_skip_without_reason_is_rejected():
    # Arrange
    action = ReplayAction.SKIP
    # Act
    # Assert
    with pytest.raises(ValueError, match="must carry a reason"):
        ReplayArgs(action=action, args=(), kwargs={})


def test_non_enum_action_is_rejected():
    # Arrange
    action = "skip"
    # Act
    # Assert
    with pytest.raises(TypeError, match="must be a ReplayAction"):
        ReplayArgs(action=action, args=(), kwargs={})


def test_skipped_is_true_for_a_skip_result():
    # Arrange
    reason = "the recipe does not say where the labels belong"
    # Act
    result = ReplayArgs(
        action=ReplayAction.SKIP, args=(), kwargs={}, reason=reason
    )
    # Assert
    assert result.skipped is True


def test_skipped_is_false_for_an_apply_result():
    # Arrange
    args = ([1, 2],)
    # Act
    result = ReplayArgs.apply(args=args, kwargs={})
    # Assert
    assert result.skipped is False
