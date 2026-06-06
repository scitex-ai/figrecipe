#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test_targets.py
# ----------------------------------------
"""Tests for figrecipe.media.render._targets — per-target formatters."""

import base64
import json
import os

import pytest

from figrecipe.media.render._targets import _to_chat, _to_markdown, _to_terminal

_OSC_PREFIX = "\033]9998;media:"


def _decode_osc(osc: str) -> dict:
    b64 = osc[len(_OSC_PREFIX) : -1]
    return json.loads(base64.b64decode(b64))


class TestToTerminal:
    """_to_terminal: format a file as an OSC escape for the terminal frontend."""

    def test_osc_escape_starts_with_media_prefix(self):
        # Arrange
        path = "/tmp/test.png"
        # Act
        osc = _to_terminal(path)
        # Assert
        assert osc.startswith(_OSC_PREFIX)

    def test_osc_escape_ends_with_bel_terminator(self):
        # Arrange
        path = "/tmp/test.png"
        # Act
        osc = _to_terminal(path)
        # Assert
        assert osc.endswith("\007")

    def test_osc_payload_classifies_known_image_type(self):
        # Arrange
        path = "/tmp/test.png"
        # Act
        payload = _decode_osc(_to_terminal(path))
        # Assert
        assert payload["type"] == "image"

    def test_osc_payload_includes_resolved_url(self):
        # Arrange
        path = "/tmp/test.png"
        # Act
        payload = _decode_osc(_to_terminal(path))
        # Assert
        assert "url" in payload

    def test_unknown_extension_payload_typed_as_file(self):
        # Arrange
        path = "/tmp/readme.txt"
        # Act
        payload = _decode_osc(_to_terminal(path))
        # Assert
        assert payload["type"] == "file"


class TestToChat:
    """_to_chat: format a file as a MediaRef dict for the chat pane."""

    def test_relative_path_classified_by_type(self):
        # Arrange
        path = "figures/plot.png"
        # Act
        ref = _to_chat(path)
        # Assert
        assert ref == {"type": "image", "path": "figures/plot.png", "ext": ".png"}

    def test_absolute_path_made_relative_to_root(self):
        # Arrange
        path = "/home/user/proj/fig.png"
        # Act
        ref = _to_chat(path, root_path="/home/user/proj")
        # Assert
        assert ref["path"] == "fig.png"

    def test_unknown_extension_typed_as_file(self):
        # Arrange
        path = "readme.txt"
        # Act
        ref = _to_chat(path)
        # Assert
        assert ref["type"] == "file"


class TestToMarkdown:
    """_to_markdown: format a file as a markdown embed or link."""

    def test_image_renders_as_embed_with_filename_alt(self):
        # Arrange
        path = "figure.png"
        # Act
        md = _to_markdown(path)
        # Assert
        assert md == "![figure.png](figure.png)"

    def test_image_renders_with_custom_alt_text(self):
        # Arrange
        path = "figure.png"
        # Act
        md = _to_markdown(path, alt="My plot")
        # Assert
        assert md == "![My plot](figure.png)"

    def test_non_image_renders_as_plain_link(self):
        # Arrange
        path = "data.csv"
        # Act
        md = _to_markdown(path)
        # Assert
        assert md == "[data.csv](data.csv)"

    def test_pdf_renders_as_plain_link(self):
        # Arrange
        path = "paper.pdf"
        # Act
        md = _to_markdown(path)
        # Assert
        assert md == "[paper.pdf](paper.pdf)"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
