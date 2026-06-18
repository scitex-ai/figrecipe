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


def _rc_path(shell: str, prog_name: str) -> str:
    if shell == "fish":
        return os.path.expanduser(f"~/.config/fish/completions/{prog_name}.fish")
    return os.path.expanduser({"bash": "~/.bashrc", "zsh": "~/.zshrc"}[shell])


def _scitex_dir() -> Path:
    """Resolve ``$SCITEX_DIR`` (default ``~/.scitex``)."""
    return Path(os.environ.get("SCITEX_DIR", os.path.expanduser("~/.scitex")))


def _cache_path(prog_name: str) -> Path:
    """Primary cache: ``$SCITEX_DIR/<prog>/runtime/completion/<prog>``."""
    return _scitex_dir() / prog_name / "runtime" / "completion" / prog_name


def _marker(prog_name: str) -> str:
    return f"# {prog_name} tab completion"


def _source_line(cache_path: Path, prog_name: str) -> str:
    return f"[ -f {cache_path} ] && source {cache_path}  {_marker(prog_name)}"


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
        help="Print the target rc file + source line without writing.",
    )
    @click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
    def install_shell_completion(shell: str, dry_run: bool, yes: bool) -> None:
        """Wire up ``<TAB>`` completion in the user's shell rc.

        \b
        Example:
          $ figrecipe install-shell-completion              # -> ~/.bashrc
          $ figrecipe install-shell-completion --shell zsh  # -> ~/.zshrc
          $ figrecipe install-shell-completion --dry-run    # preview only

        \b
        Activate in the current shell after install:
          source ~/.bashrc
        """
        del yes  # accepted for §2 compliance; use --dry-run for preview
        rc_path = _rc_path(shell, prog_name)

        if shell == "fish":
            if dry_run:
                click.echo(f"Would write fish completion to {rc_path}")
                return
            os.makedirs(os.path.dirname(rc_path), exist_ok=True)
            with open(rc_path, "w") as f:
                f.write(_generate_script(main_group, shell, prog_name) + "\n")
            click.echo(f"Tab completion installed at {rc_path}")
            click.echo(f"Run: source {rc_path}")
            return

        # Cache-file pattern: generate ONCE to a cache file, then append a
        # cheap `[ -f cache ] && source cache` line to rc (sourcing the
        # cached script is ~microseconds vs ~0.4s for the eval form that
        # re-invokes the binary on every shell start).
        cache = _cache_path(prog_name)
        line = _source_line(cache, prog_name)
        marker = _marker(prog_name)

        if dry_run:
            click.echo(f"Would write completion cache to {cache}")
            click.echo(f"Would append to {rc_path}:")
            click.echo(f"  {line}")
            return

        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(_generate_script(main_group, shell, prog_name) + "\n")

        existing = ""
        if os.path.isfile(rc_path):
            with open(rc_path) as f:
                existing = f.read()
        if marker in existing and line.strip() in existing:
            click.echo(f"Tab completion already installed in {rc_path}")
            return
        if marker in existing:
            # Drop any stale marker line(s) so we replace cleanly.
            kept = [ln for ln in existing.splitlines() if marker not in ln]
            existing = "\n".join(kept).rstrip() + "\n"
            with open(rc_path, "w") as f:
                f.write(existing)
            click.echo(f"Removed previous {prog_name} completion line from {rc_path}")

        with open(rc_path, "a") as f:
            f.write(f"\n{line}\n")
        click.echo(f"Tab completion installed for {prog_name}")
        click.echo(f"  cache:  {cache}")
        click.echo(f"  rc:     {rc_path}  (source line appended)")
        click.echo(f"Run: source {rc_path}")

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
