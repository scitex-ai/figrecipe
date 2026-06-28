#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""numpy-scalar argument serialization (figrecipe).

A numpy-int coordinate (e.g. ``ax.text(np.int64(0), ...)`` where the coord comes
from a numpy array / set_xticks) used to serialize as the STRING ``'0'`` — numpy
floats slipped through (np.float64 subclasses float) but numpy ints did not, so
they hit the ``str(value)`` fallback. A string coordinate turns the axis into a
category axis and breaks reproduce/compose
(``ConversionError: Failed to convert value(s) to axis units: '0'`` — surfaced by
NeuroVista Fig 02 panel c). These guard that numpy scalars round-trip as numbers.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import yaml

import figrecipe as fr


def _text_x(yaml_path):
    data = yaml.safe_load(Path(yaml_path).read_text())
    for ax_entry in data.get("axes", {}).values():
        for call in ax_entry.get("calls", []) + ax_entry.get("decorations", []):
            if call.get("function") == "text":
                for arg in call.get("args", []):
                    if arg.get("name") == "x":
                        return arg["data"]
    return None


@pytest.fixture()
def np_int_text_recipe(tmp_path):
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.bar([0, 1], [1.0, 2.0])
    ax.text(np.int64(0), 1.5, "lbl")
    out = tmp_path / "npint.png"
    try:
        fr.save(fig, str(out))
    except ValueError:
        pass
    plt.close("all")
    return tmp_path / "npint.yaml"


def test_numpy_int_text_x_serialized_as_number(np_int_text_recipe):
    # Arrange
    x = _text_x(np_int_text_recipe)
    # Act
    is_string = isinstance(x, str)
    # Assert
    assert not is_string


def test_numpy_int_text_x_replays_as_number(np_int_text_recipe):
    # Arrange
    _, rax = fr.reproduce(str(np_int_text_recipe))
    mpl_ax = getattr(rax, "ax", rax)
    labels = [t for t in mpl_ax.texts if t.get_text() == "lbl"]
    # Act
    replayed_x = labels[0].get_position()[0] if labels else None
    plt.close("all")
    # Assert
    assert not isinstance(replayed_x, str)


def test_numpy_str_label_saves_without_representer_crash(tmp_path):
    # Arrange — np.str_ (e.g. a label from a DataFrame column) used to crash
    # recipe->YAML save with ruamel RepresenterError (no representer for np.str_).
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2], [0, 1, 4], label=np.str_("P01"))
    ax.legend()
    out = tmp_path / "npstr.png"

    # Act
    saved = True
    try:
        fr.save(fig, str(out), validate=False, verbose=False)
    except Exception:
        saved = False
    plt.close("all")

    # Assert
    assert saved
