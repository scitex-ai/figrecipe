#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper-completeness: element-producing methods that were forwarded to raw
matplotlib (and vanished on replay) now round-trip.

arrow / axline / broken_barh / table record + reproduce directly. bar_label is
frozen into recorded annotate() calls. secondary_xaxis/secondary_yaxis record
the plain-location case; only the custom-transform-functions case (not
serializable) warns instead of silently vanishing.
"""

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr


def _reproduce(fig, tmp_path, name):
    try:
        fr.save(fig, str(tmp_path / (name + ".png")))
    except ValueError:
        pass  # geometry/recording asserted regardless of MSE-validation outcome
    _, rax = fr.reproduce(str(tmp_path / (name + ".yaml")))
    return getattr(rax, "ax", rax)


def _axes():
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig, ax


def test_arrow_round_trips(tmp_path):
    # Arrange
    fig, ax = _axes()
    ax.arrow(0.1, 0.1, 0.5, 0.5, head_width=0.05)
    # Act
    mpl_ax = _reproduce(fig, tmp_path, "arrow")
    # Assert
    assert len(mpl_ax.patches) == 1


def test_axline_round_trips(tmp_path):
    # Arrange
    fig, ax = _axes()
    ax.axline((0, 0), (1, 1))
    # Act
    mpl_ax = _reproduce(fig, tmp_path, "axline")
    # Assert
    assert len(mpl_ax.lines) == 1


def test_broken_barh_round_trips(tmp_path):
    # Arrange
    fig, ax = _axes()
    ax.broken_barh([(0.1, 0.3), (0.5, 0.2)], (0.2, 0.1))
    # Act
    mpl_ax = _reproduce(fig, tmp_path, "broken_barh")
    # Assert
    assert len(mpl_ax.collections) == 1


def test_table_round_trips(tmp_path):
    # Arrange
    fig, ax = _axes()
    ax.table(cellText=[["a", "b"], ["c", "d"]], loc="center")
    # Act
    mpl_ax = _reproduce(fig, tmp_path, "table")
    # Assert
    assert len(mpl_ax.tables) == 1


def test_bar_label_round_trips(tmp_path):
    # Arrange -- bar_label draws Annotations; they are frozen into recorded
    # annotate() calls so the labels reproduce without the live BarContainer.
    fig, ax = _axes()
    bars = ax.bar([0, 1, 2], [0.3, 0.6, 0.2])
    ax.bar_label(bars, fmt="%.1f")
    # Act
    mpl_ax = _reproduce(fig, tmp_path, "bar_label")
    reproduced = {t.get_text() for t in mpl_ax.texts if t.get_text()}
    # Assert
    assert {"0.3", "0.6", "0.2"}.issubset(reproduced)


def test_secondary_xaxis_plain_records_without_warning():
    # Arrange -- a plain secondary_xaxis(location) mirrors the primary and is
    # recorded by location, so it must NOT emit the not-recorded warning.
    import warnings

    fig, ax = _axes()
    ax.plot([0, 1], [0, 1])
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax.secondary_xaxis("top")
    # Assert
    assert not any("NOT recorded" in str(w.message) for w in caught)


def test_secondary_xaxis_with_functions_warns():
    # Arrange -- custom transform callables are not serializable.
    fig, ax = _axes()
    ax.plot([0, 1], [0, 1])
    # Act
    # a functions= secondary axis cannot be recorded -> must warn (see Assert)
    # Assert
    with pytest.warns(UserWarning, match="NOT recorded"):
        ax.secondary_xaxis("top", functions=(lambda x: x * 2, lambda x: x / 2))


def test_secondary_yaxis_plain_records_without_warning():
    # Arrange
    import warnings

    fig, ax = _axes()
    ax.plot([0, 1], [0, 1])
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax.secondary_yaxis("right")
    # Assert
    assert not any("NOT recorded" in str(w.message) for w in caught)
