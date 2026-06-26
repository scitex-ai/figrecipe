"""Tests for figrecipe._captions._manuscript_mode."""

import os

import matplotlib

matplotlib.use("Agg")

from figrecipe._captions._manuscript_mode import (
    is_manuscript_mode,
    manuscript_mode,
    set_manuscript_mode,
)


def test_default_is_off():
    # Arrange
    set_manuscript_mode(False)
    # Act
    active = is_manuscript_mode()
    # Assert
    assert active is False


def test_set_enables_mode():
    # Arrange
    set_manuscript_mode(False)
    # Act
    set_manuscript_mode(True)
    active = is_manuscript_mode()
    set_manuscript_mode(False)
    # Assert
    assert active is True


def test_context_manager_restores_previous_state():
    # Arrange
    set_manuscript_mode(False)
    # Act
    with manuscript_mode():
        inside = is_manuscript_mode()
    after = is_manuscript_mode()
    # Assert
    assert (inside, after) == (True, False)


def test_env_var_enables_mode():
    # Arrange
    set_manuscript_mode(False)
    prev = os.environ.get("FIGRECIPE_MANUSCRIPT_MODE")
    os.environ["FIGRECIPE_MANUSCRIPT_MODE"] = "1"
    # Act
    try:
        active = is_manuscript_mode()
    finally:
        if prev is None:
            os.environ.pop("FIGRECIPE_MANUSCRIPT_MODE", None)
        else:
            os.environ["FIGRECIPE_MANUSCRIPT_MODE"] = prev
    # Assert
    assert active is True


def test_add_caption_in_manuscript_mode_records_but_does_not_draw():
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], id="line")
    n_before = len(fig._fig.texts)
    # Act
    with manuscript_mode():
        fr.add_figure_caption(fig, "Off-canvas caption.")
    # Assert
    assert (fig.record.caption, len(fig._fig.texts)) == (
        "Off-canvas caption.",
        n_before,
    )


def test_add_caption_normally_draws_on_canvas():
    # Arrange
    import figrecipe as fr

    set_manuscript_mode(False)
    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], id="line")
    n_before = len(fig._fig.texts)
    # Act
    fr.add_figure_caption(fig, "Drawn caption.")
    # Assert
    assert len(fig._fig.texts) > n_before
