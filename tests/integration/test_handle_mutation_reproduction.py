#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-time final-state re-read for artists mutated after draw (figrecipe).

Only the kwargs present at call time reach the recipe, so a later
``line.set_data()`` / ``line.set_color()`` is lost and the replay draws the
artist as first created (card
figrecipe-handle-mutation-after-draw-not-recorded-20260906). The repair
re-reads the live artist at save time and writes the final state back into
the record -- the same shape as the PR #426 visibility annotation.
Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import matplotlib

matplotlib.use("Agg")
import yaml

import figrecipe as fr


def _plot_calls(recipe_path):
    with open(recipe_path) as fh:
        data = yaml.safe_load(fh)
    calls = []
    for ax_entry in data.get("axes", {}).values():
        calls.extend(
            call
            for call in ax_entry.get("calls", [])
            if call.get("function") == "plot"
        )
    return calls


def test_set_data_after_draw_round_trip_is_valid(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9])
    fig.canvas.draw()
    line.set_data([1, 2, 3], [9, 4, 1])
    # Act -- raised ValueError (MSE 802.13 INVALID) while the mutation is lost.
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert
    assert result.valid is True


def test_set_data_replay_mse_is_zero(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9])
    fig.canvas.draw()
    line.set_data([1, 2, 3], [9, 4, 1])
    # Act
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert -- the card acceptance is 0.00, not merely below threshold.
    assert result.mse == 0.0


def test_set_data_final_values_reach_the_recipe(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9])
    fig.canvas.draw()
    line.set_data([1, 2, 3], [9, 4, 1])
    # Act
    _, yaml_path, _ = fr.save(fig, str(tmp_path / "fig.png"))
    (call,) = _plot_calls(yaml_path)
    # Assert -- the y sidecar CSV carries the FINAL values, not as-drawn
    # (no header row; matplotlib floatizes set_data ints, same as live).
    import csv

    y_ref = call["args"][1]["data"]
    with open(tmp_path / y_ref, newline="") as fh:
        values = [float(row[0]) for row in csv.reader(fh)]
    assert values == [9.0, 4.0, 1.0]


def test_set_color_after_draw_round_trip_is_valid(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9])
    fig.canvas.draw()
    line.set_color("red")
    # Act -- raised ValueError (MSE 563.65 INVALID) while the mutation is lost.
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert
    assert result.valid is True


def test_set_color_replay_mse_is_zero(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9])
    fig.canvas.draw()
    line.set_color("red")
    # Act
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert -- the card acceptance is 0.00, not merely below threshold.
    assert result.mse == 0.0


def test_untouched_plot_record_gains_no_keys(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    # Act
    _, yaml_path, _ = fr.save(fig, str(tmp_path / "fig.png"))
    (call,) = _plot_calls(yaml_path)
    # Assert -- the re-read pass writes nothing when nothing mutated.
    assert set(call["kwargs"]) == {"clip_on", "color"}
