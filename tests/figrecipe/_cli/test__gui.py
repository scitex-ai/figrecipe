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
