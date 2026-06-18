#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for an ax.vlines() schematic (figrecipe).

``ax.vlines`` / ``ax.hlines`` draw data-coordinate line collections from arrays
(a plotting primitive), but they were absent from ``PLOTTING_METHODS``, so the
recording wrapper never intercepted them: the lines drew on the live figure yet
were NEVER written to the recipe (``calls: []``). On reproduce the whole tick
field vanished, leaving the panel empty and a large *same-size* pixel MSE
(NeuroVista Fig 05a Design-A-vs-B schematic: panels rendered blank).

These guards build a minimal 2-panel schematic with the exact primitives the
real figure uses -- ``vlines`` event ticks, ``axvspan`` train/test blocks,
``axvline`` cutoffs, and colored ``text`` labels -- and assert the recipe both
records the ``vlines`` and reproduces clean (no ``*-not-reproduced`` artefact).
"""

import matplotlib

matplotlib.use("Agg")
import numpy as np

import figrecipe as fr


def _build_schematic():
    """Two-panel schematic: vlines ticks + spans + cutoffs + colored text."""
    fig, axes = fr.subplots(nrows=2, ncols=1, axes_width_mm=80, axes_height_mm=20)

    event_days = np.sort(np.random.default_rng(0).uniform(10.0, 290.0, size=40))
    train_color = "#1F77B4"
    test_color = "#FF4632"

    ax_a = axes[0]
    ax_a.set_title("Design A -- time-mixed 5-fold CV", loc="left")
    for i, day in enumerate(event_days):
        ax_a.vlines(day, 0.0, 1.0, colors=train_color if i % 2 else test_color)
    ax_a.set_xlim(0, 300)
    ax_a.set_ylim(-0.1, 1.2)
    ax_a.set_yticks([])

    ax_b = axes[1]
    ax_b.set_title("Design B -- Karoly prospective", loc="left")
    ax_b.axvspan(100, 200, facecolor=train_color, alpha=0.18)
    ax_b.axvspan(200, 300, facecolor=test_color, alpha=0.18)
    ax_b.axvline(100, color="black", linestyle="--", linewidth=0.7)
    ax_b.axvline(200, color="black", linestyle="--", linewidth=0.7)
    for day in event_days:
        color = train_color if day < 200 else test_color
        ax_b.vlines(day, 0.0, 1.0, colors=color)
    ax_b.text(150, 1.06, "train", ha="center", va="bottom", color=train_color)
    ax_b.text(250, 1.06, "test", ha="center", va="bottom", color=test_color)
    ax_b.set_xlim(0, 300)
    ax_b.set_ylim(-0.1, 1.2)
    ax_b.set_yticks([])
    return fig


def test_vlines_are_recorded_in_recipe(tmp_path):
    # Arrange
    fig = _build_schematic()
    # Act
    _img, yaml_path, _result = fr.save(fig, str(tmp_path / "schematic.png"))
    recorded = [c["function"] for c in fr.info(yaml_path)["calls"]]
    # Assert
    assert recorded.count("vlines") == 80


def test_vlines_schematic_reproduces_without_divergence(tmp_path):
    # Arrange
    fig = _build_schematic()
    # Act
    fr.save(fig, str(tmp_path / "schematic.png"))
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))
