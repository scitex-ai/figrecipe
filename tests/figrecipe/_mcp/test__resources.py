#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MCP resources module.

Note: MCP tests require fastmcp>=2.0.0 which needs Python 3.10+.
Tests are skipped when fastmcp is not available.
"""

# Check if fastmcp is available (requires Python 3.10+)
import importlib.util

import pytest

HAS_FASTMCP = importlib.util.find_spec("fastmcp") is not None

requires_fastmcp = pytest.mark.skipif(
    not HAS_FASTMCP, reason="fastmcp not installed (requires Python 3.10+)"
)


@requires_fastmcp
class TestMCPResourcesExist:
    """Test that MCP resources are properly registered."""

    def test_resources_module_importable(self):
        """Test that _resources module can be imported."""
        from figrecipe._mcp._resources import register_resources

        assert callable(register_resources)

    def test_cheatsheet_content(self):
        """Test cheatsheet resource content."""
        from figrecipe._mcp._resources import CHEATSHEET

        assert "FigRecipe" in CHEATSHEET
        assert "fr.subplots()" in CHEATSHEET
        assert "fr.save(" in CHEATSHEET
        assert "fr.reproduce(" in CHEATSHEET

    def test_module_core_content(self):
        """Test module core resource content."""
        from figrecipe._mcp._resources import MODULE_CORE

        assert "fr.subplots()" in MODULE_CORE
        assert "ax.plot(" in MODULE_CORE
        assert "add_stat_annotation" in MODULE_CORE

    def test_mcp_spec_content(self):
        """Test MCP spec resource content."""
        from figrecipe._mcp._resources import MCP_SPEC

        assert "data_file" in MCP_SPEC
        assert "CSV" in MCP_SPEC
        assert "plots:" in MCP_SPEC
        assert "type:" in MCP_SPEC

    def test_mcp_spec_csv_priority(self):
        """Test that MCP spec emphasizes CSV column input."""
        from figrecipe._mcp._resources import MCP_SPEC

        # CSV should be recommended over inline
        assert "RECOMMENDED" in MCP_SPEC
        assert "data_file" in MCP_SPEC
        assert "column" in MCP_SPEC.lower()

    def test_integration_content(self):
        """Test integration resource content."""
        from figrecipe._mcp._resources import INTEGRATION

        assert "SciTeX" in INTEGRATION
        assert "stx.plt" in INTEGRATION or "scitex" in INTEGRATION.lower()


@requires_fastmcp
class TestMCPServerResources:
    """Test MCP server has resources registered."""

    @staticmethod
    def _get_resource_uris():
        import asyncio

        from figrecipe._mcp.server import mcp

        return [str(r.uri) for r in asyncio.run(mcp.list_resources())]

    def test_server_has_resources(self):
        """Test that MCP server has resources registered."""
        resources = self._get_resource_uris()
        assert len(resources) >= 4

    def test_cheatsheet_resource_registered(self):
        """Test cheatsheet resource is registered."""
        assert "figrecipe://cheatsheet" in self._get_resource_uris()

    def test_api_core_resource_registered(self):
        """Test API core resource is registered."""
        assert "figrecipe://api/core" in self._get_resource_uris()

    def test_mcp_spec_resource_registered(self):
        """Test MCP spec resource is registered."""
        assert "figrecipe://mcp-spec" in self._get_resource_uris()

    def test_integration_resource_registered(self):
        """Test integration resource is registered."""
        assert "figrecipe://integration" in self._get_resource_uris()

    def test_spec_schema_resource_registered(self):
        """Test spec-schema resource is registered."""
        assert "figrecipe://spec-schema" in self._get_resource_uris()


class TestBrandingInstructions:
    """Test branding module MCP instructions."""

    def test_instructions_include_csv_priority(self):
        """Test that MCP instructions include CSV priority."""
        from figrecipe._branding import get_mcp_instructions

        instructions = get_mcp_instructions()
        assert "CSV" in instructions
        assert "data_file" in instructions
        assert "PRIORITY" in instructions

    def test_instructions_list_resources(self):
        """Test that instructions list available resources."""
        from figrecipe._branding import get_mcp_instructions

        instructions = get_mcp_instructions()
        assert "cheatsheet" in instructions
        assert "mcp-spec" in instructions

    def test_instructions_list_tools(self):
        """Test that instructions list available tools."""
        from figrecipe._branding import get_mcp_instructions

        instructions = get_mcp_instructions()
        assert "plot" in instructions
        assert "reproduce" in instructions
        assert "compose" in instructions


@requires_fastmcp
class TestCSVColumnDocumentation:
    """Test CSV column input is properly documented."""

    def test_cheatsheet_has_csv_section(self):
        """Test cheatsheet documents CSV input."""
        from figrecipe._mcp._resources import CHEATSHEET

        assert "CSV" in CHEATSHEET
        assert "data_file" in CHEATSHEET

    def test_mcp_spec_has_csv_example(self):
        """Test MCP spec has CSV example."""
        from figrecipe._mcp._resources import MCP_SPEC

        assert "data_file:" in MCP_SPEC
        # Column name should be a string, not array
        assert "time" in MCP_SPEC or "column" in MCP_SPEC.lower()

    def test_output_files_documented(self):
        """Test that output files (_data directory) are documented."""
        from figrecipe._mcp._resources import CHEATSHEET

        assert "_data" in CHEATSHEET or "plot_data" in CHEATSHEET
        assert ".csv" in CHEATSHEET


# EOF
