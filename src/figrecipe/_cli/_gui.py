#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: src/figrecipe/_cli/_gui.py

"""`gui` command group (browser-based editor): open / serve / status / stop.

Follows the scitex-dev fleet CLI canon (19_gui-commands.md §12): one `gui`
group with exactly four verbs. `serve` runs in the FOREGROUND; `open`
auto-serves a detached server when none is running, then opens the browser.
Runtime state lives in `_gui_runtime` so status/stop work from a fresh
shell. Ported from scitex-writer's `_cli/commands/gui.py`
(card: figrecipe-gui-cli-noun-verb-normalize-20260712).

figrecipe's own argument semantics are preserved from the previous flat
`start-gui` command: the positional arg is `source` (a .yaml recipe path,
bundle, or directory — not scitex-writer's `project`), and a directory
without `recipe.yaml` resolves to a browse-root `working_dir` instead of a
specific recipe.

`start-gui` remains as a hidden warn-forward alias for one deprecation
cycle, keeping its original `--force`/`--yes` options so existing scripts
don't break mid-cycle; the new `gui open`/`gui serve` do NOT expose
`--force` — `gui stop -y` is the direct, tracked replacement for killing a
server this CLI started. `_kill_port` is kept as a private helper used only
by the deprecated alias's `--force` path (untracked stray processes holding
the port are out of scope for the new lifecycle; users can reach for
`fuser`/`lsof` directly, matching this project's simplicity-first stance).
"""

from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional, Tuple

import click

from . import _gui_runtime


