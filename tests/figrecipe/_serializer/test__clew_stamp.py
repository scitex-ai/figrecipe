#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clew-tracked stamp on saved recipes.

A figure saved while a scitex-clew session is active must carry that fact
in the recipe (``figure.clew_tracked: true``); a save with no active session
leaves the recipe clean and never clears a stamp an earlier save recorded
(provenance is monotonic). The stamp is what the editor's tracked indicator
reads. Best-effort: clew is absent in this env, so the flag is set on the
record directly -- no mocks, the flag is plain record state.
"""

import matplotlib

matplotlib.use("Agg")


import figrecipe as fr
from figrecipe._serializer._clew import is_tracking


def _plotted_yaml(tmp_path, tracked):
    fig, ax = fr.subplots()
    ax.plot([0, 1], [1.5, 2.5])
    fig.record.clew_tracked = tracked
    path = tmp_path / "stamped.yaml"
    fig.save_recipe(path)
    return path


def test_save_writes_clew_tracked_for_a_stamped_record(tmp_path):
    # Arrange
    import yaml
    # Act
    path = _plotted_yaml(tmp_path, True)
    # Assert
    assert yaml.safe_load(path.read_text())["figure"].get("clew_tracked") is True


def test_save_leaves_untracked_recipe_clean(tmp_path):
    # Arrange
    # Act
    path = _plotted_yaml(tmp_path, False)
    # Assert
    assert "clew_tracked" not in path.read_text()


def test_clew_stamp_round_trips_through_load(tmp_path):
    # Arrange
    path = _plotted_yaml(tmp_path, True)
    # Act
    replayed, _ = fr.reproduce(str(path))
    # Assert
    assert replayed.record.clew_tracked is True


def test_is_tracking_is_false_without_clew():
    # Arrange
    # Act
    tracked = is_tracking()
    # Assert
    assert tracked is False
