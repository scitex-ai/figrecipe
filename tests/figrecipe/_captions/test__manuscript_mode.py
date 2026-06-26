"""Tests for figrecipe._captions._manuscript_mode."""

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
    # Act / Assert
    assert is_manuscript_mode() is False


def test_set_toggles_on_and_off():
    # Arrange / Act
    set_manuscript_mode(True)
    try:
        # Assert
        assert is_manuscript_mode() is True
    finally:
        set_manuscript_mode(False)


def test_context_manager_restores_previous_state():
    # Arrange
    set_manuscript_mode(False)
    # Act
    with manuscript_mode():
        inside = is_manuscript_mode()
    # Assert
    assert inside is True
    assert is_manuscript_mode() is False


def test_env_var_enables_mode(monkeypatch):
    # Arrange
    set_manuscript_mode(False)
    monkeypatch.setenv("FIGRECIPE_MANUSCRIPT_MODE", "1")
    # Act / Assert
    assert is_manuscript_mode() is True


def test_add_caption_in_manuscript_mode_records_but_does_not_draw():
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], id="line")
    n_before = len(fig._fig.texts)
    # Act
    with manuscript_mode():
        fr.add_figure_caption(fig, "Off-canvas caption.")
    # Assert: caption recorded canonically, but no text drawn on the figure.
    assert fig.record.caption == "Off-canvas caption."
    assert len(fig._fig.texts) == n_before


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
