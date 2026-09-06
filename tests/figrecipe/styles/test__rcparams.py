#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe.styles._rcparams: capture must yield YAML-safe values.

matplotlib validates ``lines.solid_capstyle`` and friends into ``CapStyle`` /
``JoinStyle`` enums, and those enums SUBCLASS ``str`` -- so they slip past an
``isinstance(value, str)`` test and reach the YAML writer as enum objects. The
writer then raises ``RepresenterError: cannot represent an object:
<CapStyle.round: 'round'>`` and the recipe is lost: the png is written before
the crash, the yaml never is. Every ``seaborn-v0_8-*`` style sets one of these,
so ``plt.style.use("seaborn-v0_8-whitegrid")`` was enough to make ``fr.save``
raise (measured 2026-09-06).
"""

import enum

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import pytest

from figrecipe.styles._rcparams import (
    _from_primitive,
    _to_primitive,
    capture_rcparams_delta,
)


def test_import_styles__rcparams_module():
    # Arrange
    module_path = "figrecipe.styles._rcparams"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# ── an rcParam enum becomes its plain value ──────────────────────────────────


def test_capstyle_enum_becomes_its_string_value():
    # Arrange
    from matplotlib._enums import CapStyle

    value = CapStyle.round
    # Act
    out = _to_primitive(value)
    # Assert
    assert out == "round"


def test_capstyle_enum_does_not_survive_as_an_enum():
    """The bug: it IS a str, so the str branch used to hand it back whole."""
    # Arrange
    from matplotlib._enums import CapStyle

    value = CapStyle.round
    # Act
    out = _to_primitive(value)
    # Assert
    assert not isinstance(out, enum.Enum)


def test_joinstyle_enum_becomes_its_string_value():
    # Arrange
    from matplotlib._enums import JoinStyle

    value = JoinStyle.bevel
    # Act
    out = _to_primitive(value)
    # Assert
    assert out == "bevel"


def test_captured_delta_holds_no_enum_values():
    """The whole snapshot, not one key: nothing YAML cannot represent."""
    # Arrange
    with mpl.rc_context():
        mpl.rcParams["lines.solid_capstyle"] = "round"
        mpl.rcParams["lines.dash_joinstyle"] = "bevel"
        # Act
        delta = capture_rcparams_delta()
    # Assert
    assert not [v for v in delta.values() if isinstance(v, enum.Enum)]


def test_captured_capstyle_round_trips_back_into_rcparams():
    """Control: the primitive must still be a value matplotlib accepts."""
    # Arrange
    with mpl.rc_context():
        mpl.rcParams["lines.solid_capstyle"] = "round"
        delta = capture_rcparams_delta()
    # Act
    with mpl.rc_context():
        mpl.rcParams["lines.solid_capstyle"] = _from_primitive(
            delta["lines.solid_capstyle"]
        )
        restored = str(mpl.rcParams["lines.solid_capstyle"])
    # Assert
    assert "round" in restored


# ── controls: the other value kinds are unchanged by the enum branch ─────────


@pytest.mark.parametrize(
    "value", ["round", 4.0, 12, True, None, ["a", "b"], [1.5, 2.5]]
)
def test_plain_values_pass_through_unchanged(value):
    # Arrange
    original = value
    # Act
    out = _to_primitive(original)
    # Assert
    assert out == original


def test_cycler_is_still_captured_as_its_own_marker():
    """Control: the pre-existing Cycler branch must not be shadowed."""
    # Arrange
    from cycler import cycler

    value = cycler(color=["#aa0000", "#0000aa"])
    # Act
    out = _to_primitive(value)
    # Assert
    assert "__cycler__" in out


def test_cycler_round_trips_back_to_a_cycler():
    # Arrange
    from cycler import Cycler, cycler

    value = cycler(color=["#aa0000", "#0000aa"])
    # Act
    out = _from_primitive(_to_primitive(value))
    # Assert
    assert isinstance(out, Cycler)


# EOF
