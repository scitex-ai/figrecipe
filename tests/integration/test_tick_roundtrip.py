"""Regression: set_xticks(positions, labels) must round-trip faithfully.

Guards the figrecipe<0.29.4 bug where tick POSITIONS serialized with a different
count/values than the labels (positions [8,16,24] -> [0,1]), breaking reproduce.
No mocks -- a real figure saved to tmp_path and the recipe/CSV read back.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr


def _tick_csv_values(tmp_path, stem):
    data_dir = tmp_path / f"{stem}_data"
    hits = [p for p in data_dir.iterdir() if "tick" in p.name and p.suffix == ".csv"]
    assert len(hits) == 1, [p.name for p in data_dir.iterdir()]
    return hits[0].read_text().split()


def test_set_xticks_positions_serialize_faithfully(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([8, 16, 24], [1, 2, 3], id="line")
    ax.set_xticks([8, 16, 24], labels=["8", "16", "24"])
    # Act
    fr.save(fig, str(tmp_path / "t.yaml"))
    # Assert: the real positions (not an index like [0,1]) are stored.
    assert _tick_csv_values(tmp_path, "t") == ["8", "16", "24"]


def test_set_xticks_recipe_reproduces_without_error(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([8, 16, 24], [1, 2, 3], id="line")
    ax.set_xticks([8, 16, 24], labels=["8", "16", "24"])
    fr.save(fig, str(tmp_path / "t2.yaml"))
    # Act
    fig2, ax2 = fr.reproduce(str(tmp_path / "t2.yaml"))
    # Assert: reproduced axis keeps the 3 tick positions.
    assert list(ax2._ax.get_xticks()) == [8.0, 16.0, 24.0]


def test_faithfulness_guard_raises_on_mismatched_tick_op():
    # Arrange
    import pytest

    from figrecipe._serializer._save import _assert_tick_call_faithful

    call = {
        "function": "set_xticks",
        "id": "set_xticks_000",
        "args": [{"name": "ticks", "data": [0, 1]}],
        "kwargs": {"labels": ["8", "16", "24"]},
    }
    # Act
    # Assert
    with pytest.raises(ValueError, match="FR-FAITHFUL-TICKS"):
        _assert_tick_call_faithful(call)


def test_faithfulness_guard_passes_on_matched_tick_op():
    # Arrange
    from figrecipe._serializer._save import _assert_tick_call_faithful

    call = {
        "function": "set_xticks",
        "id": "set_xticks_000",
        "args": [{"name": "ticks", "data": [8, 16, 24]}],
        "kwargs": {"labels": ["8", "16", "24"]},
    }
    # Act
    result = _assert_tick_call_faithful(call)
    # Assert
    assert result is None
