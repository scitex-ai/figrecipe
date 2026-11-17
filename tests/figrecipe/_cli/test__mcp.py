"""Actual local MCP catalog discovery through root and local JSON options."""

import json

import pytest
from click.testing import CliRunner

from figrecipe._cli import main
from figrecipe._cli._mcp import _get_tools_dict
from figrecipe._mcp.server import mcp


@pytest.mark.parametrize(("filters", "prefix"), [
    ([], ""), (["--module", "plt"], "plt_"),
    (["--module", "diagram"], "diagram_"),
])
@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_mcp_json_names_match_native_registry(filters, prefix, position):
    # Arrange
    expected = {name for name in _get_tools_dict(mcp) if name.startswith(prefix)}
    args = ["mcp", "list-tools", *filters]
    variants = {"root": ["--json", *args], "local": [*args, "--json"],
                "both": ["--json", *args, "--json"]}
    # Act
    result = CliRunner().invoke(main, variants[position])
    data = json.loads(result.stdout)
    actual = {tool["name"] for module in data["modules"].values() for tool in module["tools"]}
    # Assert
    assert (result.exit_code, data["total"], actual) == (0, len(expected), expected)


def test_mcp_text_remains_available():
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(main, ["mcp", "list-tools", "--module", "plt"])
    # Assert
    assert (result.exit_code, "FigRecipe MCP:" in result.stdout) == (0, True)


def test_mcp_unknown_module_fails():
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(main, ["--json", "mcp", "list-tools", "--module", "missing7f8a"])
    # Assert
    assert (result.exit_code, "Unknown module" in result.stderr) == (1, True)
