"""Actual style discovery output and invalid-preset behavior."""

import json

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from figrecipe._cli import main
from figrecipe.styles._style_loader import load_preset


@pytest.mark.parametrize("name", ["SCITEX", "MATPLOTLIB"])
def test_style_text_contains_native_preset(name):
    # Arrange
    expected = json.loads(json.dumps(load_preset(name)))
    # Act
    result = CliRunner().invoke(main, ["style", "show", name])
    body = result.stdout.split("\n\n", 1)[1]
    # Assert
    assert (result.exit_code, YAML(typ="safe").load(body)) == (0, expected)


@pytest.mark.parametrize("args", [
    ["style", "show", "SciTeX-Missing-Style-7f8a"],
    ["style", "show", "SciTeX-Missing-Style-7f8a", "--json"],
    ["--json", "style", "show", "SciTeX-Missing-Style-7f8a"],
])
def test_missing_style_fails_loudly(args):
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(main, args)
    # Assert
    assert (result.exit_code, "Unknown style preset" in result.stderr) == (1, True)
