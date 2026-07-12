#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test file for: src/figrecipe/_cli/_gui.py

"""Tests for the `figrecipe gui` command group (real Click invocation).

Ported from scitex-writer's tests/scitex_writer/_cli/commands/test_gui.py
idiom (card figrecipe-gui-cli-noun-verb-normalize-20260712): CLI-level
tests use `--dry-run` to avoid actually starting a Django server, and an
isolated per-test state file via `FIGRECIPE_GUI_STATE` so `status`/`stop`
tests never touch a real running server on the host.
"""

import json
import os

import pytest
from click.testing import CliRunner

from figrecipe._cli import _gui_runtime, main
from figrecipe._cli._gui import gui


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def isolated_state(tmp_path):
    state_file = tmp_path / "gui.json"
    os.environ["FIGRECIPE_GUI_STATE"] = str(state_file)
    yield state_file
    os.environ.pop("FIGRECIPE_GUI_STATE", None)


class TestGuiGroupRegistration:
    """Test the `gui` group's wiring onto the top-level CLI."""

    def test_gui_group_registered_on_main(self):
        # Arrange
        commands = main.commands
        # Act
        present = "gui" in commands
        # Assert
        assert present

    def test_gui_group_has_canonical_verbs(self):
        # Arrange
        verbs = set(gui.commands)
        # Act
        canonical = {"open", "serve", "status", "stop"}
        # Assert
        assert canonical <= verbs

    def test_start_gui_alias_registered_on_main(self):
        # Arrange
        commands = main.commands
        # Act
        present = "start-gui" in commands
        # Assert
        assert present

    def test_start_gui_alias_is_hidden(self):
        # Arrange
        command = main.commands["start-gui"]
        # Act
        hidden = command.hidden
        # Assert
        assert hidden


