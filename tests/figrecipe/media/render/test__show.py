#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test_show.py
# ----------------------------------------
"""Tests for figrecipe.media.render._show — dispatch a file to a target."""

import json
import os

import pytest

from figrecipe.media.render import show


class TestShow:
    """show: render a media file to terminal, chat, or markdown."""

    def test_markdown_target_returns_image_embed(self):
        # Arrange
        path = "figure.png"
        # Act
        result = show(path, target="markdown")
        # Assert
        assert result == "![figure.png](figure.png)"

    def test_chat_target_returns_classified_json(self):
        # Arrange
        path = "data.csv"
        # Act
        parsed = json.loads(show(path, target="chat"))
        # Assert
        assert parsed["type"] == "csv"

    def test_terminal_target_returns_osc_escape(self):
        # Arrange
        path = "/tmp/test.png"
        # Act
        result = show(path, target="terminal")
        # Assert
        assert result.startswith("\033]9998;media:")

    def test_terminal_target_writes_osc_escape_to_stdout(self, capsys):
        # Arrange
        path = "/tmp/test.png"
        # Act
        show(path, target="terminal")
        captured = capsys.readouterr()
        # Assert
        assert "\033]9998;media:" in captured.out

    def test_unknown_target_raises_value_error(self):
        # Arrange
        path = "fig.png"
        # Act
        # Assert
        with pytest.raises(ValueError, match="Unknown target"):
            show(path, target="invalid")


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
