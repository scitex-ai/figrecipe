#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay of stale stringified axis limits (figrecipe).

Recipes written before native numpy-scalar serialization (figrecipe < 0.28.21)
could store a numeric axis limit / line position as the STRING ``'0'`` (an
``np.int64`` coordinate hit the ``str(value)`` fallback). On replay matplotlib
cannot convert a raw string to axis units and raises
``ConversionError: Failed to convert value(s) to axis units`` -- which broke
reproduce/compose of such recipes (NeuroVista Fig 02 composite). The reproducer
now coerces stringified numbers on the inherently-numeric axis methods; this
guards that a stale recipe still reproduces with the recorded numeric limits.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
import yaml

import figrecipe as fr


@pytest.fixture()
def stale_string_xlim_recipe(tmp_path):
    """A recipe whose ``set_xlim`` args were stringified (pre-0.28.21 artifact)."""
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2], [0.0, 1.0, 4.0])
    ax.set_xlim(0, 2)
    try:
        fr.save(fig, str(tmp_path / "fig.png"))
    except ValueError:
        pass
    plt.close("all")
    recipe = tmp_path / "fig.yaml"
    data = yaml.safe_load(recipe.read_text())
    for ax_entry in data.get("axes", {}).values():
        for call in ax_entry.get("calls", []) + ax_entry.get("decorations", []):
            if call.get("function") == "set_xlim":
                for arg in call.get("args", []):
                    if "data" in arg:
                        arg["data"] = str(arg["data"])
    recipe.write_text(yaml.safe_dump(data))
    return recipe


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_stale_stringified_xlim_replays_as_numeric_limits(stale_string_xlim_recipe):
    # Arrange
    _, rax = fr.reproduce(str(stale_string_xlim_recipe))
    mpl_ax = getattr(rax, "ax", rax)
    # Act
    xlim = mpl_ax.get_xlim()
    plt.close("all")
    # Assert
    assert xlim == (0.0, 2.0)