class TestStartGuiDeprecatedAlias:
    """Test the deprecated `start-gui` -> `gui open` forwarding alias."""

    def test_start_gui_warns_deprecated(self, runner):
        # Arrange
        args = ["start-gui", "--dry-run"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert "deprecated" in result.output

    def test_start_gui_dry_run_exits_zero(self, runner):
        # Arrange
        args = ["start-gui", "--dry-run"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert result.exit_code == 0

    def test_start_gui_dry_run_forwards_to_open(self, runner):
        # Arrange
        # `--json` payload and the deprecation warning may share the same
        # output stream under CliRunner's default mixing, so assert the
        # forwarded payload key by substring rather than a strict
        # json.loads() of the whole (possibly-mixed) output.
        args = ["start-gui", "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert '"would_open": true' in result.output


class TestGuiOpenDryRun:
    """Test `gui open --dry-run` (never actually starts a server)."""

    def test_gui_open_dry_run_exits_zero(self, runner):
        # Arrange
        args = ["gui", "open", "--dry-run"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert result.exit_code == 0

    def test_gui_open_dry_run_json_shape(self, runner):
        # Arrange
        args = ["gui", "open", "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_open"]


class TestGuiServeDryRun:
    """Test `gui serve --dry-run` (never actually starts a server)."""

    def test_gui_serve_dry_run_exits_zero(self, runner):
        # Arrange
        args = ["gui", "serve", "--dry-run"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert result.exit_code == 0

    def test_gui_serve_dry_run_json_shape(self, runner):
        # Arrange
        args = ["gui", "serve", "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_serve"]


class TestGuiStatus:
    """Test `gui status` against an isolated (never-running) state file."""

    def test_gui_status_json_not_running(self, runner, isolated_state):
        # Arrange
        args = ["gui", "status", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload == {"running": False}

    def test_gui_status_human_not_running(self, runner, isolated_state):
        # Arrange
        args = ["gui", "status"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert "Not running" in result.output


class TestGuiStop:
    """Test `gui stop` idempotency and the --yes confirmation gate."""

    def test_gui_stop_json_idempotent(self, runner, isolated_state):
        # Arrange
        args = ["gui", "stop", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload == {"stopped": False, "running": False}

    def test_gui_stop_dry_run_reports_would_stop(self, runner, isolated_state):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 5050, "127.0.0.1", None, isolated_state)
        args = ["gui", "stop", "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_stop"]

    def test_gui_stop_dry_run_leaves_server_state(self, runner, isolated_state):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 5050, "127.0.0.1", None, isolated_state)
        args = ["gui", "stop", "--dry-run"]
        # Act
        runner.invoke(main, args)
        # Assert
        assert isolated_state.exists()

    def test_gui_stop_without_yes_refuses_exit_code(self, runner, isolated_state):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 5050, "127.0.0.1", None, isolated_state)
        args = ["gui", "stop"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert result.exit_code == 2

    def test_gui_stop_without_yes_refuses_message(self, runner, isolated_state):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 5050, "127.0.0.1", None, isolated_state)
        args = ["gui", "stop"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert "without --yes" in result.output

    def test_gui_stop_without_yes_leaves_state(self, runner, isolated_state):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 5050, "127.0.0.1", None, isolated_state)
        args = ["gui", "stop"]
        # Act
        runner.invoke(main, args)
        # Assert
        assert isolated_state.exists()


class TestGuiDefaultGroup:
    """`gui` falls back to `open` when the first token isn't a known verb."""

    def test_bare_source_dry_run_resolves_to_open(self, runner, tmp_path):
        # Arrange
        source = tmp_path / "figure.yaml"
        source.write_text("")
        args = ["gui", str(source), "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_open"]

    def test_bare_source_dry_run_carries_source_path(self, runner, tmp_path):
        # Arrange
        source = tmp_path / "figure.yaml"
        source.write_text("")
        args = ["gui", str(source), "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["source"] == str(source)

    def test_bare_no_args_dry_run_resolves_to_open(self, runner):
        # Arrange
        args = ["gui", "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_open"]

    def test_explicit_serve_verb_still_resolves_to_serve(self, runner, tmp_path):
        # Arrange
        source = tmp_path / "figure.yaml"
        source.write_text("")
        args = ["gui", "serve", str(source), "--dry-run", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload["would_serve"]

    def test_explicit_status_verb_still_resolves_to_status(
        self, runner, isolated_state
    ):
        # Arrange
        args = ["gui", "status", "--json"]
        # Act
        result = runner.invoke(main, args)
        payload = json.loads(result.output)
        # Assert
        assert payload == {"running": False}

    def test_bare_help_shows_group_help_not_open_help(self, runner):
        # Arrange: --help must never silently default to `open --help`.
        args = ["gui", "--help"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert "serve" in result.output and "status" in result.output


class TestGuiServeBindOrFail:
    """`gui serve` never silently drifts to a different port than requested."""

    def test_refuses_when_port_already_bound(self, runner, isolated_state):
        # Arrange: hold a real socket on an ephemeral port first.
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        held_port = sock.getsockname()[1]
        args = ["gui", "serve", "--port", str(held_port)]
        # Act
        try:
            result = runner.invoke(main, args)
        finally:
            sock.close()
        # Assert
        assert result.exit_code == 1

    def test_refuses_when_port_already_bound_message(self, runner, isolated_state):
        # Arrange
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        held_port = sock.getsockname()[1]
        args = ["gui", "serve", "--port", str(held_port)]
        # Act
        try:
            result = runner.invoke(main, args)
        finally:
            sock.close()
        # Assert
        assert "already in use" in result.output

    def test_refuses_when_port_taken_leaves_no_state_file(self, runner, isolated_state):
        # Arrange
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        held_port = sock.getsockname()[1]
        args = ["gui", "serve", "--port", str(held_port)]
        # Act
        try:
            runner.invoke(main, args)
        finally:
            sock.close()
        # Assert: no silent instance is ever recorded as running.
        assert not isolated_state.exists()

    def test_refuses_when_already_recorded_running(self, runner, isolated_state):
        # Arrange: a live pid (our own test process) recorded as running.
        _gui_runtime.write_state(os.getpid(), 31296, "127.0.0.1", None, isolated_state)
        args = ["gui", "serve"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert result.exit_code == 1

    def test_refuses_when_already_recorded_running_message(
        self, runner, isolated_state
    ):
        # Arrange
        _gui_runtime.write_state(os.getpid(), 31296, "127.0.0.1", None, isolated_state)
        args = ["gui", "serve"]
        # Act
        result = runner.invoke(main, args)
        # Assert
        assert "already running" in result.output


class TestGuiConsumerBranding:
    """Consumer console-scripts (e.g. scitex-plt) get a rebranded GUI title/favicon."""

    @pytest.fixture(autouse=True)
    def _clean_branding_env(self):
        for key in ("FIGRECIPE_APP_LABEL", "FIGRECIPE_FAVICON_COLOR"):
            os.environ.pop(key, None)
        yield
        for key in ("FIGRECIPE_APP_LABEL", "FIGRECIPE_FAVICON_COLOR"):
            os.environ.pop(key, None)

    def test_scitex_plt_prog_name_sets_app_label(self, runner):
        # Arrange
        args = ["--version"]
        # Act
        runner.invoke(main, args, prog_name="scitex-plt")
        # Assert
        assert os.environ.get("FIGRECIPE_APP_LABEL") == "SciTeX Plot"

    def test_scitex_plt_prog_name_sets_favicon_color(self, runner):
        # Arrange
        args = ["--version"]
        # Act
        runner.invoke(main, args, prog_name="scitex-plt")
        # Assert
        assert os.environ.get("FIGRECIPE_FAVICON_COLOR") == "#001f3f"

    def test_figrecipe_prog_name_sets_no_branding(self, runner):
        # Arrange
        args = ["--version"]
        # Act
        runner.invoke(main, args, prog_name="figrecipe")
        # Assert
        assert os.environ.get("FIGRECIPE_APP_LABEL") is None

    def test_existing_env_override_wins_over_inference(self, runner):
        # Arrange
        os.environ["FIGRECIPE_APP_LABEL"] = "Custom Title"
        args = ["--version"]
        # Act
        runner.invoke(main, args, prog_name="scitex-plt")
        # Assert
        assert os.environ.get("FIGRECIPE_APP_LABEL") == "Custom Title"
