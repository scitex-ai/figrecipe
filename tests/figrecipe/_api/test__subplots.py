#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A partial ``style=`` dict must override, not replace.

Reported by scitex-business on 2026-09-02 from real work: setting only the
Japanese font, ``fr.subplots(style={"font_family": ...})``, silently took the
rest of the SCITEX style with it. The keys left out did not fall back to the
loaded style either -- they fell back to literals hardcoded in
``apply_style_mm`` (``style.get("axis_font_size_pt", 8)`` where the style says
7.0), so a partial dict produced a third configuration belonging to neither.

Measured on develop before the fix:

    style not passed              axes.labelsize=7.0     spines.top=False
    style={"font_family": ...}    axes.labelsize=8.0     spines.top=False
    style={}                      axes.labelsize=medium  spines.top=True

The baseline in these tests is deliberately READ, not hardcoded: asserting
against a literal 7.0 would pin today's SCITEX values and fail whenever the
preset is retuned, which is a different thing from what is being tested here.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import pytest


def _rendered_style():
    """The three signals business compared: two sizes and a spine."""
    return (
        mpl.rcParams["axes.labelsize"],
        mpl.rcParams["xtick.labelsize"],
        mpl.rcParams["axes.spines.top"],
    )


@pytest.fixture
def baseline():
    """What fr.subplots() gives with no style= at all."""
    import figrecipe as fr

    with mpl.rc_context():
        fig, _ax = fr.subplots()
        got = _rendered_style()
    import matplotlib.pyplot as plt

    plt.close("all")
    return got


def _with_style(style):
    import figrecipe as fr

    with mpl.rc_context():
        fig, _ax = fr.subplots(style=style)
        got = _rendered_style()
    import matplotlib.pyplot as plt

    plt.close("all")
    return got


def test_import__api__subplots_module():
    # Arrange
    module_path = "figrecipe._api._subplots"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_a_one_key_style_keeps_the_rest_of_the_style(baseline):
    """The reported case: only the font was set, the rest went with it."""
    # Arrange
    partial = {"font_family": "DejaVu Sans"}
    # Act
    got = _with_style(partial)
    # Assert
    assert got == baseline


def test_an_empty_style_changes_nothing(baseline):
    """style={} said 'override nothing' and reverted everything."""
    # Arrange
    empty = {}
    # Act
    got = _with_style(empty)
    # Assert
    assert got == baseline


def test_the_full_spread_workaround_still_works(baseline):
    """business's workaround must keep working now the library does it."""
    # Arrange
    import figrecipe as fr

    spread = {**dict(fr.SCITEX_STYLE), "font_family": "DejaVu Sans"}
    # Act
    got = _with_style(spread)
    # Assert
    assert got == baseline


def test_an_override_actually_overrides(baseline):
    """Control: merging must not swallow the key the caller DID pass.

    Without this, a fix that ignored `style=` entirely would satisfy every
    assertion above perfectly.
    """
    # Arrange
    bigger = baseline[0] * 2 if isinstance(baseline[0], (int, float)) else 20.0
    # Act
    got = _with_style({"axis_font_size_pt": bigger})
    # Assert
    assert got[0] == bigger


def test_control_an_override_leaves_the_other_keys_alone(baseline):
    """The other half: overriding one key must not disturb its neighbours."""
    # Arrange
    bigger = baseline[0] * 2 if isinstance(baseline[0], (int, float)) else 20.0
    # Act
    got = _with_style({"axis_font_size_pt": bigger})
    # Assert
    assert (got[1], got[2]) == (baseline[1], baseline[2])


# EOF
