#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shell tab-completion for the figrecipe CLI.

Per audit-cli §1a every scitex-* CLI must expose
``install-shell-completion`` and ``print-shell-completion`` so users get
``<TAB>`` completion. ``attach_shell_completion(main, prog_name="figrecipe")``
registers four leaves on ``main``:

  * ``print-shell-completion   --shell {bash,zsh,fish}``  (canonical)
  * ``install-shell-completion --shell {bash,zsh,fish}``  (canonical)
  * ``install-tab-completion``   (hidden deprecated alias)
  * ``completion``               (hidden deprecated alias)

Drop-in contract v1: ``install-shell-completion`` writes the generated
script to the drop-in file ``$SCITEX_DIR/<prog>/runtime/completion/<prog>``
(default ``~/.scitex/figrecipe/runtime/completion/figrecipe``) with an
atomic rename, skips the rewrite when the content is unchanged
(idempotent), and prints the drop-in path. It never touches shell
startup files — sourcing the printed path (or a loader that sources the
drop-in directory) activates completion.

Why generate the completion script IN-PROCESS (``click.shell_completion``)
instead of shelling out to ``subprocess.run([prog_name])`` the way the
shared scitex-dev helper historically did: figrecipe's CI (and any
``PYTHONPATH``-based / ``pip install --target`` deployment, e.g. the
Spartan SIF runner) has figrecipe importable but NO ``figrecipe``
console-script on ``$PATH``. The subprocess form then dies with
``FileNotFoundError`` (zero-output), so ``print-shell-completion`` exited
non-zero in CI. Click already knows how to emit the script for the
in-memory ``Group`` object, so we ask it directly — no binary lookup, no
subprocess, works identically on a dev box and inside the SIF.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import click

SHELLS = ["bash", "zsh", "fish"]


def _complete_var(prog_name: str) -> str:
    """Click's autocompletion env var: ``_<UPPER_PROG>_COMPLETE``."""
    return "_" + prog_name.upper().replace("-", "_") + "_COMPLETE"


def _generate_script(main_group: click.Group, shell: str, prog_name: str) -> str:
    """Return the click-generated completion script for ``shell`` in-process.

    Uses ``click.shell_completion.get_completion_class`` so no ``prog_name``
    console-script needs to exist on ``$PATH`` (the CI / SIF failure mode).
    """
    from click.shell_completion import get_completion_class

    comp_cls = get_completion_class(shell)
    if comp_cls is None:  # pragma: no cover - SHELLS is constrained by Choice
        raise click.ClickException(f"Unsupported shell: {shell}")
    completer = comp_cls(main_group, {}, prog_name, _complete_var(prog_name))
    script = completer.source().strip()
    if not script:  # pragma: no cover - defensive; click always emits a body
        raise click.ClickException(
            f"Failed to generate {shell} completion script for {prog_name}."
        )
    return script


def _scitex_dir() -> Path:
    """Resolve ``$SCITEX_DIR`` (default ``~/.scitex``)."""
    return Path(os.environ.get("SCITEX_DIR", os.path.expanduser("~/.scitex")))


def _cache_path(prog_name: str) -> Path:
    """Drop-in file: ``$SCITEX_DIR/<prog>/runtime/completion/<prog>``."""
    return _scitex_dir() / prog_name / "runtime" / "completion" / prog_name


def _write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically (tmp file + rename)."""
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
        os.chmod(path, 0o644)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def attach_shell_completion(main_group: click.Group, *, prog_name: str) -> None:
    """Register the four shell-completion leaves on ``main_group``."""

    @main_group.command("print-shell-completion")
    @click.option(
        "--shell",
        type=click.Choice(SHELLS),
        default="bash",
        help="Target shell. Default: bash.",
    )
    def print_shell_completion(shell: str) -> None:
        """Print the click-generated completion script to stdout.

        \b
        Example:
          $ figrecipe print-shell-completion --shell bash
          $ figrecipe print-shell-completion --shell zsh
          $ eval "$(figrecipe print-shell-completion --shell bash)"
        """
        click.echo(_generate_script(main_group, shell, prog_name))

    @main_group.command("install-shell-completion")
    @click.option(
        "--shell",
        type=click.Choice(SHELLS),
        default="bash",
        help="Target shell. Default: bash.",
    )
    @click.option(
        "--dry-run",
        is_flag=True,
        help="Print the drop-in path without writing.",
    )
    @click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
    def install_shell_completion(shell: str, dry_run: bool, yes: bool) -> None:
        """Install the ``<TAB>``-completion drop-in file.

        \b
        Example:
          $ figrecipe install-shell-completion
          $ figrecipe install-shell-completion --shell zsh
          $ figrecipe install-shell-completion --dry-run    # preview only

        \b
        Activate in the current shell after install:
          source ~/.scitex/figrecipe/runtime/completion/figrecipe
        """
        del yes  # accepted for §2 compliance; use --dry-run for preview
        drop_in = _cache_path(prog_name)

        if dry_run:
            click.echo(f"Would write completion drop-in to {drop_in}")
            return

        script = _generate_script(main_group, shell, prog_name) + "\n"
        drop_in.parent.mkdir(parents=True, exist_ok=True)

        try:
            existing = drop_in.read_text() if drop_in.is_file() else None
        except OSError:
            existing = None
        if existing == script:
            click.echo(f"Tab completion already installed at {drop_in}")
            return

        _write_atomic(drop_in, script)
        click.echo(f"Tab completion installed at {drop_in}")
        click.echo(f"Run: source {drop_in}")

    @main_group.command(
        "install-tab-completion",
        hidden=True,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )
    @click.pass_context
    def install_tab_completion_deprecated(ctx: click.Context) -> None:
        """(deprecated) Renamed to ``install-shell-completion``."""
        click.echo(
            f"error: `{prog_name} install-tab-completion` was renamed to "
            f"`{prog_name} install-shell-completion`.\n"
            f"Re-run with: {prog_name} install-shell-completion",
            err=True,
        )
        ctx.exit(2)

    @main_group.command(
        "completion",
        hidden=True,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )
    @click.pass_context
    def completion_deprecated(ctx: click.Context) -> None:
        """(deprecated) Renamed to ``install-shell-completion``."""
        click.echo(
            f"error: `{prog_name} completion` was renamed to "
            f"`{prog_name} install-shell-completion`.\n"
            f"Re-run with: {prog_name} install-shell-completion",
            err=True,
        )
        ctx.exit(2)
