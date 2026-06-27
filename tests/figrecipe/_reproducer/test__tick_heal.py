"""Tests for figrecipe._reproducer._tick_heal (legacy mismatched-tick heal)."""

import matplotlib

matplotlib.use("Agg")

from figrecipe._reproducer._tick_heal import heal_tick_call


def test_set_xticks_mismatch_truncates_to_common_length():
    # Arrange: legacy recipe with 2 positions but 3 labels.
    args = ([0, 1],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    new_args, new_kwargs = heal_tick_call(None, "set_xticks", args, kwargs)
    # Assert
    assert (len(new_args[0]), len(new_kwargs["labels"])) == (2, 2)


def test_set_xticks_matched_counts_unchanged():
    # Arrange
    args = ([8, 16, 24],)
    kwargs = {"labels": ["8", "16", "24"]}
    # Act
    new_args, new_kwargs = heal_tick_call(None, "set_xticks", args, kwargs)
    # Assert
    assert (new_args[0], new_kwargs["labels"]) == ([8, 16, 24], ["8", "16", "24"])


def test_non_tick_method_passes_through():
    # Arrange
    args = ([1, 2, 3],)
    kwargs = {"color": "red"}
    # Act
    new_args, new_kwargs = heal_tick_call(None, "plot", args, kwargs)
    # Assert
    assert (new_args, new_kwargs) == (args, kwargs)
