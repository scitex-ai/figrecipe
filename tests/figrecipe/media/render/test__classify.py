#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test_classify.py
# ----------------------------------------
"""Tests for figrecipe.media.render._classify — classify files by media type."""

import os

import pytest

from figrecipe.media.render import MEDIA_EXTENSIONS, classify


class TestClassify:
    """classify: map a file path to its media-type descriptor."""

    @pytest.mark.parametrize(
        "path,expected_type",
        [
            ("figure.png", "image"),
            ("plot.jpg", "image"),
            ("photo.jpeg", "image"),
            ("anim.gif", "image"),
            ("icon.svg", "image"),
            ("img.webp", "image"),
            ("img.bmp", "image"),
            ("paper.pdf", "pdf"),
            ("data.csv", "csv"),
            ("results.tsv", "csv"),
            ("chart.html", "plotly"),
            ("diagram.mmd", "mermaid"),
        ],
    )
    def test_known_extension_yields_expected_media_type(self, path, expected_type):
        # Arrange / parametrized path + expected type
        # Act
        ref = classify(path)
        # Assert
        assert ref is not None and ref["type"] == expected_type

    def test_known_extension_preserves_original_path(self):
        # Arrange
        path = "figures/sub/plot.png"
        # Act
        ref = classify(path)
        # Assert
        assert ref is not None and ref["path"] == path

    def test_unknown_extension_returns_none(self):
        # Arrange
        path = "readme.txt"
        # Act
        result = classify(path)
        # Assert
        assert result is None

    def test_path_without_extension_returns_none(self):
        # Arrange
        path = "noext"
        # Act
        result = classify(path)
        # Assert
        assert result is None

    def test_uppercase_extension_classified_case_insensitively(self):
        # Arrange
        path = "FIGURE.PNG"
        # Act
        ref = classify(path)
        # Assert
        assert ref is not None and ref["type"] == "image"

    def test_every_media_extension_set_is_non_empty(self):
        # Arrange
        empty = [t for t, exts in MEDIA_EXTENSIONS.items() if len(exts) == 0]
        # Act / inspection already done above
        # Assert
        assert empty == []

    def test_media_extensions_mapping_is_immutable(self):
        # Arrange
        new_value = frozenset({".xyz"})
        # Act
        # Assert
        with pytest.raises(TypeError):
            MEDIA_EXTENSIONS["new_type"] = new_value


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