def _kill_port(port: int) -> bool:
    """Kill process occupying the given port. Returns True if killed.

    Legacy helper retained ONLY for the deprecated `start-gui --force` alias
    (see module docstring) — the new `gui` group's own lifecycle uses
    `gui stop` instead.
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


def _resolve_source(
    source: Optional[str],
) -> Tuple[Optional[Path], Optional[Path]]:
    """Resolve a `source` CLI arg into (source_path, working_dir).

    A directory without `recipe.yaml` is treated as a working_dir browse
    root rather than a specific recipe — ported verbatim from figrecipe's
    original flat `start-gui` command.
    """
    if source is None:
        return None, None
    source_path = Path(source)
    working_dir = None
    if source_path.is_dir():
        recipe_yaml = source_path / "recipe.yaml"
        if not recipe_yaml.exists():
            working_dir = source_path
            source_path = None
    return source_path, working_dir


def _emit_json(payload: dict) -> None:
    import json as _json

    click.echo(_json.dumps(payload, indent=2))


@click.group("gui")
def gui():
    """Browser-based editor: open, serve, status, stop."""


# =========================================================================
# gui serve — run the server in the foreground
# =========================================================================


@gui.command("serve")
@click.argument("source", type=click.Path(exists=True), required=False)
@click.option("--port", type=int, default=5050, help="Server port (default: 5050).")
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
@click.option("--dry-run", is_flag=True, default=False, help="Print, don't launch.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON.")
def gui_serve(source, port, host, dry_run, as_json):
    """Run the editor server in the foreground (Ctrl-C to stop).

    SOURCE is the optional path to a .yaml recipe file or a directory.
    If not provided, creates a new blank figure.

    \b
    Example:
        $ figrecipe gui serve
        $ figrecipe gui serve figure.yaml --port 5051
    """
    source_path, working_dir = _resolve_source(source)
    if working_dir is not None:
        click.echo(f"Browsing directory: {working_dir}")
    if dry_run:
        payload = {
            "would_serve": True,
            "host": host,
            "port": port,
            "source": str(source_path) if source_path else None,
            "working_dir": str(working_dir) if working_dir else None,
        }
        if as_json:
            _emit_json(payload)
        else:
            click.echo(f"Would serve editor at http://{host}:{port}.")
        return 0

    import os

    from .. import gui as fr_gui

    _gui_runtime.write_state(
        os.getpid(),
        port,
        host,
        str(source_path)
        if source_path
        else (str(working_dir) if working_dir else None),
    )
    try:
        fr_gui(
            source_path,
            port=port,
            host=host,
            open_browser=False,
            desktop=False,
            working_dir=working_dir,
        )
    except Exception as e:
        raise click.ClickException(f"Editor failed: {e}") from e
    finally:
        _gui_runtime.clear_state()
    return 0


# =========================================================================
# gui open — ensure a server is running, then open the browser
# =========================================================================


def _autoserve(source: Optional[str], port: int, host: str) -> dict:
    """Spawn a detached `gui serve` and wait for its state file."""
    log_path = _gui_runtime.state_path().with_name("gui.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "figrecipe", "gui", "serve"]
    if source:
        cmd.append(str(source))
    cmd += ["--port", str(port), "--host", host]
    with open(log_path, "ab") as log:
        subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        current = _gui_runtime.status()
        if current.get("running"):
            return current
        time.sleep(0.3)
    return {"running": False, "log": str(log_path)}


@gui.command("open")
@click.argument("source", type=click.Path(exists=True), required=False)
@click.option("--port", type=int, default=5050, help="Server port (default: 5050).")
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
@click.option("--no-browser", is_flag=True, default=False, help="Don't open browser.")
@click.option(
    "--desktop",
    is_flag=True,
    default=False,
    help="Launch as desktop window (requires pywebview).",
)
@click.option("--dry-run", is_flag=True, default=False, help="Print, don't launch.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON.")
def gui_open(source, port, host, no_browser, desktop, dry_run, as_json):
    """Open the editor, auto-starting a background server when needed.

    SOURCE is the optional path to a .yaml recipe file or a directory.
    If not provided, creates a new blank figure.

    \b
    Example:
        $ figrecipe gui open
        $ figrecipe gui open figure.yaml --port 5051
        $ figrecipe gui open --desktop
    """
    source_path, working_dir = _resolve_source(source)
    if working_dir is not None:
        click.echo(f"Browsing directory: {working_dir}")
    if dry_run:
        payload = {
            "would_open": True,
            "host": host,
            "port": port,
            "desktop": desktop,
            "source": str(source_path) if source_path else None,
            "working_dir": str(working_dir) if working_dir else None,
        }
        if as_json:
            _emit_json(payload)
        else:
            click.echo(f"Would open editor at http://{host}:{port}.")
        return 0

    if desktop:
        # Desktop mode is synchronous/blocking by nature (its own window),
        # not a backgroundable server — run it directly, no state file.
        from .. import gui as fr_gui

        try:
            fr_gui(
                source_path,
                port=port,
                host=host,
                open_browser=False,
                desktop=True,
                working_dir=working_dir,
            )
        except Exception as e:
            raise click.ClickException(f"Editor failed: {e}") from e
        return 0

    current = _gui_runtime.status()
    if not current.get("running"):
        current = _autoserve(source, port, host)
        if not current.get("running"):
            click.echo(
                f"Error: server did not come up within 30s; see {current.get('log')}",
                err=True,
            )
            # `return 1` would be silently discarded by Click's standalone
            # mode (it only exits non-zero via ctx.exit(code)/SystemExit),
            # so raise explicitly to make the failure observable to scripts.
            raise SystemExit(1)
    url = current["url"]
    if not no_browser:
        webbrowser.open(url)
    if as_json:
        _emit_json(current)
    else:
        click.echo(f"Editor running at {url}.")
    return 0


# =========================================================================
# gui status / gui stop
# =========================================================================


@gui.command("status")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON.")
def gui_status(as_json):
    """Report whether the editor server is running.

    \b
    Example:
        $ figrecipe gui status
        $ figrecipe gui status --json
    """
    current = _gui_runtime.status()
    if as_json:
        _emit_json(current)
    elif current.get("running"):
        click.echo(f"Running at {current['url']} (pid {current['pid']}).")
    else:
        click.echo("Not running.")
    return 0


@gui.command("stop")
@click.option("--dry-run", is_flag=True, default=False, help="Print, don't stop.")
@click.option(
    "--yes", "-y", is_flag=True, default=False, help="Stop without confirmation."
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON.")
def gui_stop(dry_run, yes, as_json):
    """Stop the editor server started by `gui serve` / `gui open`.

    \b
    Example:
        $ figrecipe gui stop -y
        $ figrecipe gui stop --dry-run
    """
    current = _gui_runtime.status()
    if not current.get("running"):
        if as_json:
            _emit_json({"stopped": False, "running": False})
        else:
            click.echo("Not running.")
        return 0
    if dry_run:
        would = {"would_stop": True, "pid": current["pid"], "url": current["url"]}
        if as_json:
            _emit_json(would)
        else:
            click.echo(f"Would stop {current['url']} (pid {current['pid']}).")
        return 0
    if not yes:
        click.echo(
            f"Refusing to stop {current['url']} (pid {current['pid']}) "
            "without --yes/-y.",
            err=True,
        )
        # `return 2` would be silently discarded by Click's standalone mode
        # (see `gui_open`'s comment above) — raise explicitly so scripts
        # checking `$?` actually observe the refusal.
        raise SystemExit(2)
    result = _gui_runtime.stop()
    if as_json:
        _emit_json(result)
    elif result.get("stopped"):
        click.echo(f"Stopped (pid {result['pid']}).")
    else:
        click.echo("Not running.")
    return 0


# =========================================================================
# start-gui — hidden warn-forward alias (one deprecation cycle)
# =========================================================================


@click.command("start-gui", hidden=True)
@click.argument("source", type=click.Path(exists=True), required=False)
@click.option("--port", type=int, default=5050)
@click.option("--host", default="127.0.0.1")
@click.option("--no-browser", is_flag=True, default=False)
@click.option("--desktop", is_flag=True, default=False)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="[deprecated] kill existing process on port; use `gui stop -y` instead.",
)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("-y", "--yes", is_flag=True, default=False)
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def start_gui(
    ctx, source, port, host, no_browser, desktop, force, dry_run, yes, as_json
):
    """Deprecated alias for `gui open`."""
    del yes  # accepted for back-compat only; `gui open` has no confirmation gate
    click.echo(
        "Warning: `start-gui` is deprecated; use `figrecipe gui open` instead.",
        err=True,
    )
    if force and not dry_run:
        if _kill_port(port):
            click.echo(f"Killed existing process on port {port}", err=True)
            time.sleep(0.5)
    return ctx.invoke(
        gui_open,
        source=source,
        port=port,
        host=host,
        no_browser=no_browser,
        desktop=desktop,
        dry_run=dry_run,
        as_json=as_json,
    )


# EOF
