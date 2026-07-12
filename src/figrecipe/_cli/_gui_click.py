#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: src/figrecipe/_cli/_gui_click.py

"""Generic Click/networking helpers used by `_gui.py`.

Split out of `_gui.py` purely to keep that module under the project's
512-line file-size convention -- nothing here is figrecipe-specific
(the `gui` command wiring, `_resolve_source`, and the Django launch call
all stay in `_gui.py`).
"""

from __future__ import annotations

import socket
import subprocess
from typing import Optional

import click


def _port_is_free(host: str, port: int) -> bool:
    """True when ``host:port`` can be bound right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _port_holder(port: int) -> Optional[str]:
    """Best-effort description of the process listening on ``port``.

    Returns None (never raises) when `ss` isn't available or nothing is
    found -- this is a diagnostic nicety, not load-bearing.
    """
    try:
        proc = subprocess.run(
            ["ss", "-ltnp"], capture_output=True, text=True, timeout=3
        )
    except (OSError, subprocess.SubprocessError):
        return None
    for line in proc.stdout.splitlines():
        if f":{port} " in line:
            _, _, users = line.partition("users:")
            return (users.strip() or line.strip()) or None
    return None


def _kill_port(port: int) -> bool:
    """Kill process occupying the given port. Returns True if killed.

    Legacy helper retained ONLY for `_gui.py`'s deprecated `start-gui
    --force` alias -- the `gui` group's own lifecycle uses `gui stop`
    instead.
    """
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        pids = result.stdout.strip().split()
        if not pids:
            return False
        for pid in pids:
            subprocess.run(["kill", "-9", pid], capture_output=True)
        return True
    except FileNotFoundError:
        # lsof not available, try fuser
        try:
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
            )
            return True
        except FileNotFoundError:
            return False


class _DefaultGroup(click.Group):
    """A `click.Group` that falls back to a default subcommand.

    Looks at the first NON-option token (skipping any leading `-`/`--`
    flags) rather than strictly `args[0]`: when it isn't a registered
    subcommand name, the WHOLE arg list is treated as belonging to
    `default_cmd_name` instead of raising an unknown-command error. This is
    what lets `figrecipe gui figure.yaml` (and a bare `figrecipe gui
    --dry-run`, no positional at all) keep working -- implicitly `gui open
    ...` -- alongside the explicit `gui open`/`serve`/`status`/`stop`.

    Known limitation (accepted, matches other default-group CLIs e.g.
    docker/git plumbing): options meant for the default command must come
    AFTER the positional, not before it bare (`gui figure.yaml --port 8080`
    works; `gui --port 8080 figure.yaml` does not, since the first
    non-option token, "figure.yaml", is never reached when an earlier `-`
    token was already handed to the group's own (empty) option parser).
    """

    def __init__(self, *args, default_cmd_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_cmd_name = default_cmd_name

    def parse_args(self, ctx, args):
        # A bare `-h`/`--help` (with no other positional) must show the
        # GROUP's own help (listing open/serve/status/stop), not silently
        # default to `open --help` -- so leave it untouched and let click's
        # normal group parsing handle it.
        if any(a in ("-h", "--help") for a in args):
            return super().parse_args(ctx, args)
        first_non_option = next((a for a in args if not a.startswith("-")), None)
        if first_non_option is None or first_non_option not in self.commands:
            args = [self.default_cmd_name, *args]
        return super().parse_args(ctx, args)


# EOF
