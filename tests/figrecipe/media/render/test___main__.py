#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test___main__.py
# ----------------------------------------
"""Tests for figrecipe.media.render.__main__ — the CLI entry point."""

import json
import os

import pytest

from figrecipe.media.render.__main__ import main


class TestMainClassify:
    """`classify` subcommand prints a JSON MediaRef."""

    def test_classify_known_file_prints_media_ref_json(self, capsys):
        # Arrange
        argv = ["classify", "data.csv"]
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert json.loads(captured.out)["type"] == "csv"

    def test_classify_unknown_file_prints_null(self, capsys):
        # Arrange
        argv = ["classify", "readme.txt"]
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert captured.out.strip() == "null"


class TestMainDetect:
    """`detect` subcommand prints a JSON list of MediaRefs."""

    def test_detect_prints_refs_for_matching_root(self, capsys):
        # Arrange
        argv = ["detect", "Saved /proj/fig.png", "--root", "/proj"]
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert json.loads(captured.out)[0]["path"] == "fig.png"


class TestMainShow:
    """`show` subcommand renders to the chosen target."""

    def test_show_markdown_prints_embed_string(self, capsys):
        # Arrange
        argv = ["show", "fig.png", "--target", "markdown"]
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert captured.out.strip() == "![fig.png](fig.png)"

    def test_show_terminal_writes_osc_escape_to_stdout(self, capsys):
        # Arrange
        argv = ["show", "/tmp/fig.png", "--target", "terminal"]
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert captured.out.startswith("\033]9998;media:")


class TestMainNoCommand:
    """Invoking with no subcommand prints help and does not raise."""

    def test_no_command_prints_usage_without_error(self, capsys):
        # Arrange
        argv = []
        # Act
        main(argv)
        captured = capsys.readouterr()
        # Assert
        assert "usage" in captured.out.lower()


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
