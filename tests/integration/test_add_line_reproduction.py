#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for ax.add_line()/ax.add_artist() (figrecipe).

A Line2D added via add_line()/add_artist() was forwarded to matplotlib but
never recorded, so it vanished on replay and the figure failed save-time
reproducibility (card figrecipe-unrecorded-axes-artist-methods-20261005).
Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import pytest
import yaml
from matplotlib.lines import Line2D

import figrecipe as fr


def _find_line_spec(recipe_path, function):
    with open(recipe_path) as fh:
        data = yaml.safe_load(fh)
    for ax_entry in data.get("axes", {}).values():
        for call in ax_entry.get("calls", []) + ax_entry.get("decorations", []):
            if call.get("function") == function:
                return call["kwargs"]["line_spec"]
    return None


def test_add_line_round_trip_is_valid(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_line(Line2D([0, 3], [0, 9]))
    # Act -- raised ValueError (MSE 391.64 INVALID) while unrecorded.
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert
    assert result.valid is True


def test_add_line_replay_mse_is_zero(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_line(Line2D([0, 3], [0, 9]))
    # Act
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert -- the card acceptance is 0.00, not merely below threshold.
    assert result.mse == 0.0


def test_add_line_recorded_in_recipe(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_line(Line2D([0, 3], [0, 9]))
    # Act
    _, yaml_path, _ = fr.save(fig, str(tmp_path / "fig.png"))
    spec = _find_line_spec(yaml_path, "add_line")
    # Assert
    assert (spec or {}).get("type") == "Line2D"


def test_add_artist_line_round_trip_is_valid(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_artist(Line2D([0, 3], [0, 9]))
    # Act -- raised ValueError (MSE 371.02 INVALID) while unrecorded.
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert
    assert result.valid is True


def test_add_artist_line_replay_mse_is_zero(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_artist(Line2D([0, 3], [0, 9]))
    # Act
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert -- the card acceptance is 0.00, not merely below threshold.
    assert result.mse == 0.0


def test_add_artist_non_line_fails_loud(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    # Act
    # a patch via add_artist would be dropped on replay (see Assert)
    # Assert
    with pytest.raises(ValueError, match="add_patch"):
        ax.add_artist(mpatches.Rectangle((0, 0), 1, 1))
