"""Tests for figrecipe._captions._validate (FR-CAP-001: no \\footnote in captions)."""

import matplotlib

matplotlib.use("Agg")

import pytest

from figrecipe._captions._validate import (
    FootnoteInCaptionError,
    check_caption_latex_safe,
)


def test_plain_caption_passes():
    # Arrange
    text = "Two-condition comparison (n=3)."
    # Act
    result = check_caption_latex_safe(text, "the figure caption")
    # Assert
    assert result is None


def test_none_is_noop():
    # Arrange
    text = None
    # Act
    result = check_caption_latex_safe(text, "the figure caption")
    # Assert
    assert result is None


def test_footnote_command_raises():
    # Arrange
    text = "Throughput\\footnote{disclosure} per condition."
    # Act
    # Assert
    with pytest.raises(FootnoteInCaptionError):
        check_caption_latex_safe(text, "the figure caption")


def test_footnotemark_also_raises():
    # Arrange
    text = "See above\\footnotemark."
    # Act
    # Assert
    with pytest.raises(FootnoteInCaptionError):
        check_caption_latex_safe(text, "the figure caption")


def test_error_names_the_location():
    # Arrange
    text = "Panel\\footnote{x}."
    # Act
    # Assert
    with pytest.raises(FootnoteInCaptionError, match="the panel B caption"):
        check_caption_latex_safe(text, "the panel B caption")


def test_plain_word_footnote_is_allowed():
    # Arrange: the English word, NOT the \footnote command, must NOT trip.
    text = "The footnote describes the cohort."
    # Act
    result = check_caption_latex_safe(text, "the figure caption")
    # Assert
    assert result is None


def test_add_figure_caption_rejects_footnote():
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], id="line")
    # Act
    # Assert
    with pytest.raises(FootnoteInCaptionError):
        fr.add_figure_caption(fig, "x\\footnote{y}")


def test_save_rejects_footnote_naming_the_file(tmp_path):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], id="line")
    fig.record.caption = "x\\footnote{y}"
    # Act
    # Assert
    with pytest.raises(FootnoteInCaptionError, match="bad.yaml"):
        fr.save(fig, str(tmp_path / "bad.yaml"))
