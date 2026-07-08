#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper-completeness: newly-recorded methods round-trip; un-serializable
draw methods warn instead of silently vanishing on reproduce().

arrow / axline / broken_barh / table were forwarded to raw matplotlib and
vanished on replay; they now record + reproduce. bar_label / secondary_xaxis
/ secondary_yaxis cannot round-trip (live container / transform callables) so
they must WARN on use.
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


def test_bar_label_warns_not_recorded():
    # Arrange
    fig, ax = _axes()
    bars = ax.bar([0, 1], [0.3, 0.6])
    # Act
    # bar_label takes a live BarContainer -> not recordable -> must warn (Assert)
    # Assert
    with pytest.warns(UserWarning, match="NOT recorded"):
        ax.bar_label(bars)


def test_secondary_xaxis_warns_not_recorded():
    # Arrange
    fig, ax = _axes()
    # Act
    # secondary_xaxis takes transform callables -> not recordable -> warn (Assert)
    # Assert
    with pytest.warns(UserWarning, match="NOT recorded"):
        ax.secondary_xaxis("top")


def test_secondary_yaxis_warns_not_recorded():
    # Arrange
    fig, ax = _axes()
    # Act
    # secondary_yaxis takes transform callables -> not recordable -> warn (Assert)
    # Assert
    with pytest.warns(UserWarning, match="NOT recorded"):
        ax.secondary_yaxis("right")
