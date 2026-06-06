#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test_detect.py
# ----------------------------------------
"""Tests for figrecipe.media.render._detect — find media refs in text."""

import os

import pytest

from figrecipe.media.render import detect

_ROOT = "/home/user/proj"


class TestDetect:
    """detect: extract media file references from arbitrary text."""

    def test_single_absolute_path_detected_as_relative_ref(self):
        # Arrange
        text = "Saved to /home/user/proj/figures/plot.png"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs == [{"type": "image", "path": "figures/plot.png", "ext": ".png"}]

    def test_two_distinct_paths_yield_two_refs(self):
        # Arrange
        text = "Created /home/user/proj/fig.png and /home/user/proj/data.csv"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert {r["type"] for r in refs} == {"image", "csv"}

    def test_repeated_path_is_deduplicated_to_one_ref(self):
        # Arrange
        text = "/home/user/proj/fig.png and again /home/user/proj/fig.png"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert len(refs) == 1

    def test_none_root_path_returns_empty_list(self):
        # Arrange
        text = "some text"
        # Act
        refs = detect(text, root_path=None)
        # Assert
        assert refs == []

    def test_empty_text_returns_empty_list(self):
        # Arrange
        text = ""
        # Act
        refs = detect(text, root_path="/root")
        # Assert
        assert refs == []

    def test_text_without_matching_root_returns_empty_list(self):
        # Arrange
        text = "No file paths here"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs == []

    def test_non_media_extension_is_ignored(self):
        # Arrange
        text = "Wrote /home/user/proj/script.py"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs == []

    def test_trailing_slash_on_root_still_matches(self):
        # Arrange
        text = "File at /home/user/proj/fig.png"
        # Act
        refs = detect(text, root_path="/home/user/proj/")
        # Assert
        assert refs == [{"type": "image", "path": "fig.png", "ext": ".png"}]

    def test_filename_with_parentheses_preserved(self):
        # Arrange
        text = "Saved /home/user/proj/Figure(v2).png done"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs[0]["path"] == "Figure(v2).png"

    def test_filename_with_brackets_preserved(self):
        # Arrange
        text = "Saved /home/user/proj/data[final].csv done"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs[0]["path"] == "data[final].csv"

    def test_trailing_period_stripped_from_path(self):
        # Arrange
        text = "Saved to /home/user/proj/fig.png."
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert refs[0]["path"] == "fig.png"

    def test_comma_separated_paths_both_detected(self):
        # Arrange
        text = "Created /home/user/proj/a.png, /home/user/proj/b.csv"
        # Act
        refs = detect(text, root_path=_ROOT)
        # Assert
        assert len(refs) == 2


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
