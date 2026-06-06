#!/usr/bin/env python3
# File: tests/figrecipe/media/render/test_mcp_server.py
# ----------------------------------------
"""Tests for figrecipe.media.render.mcp_server — MCP tool wrappers."""

import asyncio
import json
import os

import pytest

from figrecipe.media.render import mcp_server

_HAS_FASTMCP = mcp_server.FASTMCP_AVAILABLE


def _tool_fn(name):
    """Return the underlying Python function for a registered MCP tool."""
    tools = asyncio.run(mcp_server.mcp.get_tools())
    return tools[name].fn


class TestModuleContract:
    """mcp_server exposes a stable import-level contract."""

    def test_module_exports_fastmcp_available_flag(self):
        # Arrange
        flag = mcp_server.FASTMCP_AVAILABLE
        # Act
        is_bool = isinstance(flag, bool)
        # Assert
        assert is_bool is True

    def test_mcp_object_present_iff_fastmcp_available(self):
        # Arrange
        has_mcp = mcp_server.mcp is not None
        # Act
        matches_flag = has_mcp == mcp_server.FASTMCP_AVAILABLE
        # Assert
        assert matches_flag is True


@pytest.mark.skipif(not _HAS_FASTMCP, reason="fastmcp not installed")
class TestServerWithFastMCP:
    """When fastmcp is installed, the server is named for media rendering."""

    def test_server_is_named_scitex_media_render(self):
        # Arrange
        server = mcp_server.mcp
        # Act
        name = server.name
        # Assert
        assert name == "scitex-media-render"

    def test_render_classify_tool_returns_media_ref_json(self):
        # Arrange
        classify = _tool_fn("render_classify")
        # Act
        result = json.loads(classify("data.csv"))
        # Assert
        assert result["type"] == "csv"

    def test_render_classify_tool_returns_null_for_unknown(self):
        # Arrange
        classify = _tool_fn("render_classify")
        # Act
        result = classify("readme.txt")
        # Assert
        assert result == "null"

    def test_render_detect_tool_returns_refs_json(self):
        # Arrange
        detect = _tool_fn("render_detect")
        # Act
        result = json.loads(detect("Saved /proj/fig.png", root_path="/proj"))
        # Assert
        assert result[0]["path"] == "fig.png"

    def test_render_show_tool_returns_markdown_embed(self):
        # Arrange
        show = _tool_fn("render_show")
        # Act
        result = show("fig.png", target="markdown")
        # Assert
        assert result == "![fig.png](fig.png)"


@pytest.mark.skipif(_HAS_FASTMCP, reason="fastmcp installed — main() starts server")
class TestServerWithoutFastMCP:
    """Without fastmcp, main() reports the missing dependency and exits."""

    def test_main_exits_when_fastmcp_missing(self):
        # Arrange
        # Act
        # Assert
        with pytest.raises(SystemExit):
            mcp_server.main()


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
