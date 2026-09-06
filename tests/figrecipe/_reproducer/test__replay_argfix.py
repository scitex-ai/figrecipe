#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._reproducer._replay_argfix: dash specs survive YAML.

matplotlib takes a custom dash pattern as ``(offset, (on, off, ...))``. YAML
has no tuples, so a recipe stores it as ``[0, [6, 4]]``, and matplotlib
rejects that list form ("Unrecognized linestyle") -- the line replayed solid
and a correct figure failed reproducibility validation (scitex-business,
2026-09-02; reproduced 2026-09-04, MSE 240). The fixup turns the two-element
``[number, sequence]`` shape back into the tuple and leaves everything else
alone; the controls below pin the "leaves everything else alone" half.
"""

import pytest

from figrecipe._reproducer._replay_argfix import (
    _normalise_dash_patterns,
    _normalise_dash_spec,
)


def test_import__reproducer__replay_argfix_module():
    # Arrange
    module_path = "figrecipe._reproducer._replay_argfix"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# ── the shape YAML produces becomes the tuple matplotlib takes ────────────────


def test_nested_list_dash_spec_becomes_offset_and_tuple():
    # Arrange
    from_yaml = [0, [6, 4]]
    # Act
    fixed = _normalise_dash_spec(from_yaml)
    # Assert
    assert fixed == (0, (6, 4))


def test_normalised_dash_spec_inner_sequence_is_a_tuple():
    """matplotlib's validator wants a real tuple inside, not a list."""
    # Arrange
    from_yaml = [0, [6, 4]]
    # Act
    inner = _normalise_dash_spec(from_yaml)[1]
    # Assert
    assert isinstance(inner, tuple)


def test_float_offset_is_kept():
    # Arrange
    from_yaml = [2.5, [3, 1, 1, 1]]
    # Act
    fixed = _normalise_dash_spec(from_yaml)
    # Assert
    assert fixed == (2.5, (3, 1, 1, 1))


# ── controls: anything that is not that shape passes through untouched ───────


@pytest.mark.parametrize(
    "value",
    ["--", "dashed", "-", None, [6, 4], (0, (6, 4)), [True, [1, 1]], [0, 6, 4]],
)
def test_other_linestyle_values_are_untouched(value):
    # Arrange
    original = value
    # Act
    fixed = _normalise_dash_spec(original)
    # Assert
    assert fixed == original


# ── applied to a call: every dash-carrying kwarg, and set_linestyle's arg ─────


@pytest.mark.parametrize("key", ["linestyle", "ls", "dashes"])
def test_dash_kwargs_are_normalised_on_any_call(key):
    # Arrange
    kwargs = {key: [0, [6, 4]], "color": "k"}
    # Act
    _args, fixed = _normalise_dash_patterns("plot", [], kwargs)
    # Assert
    assert fixed[key] == (0, (6, 4))


def test_non_dash_kwargs_are_left_alone():
    """Control: a two-element list under another key is data, not a dash."""
    # Arrange
    kwargs = {"xy": [0, [6, 4]]}
    # Act
    _args, fixed = _normalise_dash_patterns("annotate", [], kwargs)
    # Assert
    assert fixed["xy"] == [0, [6, 4]]


def test_set_linestyle_positional_arg_is_normalised():
    # Arrange
    args = [[0, [6, 4]]]
    # Act
    fixed_args, _kwargs = _normalise_dash_patterns("set_linestyle", args, {})
    # Assert
    assert fixed_args[0] == (0, (6, 4))


def test_positional_args_of_other_methods_are_left_alone():
    """Control: only set_linestyle/set_dashes take a dash spec positionally."""
    # Arrange
    args = [[0, [6, 4]]]
    # Act
    fixed_args, _kwargs = _normalise_dash_patterns("plot", args, {})
    # Assert
    assert fixed_args[0] == [0, [6, 4]]


# EOF
