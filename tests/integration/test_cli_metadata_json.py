"""Real read-only CLI commands honor root and local JSON flags alike."""

import json

import pytest
from click.testing import CliRunner

import figrecipe as fr
from figrecipe._cli import main


@pytest.fixture
def recipe(tmp_path):
    # Arrange
    target = tmp_path / "figure.png"
    fig, ax = fr.subplots()
    ax.plot([0, 1], [1, 3])
    # Act
    fr.save(fig, target)
    # Assert: fixture creation uses ordinary save validation.
    return target.with_suffix(".yaml")


@pytest.mark.parametrize("command", [
    ["show-version"], ["show-version", "--full"],
    ["style", "list"], ["style", "show", "SCITEX"],
    ["list-python-apis", "--root-only"],
])
@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_metadata_json_matches_local_contract(command, position):
    # Arrange
    args = command
    runner = CliRunner()
    local = runner.invoke(main, [*args, "--json"])
    variants = {
        "root": ["--json", *args],
        "local": [*args, "--json"],
        "both": ["--json", *args, "--json"],
    }
    # Act
    actual = runner.invoke(main, variants[position])
    # Assert
    assert (actual.exit_code, json.loads(actual.stdout)) == (
        local.exit_code, json.loads(local.stdout),
    )


@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_recipe_metadata_json_matches_local_contract(recipe, position):
    # Arrange
    args = ["info", str(recipe)]
    runner = CliRunner()
    local = runner.invoke(main, [*args, "--json"])
    variants = {
        "root": ["--json", *args],
        "local": [*args, "--json"],
        "both": ["--json", *args, "--json"],
    }
    # Act
    actual = runner.invoke(main, variants[position])
    # Assert
    assert (actual.exit_code, json.loads(actual.stdout)) == (
        local.exit_code, json.loads(local.stdout),
    )
