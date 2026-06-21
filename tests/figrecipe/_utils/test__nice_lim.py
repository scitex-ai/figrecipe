"""GH #140: tick-friendly axis-limit helper ``figrecipe.nice_lim``.

Each test focuses on one observable property of ``nice_lim`` and is
AAA-structured (``# Arrange`` / ``# Act`` / ``# Assert`` markers) to
satisfy STX-TQ002 / STX-TQ007 (PA-307 §3 test-quality).
"""

from __future__ import annotations

import pytest


def test_timeline_day_max_snaps_up_to_next_round_to():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [0, 367]
    # Act
    lo, hi = fr.nice_lim(data, lower=0, round_to=10)
    # Assert
    assert (lo, hi) == (0.0, 370.0)


def test_auto_round_to_picks_data_order_of_magnitude():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [0, 367]
    # Act
    lo, hi = fr.nice_lim(data)
    # Assert
    assert (lo, hi) == (0.0, 400.0)


def test_count_histogram_max_does_not_touch_top_spine():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    counts = [0, 0, 1, 4, 19]
    # Act
    _, hi = fr.nice_lim(counts, round_to=5)
    # Assert
    assert hi == 20.0


def test_explicit_lower_zero_is_honoured_for_negative_friendly_data():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [3, 27]
    # Act
    lo, _ = fr.nice_lim(data, lower=0, round_to=10)
    # Assert
    assert lo == 0.0


def test_lower_none_snaps_left_edge_below_negative_data_min():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [-3, 27]
    # Act
    lo, _ = fr.nice_lim(data, lower=None, round_to=10)
    # Assert
    assert lo == -10.0


def test_exact_round_max_is_pushed_one_step_off_the_spine():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [0, 20]
    # Act
    _, hi = fr.nice_lim(data, lower=0, round_to=10)
    # Assert
    assert hi == 30.0


def test_empty_data_returns_unit_step_window_without_crashing():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    # Act
    lo, hi = fr.nice_lim([], lower=0, round_to=10)
    # Assert
    assert (lo, hi) == (0.0, 10.0)


def test_all_nan_data_returns_unit_step_window_without_crashing():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    import math

    data = [math.nan, math.nan]
    # Act
    lo, hi = fr.nice_lim(data, lower=0, round_to=5)
    # Assert
    assert (lo, hi) == (0.0, 5.0)


def test_data_max_equals_zero_returns_one_round_to_step_high():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    data = [0, 0, 0]
    # Act
    _, hi = fr.nice_lim(data, lower=0, round_to=10)
    # Assert
    assert hi == 10.0


def test_negative_round_to_raises_value_error():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    # Act
    # Assert
    with pytest.raises(ValueError):
        fr.nice_lim([1, 2, 3], round_to=-5)


def test_zero_round_to_raises_value_error():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    # Act
    # Assert
    with pytest.raises(ValueError):
        fr.nice_lim([1, 2, 3], round_to=0)


def test_nice_lim_is_exposed_at_top_level_per_pep_562():
    # Arrange
    fr = pytest.importorskip("figrecipe")
    # Act
    nl = fr.nice_lim
    # Assert
    assert callable(nl)
