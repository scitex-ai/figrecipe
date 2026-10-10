#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for ax.add_collection() (figrecipe).

A LineCollection added via add_collection() was forwarded to matplotlib but
never recorded, so it vanished on replay and the figure failed save-time
reproducibility (card figrecipe-unrecorded-axes-artist-methods-20261005).
Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import matplotlib

matplotlib.use("Agg")
import pytest
import yaml
from matplotlib.collections import LineCollection, PathCollection

import figrecipe as fr


def _find_collection_spec(recipe_path):
    with open(recipe_path) as fh:
        data = yaml.safe_load(fh)
    for ax_entry in data.get("axes", {}).values():
        for call in ax_entry.get("calls", []) + ax_entry.get("decorations", []):
            if call.get("function") == "add_collection":
                return call["kwargs"]["collection_spec"]
    return None


def test_add_collection_round_trip_is_valid(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_collection(LineCollection([[(0, 0), (3, 9)]], colors=["red"]))
    # Act -- raised ValueError (MSE 389.34 INVALID) while unrecorded.
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert
    assert result.valid is True


def test_add_collection_replay_mse_is_zero(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_collection(LineCollection([[(0, 0), (3, 9)]], colors=["red"]))
    # Act
    _, _, result = fr.save(fig, str(tmp_path / "fig.png"))
    # Assert -- the card acceptance is 0.00, not merely below threshold.
    assert result.mse == 0.0


def test_add_collection_recorded_in_recipe(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.add_collection(LineCollection([[(0, 0), (3, 9)]], colors=["red"]))
    # Act
    _, yaml_path, _ = fr.save(fig, str(tmp_path / "fig.png"))
    spec = _find_collection_spec(yaml_path)
    # Assert
    assert (spec or {}).get("type") == "LineCollection"


def test_add_collection_non_line_collection_fails_loud(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    # Act
    # a non-LineCollection would be dropped on replay (see Assert)
    # Assert
    with pytest.raises(ValueError, match="LineCollection"):
        ax.add_collection(PathCollection([]))


def test_figure_without_these_methods_has_no_new_spec_keys(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    # Act
    fr.save(fig, str(tmp_path / "fig.png"))
    with open(tmp_path / "fig.yaml") as fh:
        recipe_text = fh.read()
    # Assert -- the new record keys appear only when the methods are used.
    assert "line_spec" not in recipe_text and "collection_spec" not in recipe_text
