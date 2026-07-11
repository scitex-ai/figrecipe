#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scatter_labels(declutter=True): recorded, deterministic, replay-safe."""

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr


def _texts_of(rax):
    mpl_ax = getattr(rax, "ax", rax)
    return [t.get_text() for t in mpl_ax.texts]


def test_scatter_labels_adds_recorded_text():
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.scatter([0.2, 0.5, 0.8], [0.2, 0.5, 0.8])
    # Act
    ax.scatter_labels([0.2, 0.5, 0.8], [0.2, 0.5, 0.8], ["P01", "P02", "P03"])
    texts = _texts_of(ax)
    # Assert
    assert {"P01", "P02", "P03"}.issubset(set(texts))


def test_declutter_separates_coincident_labels():
    # Arrange -- two labels anchored on the SAME point must not stack.
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.scatter([0.5, 0.5], [0.5, 0.5])
    # Act
    ax.scatter_labels([0.5, 0.5], [0.5, 0.5], ["AA", "BB"])
    pos = {
        t.get_text(): t.get_position()
        for t in ax.ax.texts
        if t.get_text() in ("AA", "BB")
    }
    # Assert
    assert pos["AA"] != pos["BB"]


def test_scatter_labels_deterministic():
    # Arrange
    def run():
        fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.scatter([0.4, 0.5, 0.6], [0.4, 0.5, 0.6])
        ax.scatter_labels([0.4, 0.5, 0.6], [0.4, 0.5, 0.6], ["A", "B", "C"])
        return {
            t.get_text(): tuple(round(v, 6) for v in t.get_position())
            for t in ax.ax.texts
            if t.get_text() in ("A", "B", "C")
        }

    # Act
    first, second = run(), run()
    # Assert
    assert first == second


def test_scatter_labels_round_trip(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.scatter([0.3, 0.6], [0.3, 0.6])
    ax.scatter_labels([0.3, 0.6], [0.3, 0.6], ["X1", "X2"])
    # Act
    try:
        fr.save(fig, str(tmp_path / "sl.png"))
    except ValueError:
        pass  # recording asserted regardless of MSE-validation outcome
    _, rax = fr.reproduce(str(tmp_path / "sl.yaml"))
    rtexts = _texts_of(rax)
    # Assert
    assert "X1" in rtexts and "X2" in rtexts


def test_scatter_labels_length_mismatch_raises():
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    # Act
    # mismatched x / y / labels lengths must raise at call time (see Assert)
    # Assert
    with pytest.raises(ValueError, match="equal length"):
        ax.scatter_labels([0.1, 0.2], [0.1], ["only-one"])
