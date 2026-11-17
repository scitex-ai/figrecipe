"""GUI JSON controls using real Click dispatch and isolated runtime state."""

import json

import pytest
from click.testing import CliRunner

from figrecipe._cli import main


@pytest.mark.parametrize("command", [
    ["gui", "open"], ["gui", "serve"], ["gui"], ["start-gui"],
])
@pytest.mark.parametrize("source_kind", ["none", "recipe", "browse", "project"])
@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_gui_json_dry_run_has_only_expected_payload(tmp_path, command, source_kind, position):
    # Arrange
    recipe = tmp_path / "figure.yaml"
    recipe.write_text("axes: {}\n")
    browse = tmp_path / "browse"
    browse.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (project / "recipe.yaml").write_text("axes: {}\n")
    state = tmp_path / "gui-state.json"
    source_args = {
        "none": [], "recipe": [str(recipe)],
        "browse": [str(browse)], "project": [str(project)],
    }
    arguments = [*command, *source_args[source_kind], "--dry-run"]
    variants = {
        "root": ["--json", *arguments],
        "local": [*arguments, "--json"],
        "both": ["--json", *arguments, "--json"],
    }
    payload = {
        "host": "127.0.0.1", "port": 31296,
        "source": {"none": None, "recipe": str(recipe), "browse": None, "project": str(project)}[source_kind],
        "working_dir": {"none": None, "recipe": None, "browse": str(browse), "project": None}[source_kind],
    }
    payload.update({"serve": {"would_serve": True}}.get(command[-1], {"would_open": True, "desktop": False}))
    # Act
    result = CliRunner().invoke(main, variants[position], env={"FIGRECIPE_GUI_STATE": str(state)})
    # Assert
    assert {
        "exit": result.exit_code,
        "payload": json.loads(result.stdout),
        "state_created": state.exists(),
        "recipe": recipe.read_text(),
        "project_recipe": (project / "recipe.yaml").read_text(),
        "browse_contents": list(browse.iterdir()),
    } == {
        "exit": 0, "payload": payload, "state_created": False,
        "recipe": "axes: {}\n", "project_recipe": "axes: {}\n", "browse_contents": [],
    }


@pytest.mark.parametrize("command,payload", [
    (["gui", "status"], {"running": False}),
    (["gui", "stop", "--dry-run"], {"stopped": False, "running": False}),
])
@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_gui_json_absent_state_is_readable_without_runtime_actions(tmp_path, command, payload, position):
    # Arrange
    state = tmp_path / "absent-state.json"
    variants = {"root": ["--json", *command], "local": [*command, "--json"], "both": ["--json", *command, "--json"]}
    # Act
    result = CliRunner().invoke(main, variants[position], env={"FIGRECIPE_GUI_STATE": str(state)})
    # Assert
    assert (result.exit_code, json.loads(result.stdout), state.exists()) == (0, payload, False)


@pytest.mark.parametrize("command,verb", [
    (["gui", "open"], "open"), (["gui", "serve"], "serve"),
    (["gui"], "open"), (["start-gui"], "open"),
])
def test_gui_plain_directory_dry_run_preserves_human_output(tmp_path, command, verb):
    # Arrange
    browse = tmp_path / "browse"
    browse.mkdir()
    state = tmp_path / "gui-state.json"
    # Act
    result = CliRunner().invoke(main, [*command, str(browse), "--dry-run"], env={"FIGRECIPE_GUI_STATE": str(state)})
    # Assert
    assert (result.exit_code, result.stdout, state.exists()) == (
        0, f"Browsing directory: {browse}\nWould {verb} editor at http://127.0.0.1:31296.\n", False,
    )


@pytest.mark.parametrize("command", [
    ["gui", "open"], ["gui", "serve"], ["gui"], ["start-gui"],
])
@pytest.mark.parametrize("port", [-1, 0, 65536])
@pytest.mark.parametrize("prefix", [[], ["--json"]])
def test_gui_invalid_fixed_port_is_refused_before_runtime_actions(tmp_path, command, port, prefix):
    # Arrange
    state = tmp_path / "gui-state.json"
    args = [*prefix, *command, "--dry-run", "--port", str(port)]
    # Act
    result = CliRunner().invoke(main, args, env={"FIGRECIPE_GUI_STATE": str(state)})
    # Assert
    assert {
        "exit": result.exit_code,
        "stdout": result.stdout,
        "range_error": result.stderr.endswith(
            f"Error: Invalid value for '--port': {port} is not in the range 1<=x<=65535.\n"
        ),
        "state_created": state.exists(),
    } == {"exit": 2, "stdout": "", "range_error": True, "state_created": False}


@pytest.mark.parametrize("command", [
    ["gui", "open"], ["gui", "serve"], ["gui"], ["start-gui"],
])
@pytest.mark.parametrize("port", [1, 31296, 65535])
def test_gui_fixed_port_boundaries_remain_available_in_dry_run(tmp_path, command, port):
    # Arrange
    state = tmp_path / "gui-state.json"
    payload = {"host": "127.0.0.1", "port": port, "source": None, "working_dir": None}
    payload.update({"serve": {"would_serve": True}}.get(command[-1], {"would_open": True, "desktop": False}))
    # Act
    result = CliRunner().invoke(main, [*command, "--dry-run", "--port", str(port), "--json"], env={"FIGRECIPE_GUI_STATE": str(state)})
    # Assert
    assert (result.exit_code, json.loads(result.stdout), state.exists()) == (0, payload, False)
