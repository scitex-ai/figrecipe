#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main CLI entry point for figrecipe."""

import click
from rich.console import Console

from .. import __version__
from ._apis import list_python_apis
from ._completion import attach_shell_completion
from ._compose import compose
from ._convert import convert
from ._crop import crop
from ._diagram import diagram as _diagram_cmd
from ._diff import diff
from ._extract import extract
from ._fonts import fonts
from ._gui import gui, start_gui
from ._hitmap import hitmap
from ._info import info
from ._mcp import mcp
from ._plot import plot
from ._reproduce import reproduce
from ._style import style
from ._validate import validate
from ._version import show_version
from ._version import version as version_cmd

console = Console()

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

# Command categories for organized help display
COMMAND_CATEGORIES = [
    ("Figure Creation", ["plot", "reproduce", "compose", "gui"]),
    ("Image Processing", ["convert", "crop", "diff", "show-hitmap"]),
    ("Data & Validation", ["extract", "validate", "info"]),
    ("Diagram", ["diagram"]),
    ("Style & Appearance", ["style", "list-fonts"]),
    ("Integration", ["mcp", "list-python-apis"]),
    (
        "Utility",
        [
            "show-version",
            "install-shell-completion",
            "print-shell-completion",
        ],
    ),
]


class CategorizedGroup(click.Group):
    """Custom Click group that displays commands organized by category."""

    def format_commands(self, ctx, formatter):
        """Write categorized commands to the formatter."""
        # Build command lookup
        commands = {}
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is not None and not cmd.hidden:
                commands[subcommand] = cmd

        if not commands:
            return

        # Track which commands we've displayed
        displayed = set()

        # Display commands by category
        for category_name, category_commands in COMMAND_CATEGORIES:
            # Filter to commands that exist and haven't been displayed
            category_items = []
            for name in category_commands:
                if name in commands and name not in displayed:
                    cmd = commands[name]
                    help_text = cmd.get_short_help_str(limit=formatter.width)
                    category_items.append((name, help_text))
                    displayed.add(name)

            if category_items:
                with formatter.section(category_name):
                    formatter.write_dl(category_items)

        # Display any uncategorized commands
        uncategorized = [
            (name, commands[name].get_short_help_str(limit=formatter.width))
            for name in sorted(commands.keys())
            if name not in displayed
        ]
        if uncategorized:
            with formatter.section("Other"):
                formatter.write_dl(uncategorized)


def _print_command_help(cmd, prefix: str, parent_ctx) -> None:
    """Recursively print help for a command and its subcommands."""
    console.print(f"\n[bold cyan]━━━ {prefix} ━━━[/bold cyan]")
    sub_ctx = click.Context(cmd, info_name=prefix.split()[-1], parent=parent_ctx)
    console.print(cmd.get_help(sub_ctx))

    # If this is a Group, recurse into subcommands
    if isinstance(cmd, click.Group):
        for sub_name, sub_cmd in sorted(cmd.commands.items()):
            _print_command_help(sub_cmd, f"{prefix} {sub_name}", sub_ctx)


#: Console-script name -> (GUI page title, favicon hex color). Consumer
#: packages (scitex-plt today; scitex-scholar/etc. potentially later) alias
#: this same CLI/Django app under their own entry point
#: (`[project.scripts]` -> `figrecipe._cli:main`, see figrecipe's own
#: pyproject.toml and scitex-plt's) -- this is the one place that tells
#: them apart, so branding is set here rather than forked per-consumer.
_CONSUMER_BRANDING = {
    "scitex-plt": ("SciTeX Plot", "#001f3f"),  # navy
}


def _apply_consumer_branding(prog_name: str) -> None:
    """Set FIGRECIPE_APP_LABEL/FIGRECIPE_FAVICON_COLOR for aliased consumers.

    Read by `_django.views.editor_page` when it renders the GUI shell.
    `setdefault` so an explicit env override (e.g. tests, a future
    `--title` flag) always wins over this program-name inference.
    """
    import os

    branding = _CONSUMER_BRANDING.get(prog_name)
    if branding is None:
        return
    label, favicon_color = branding
    os.environ.setdefault("FIGRECIPE_APP_LABEL", label)
    os.environ.setdefault("FIGRECIPE_FAVICON_COLOR", favicon_color)


@click.group(
    cls=CategorizedGroup,
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
)
@click.option("--version", "-V", is_flag=True, help="Show version and exit.")
@click.option("--help-recursive", is_flag=True, help="Show help for all commands.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit structured JSON output (propagates to subcommands that honour it).",
)
@click.pass_context
def main(
    ctx: click.Context, version: bool, help_recursive: bool, as_json: bool
) -> None:
    """FigRecipe - Reproducible, style-editable scientific figures via YAML recipes.

    Use 'figrecipe gui open' to launch the GUI editor.

    Config is loaded with the SciTeX precedence chain:
      config.yaml -> $FIGRECIPE_CONFIG -> ~/.scitex/figrecipe/config.yaml -> defaults
    """
    # Stash --json so subcommands can read it via ctx.obj
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    _apply_consumer_branding(ctx.info_name)

    if version:
        click.echo(f"figrecipe {__version__}")
        ctx.exit(0)

    if help_recursive:
        _show_recursive_help(ctx)
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _show_recursive_help(ctx: click.Context) -> None:
    """Display recursive help for all commands."""
    console.print("[bold cyan]━━━ figrecipe ━━━[/bold cyan]")
    console.print(ctx.get_help())

    for name, cmd in sorted(main.commands.items()):
        _print_command_help(cmd, f"figrecipe {name}", ctx)


# Register commands

main.add_command(compose)
main.add_command(convert)
main.add_command(crop)
main.add_command(_diagram_cmd, name="diagram")
main.add_command(diff)
main.add_command(extract)
main.add_command(fonts)
main.add_command(gui)
main.add_command(start_gui)
main.add_command(hitmap)
main.add_command(info)
main.add_command(list_python_apis)
main.add_command(mcp)
main.add_command(plot)
main.add_command(reproduce)
main.add_command(style)
main.add_command(validate)
main.add_command(version_cmd)
main.add_command(show_version)

try:
    from scitex_dev.cli import docs_click_group

    main.add_command(docs_click_group(package="figrecipe"))
except ImportError:
    pass

# audit-cli §13 — self-maintenance commands live under `dev`, not at the top
# level, so `figrecipe --help` stays a list of things a USER does with figures
# (doctrine 20_dev-commands.md). The group is defined here rather than in its
# own module because it holds nothing of figrecipe's own: every member is
# supplied by scitex-dev.
@click.group(context_settings=CONTEXT_SETTINGS)
def dev() -> None:
    """Self-maintenance commands for figrecipe itself."""


main.add_command(dev)

# NOT registered here: scitex-dev's own `skills_click_group`. It used to be
# added to `main`, and `_cli/__init__.py` then overwrote the same name with
# figrecipe's `_skills.skills_group` — so the scitex-dev one had never been
# reachable. Removing dead code rather than moving it under `dev`, where it
# would have collided with the real one for the first time. figrecipe's own
# group is attached to `dev` in `_cli/__init__.py`, beside the alias.

# §12 IS DELIBERATELY LEFT FIRING, and this is the reasoning rather than an
# oversight. The rule wants `start-gui` re-registered through
# `scitex_dev.ecosystem.deprecated_alias()` so the static auditor can see it.
# Doing that was tried and REVERTED: the generic helper forwards argv to the
# target and nothing else, while figrecipe's hand-rolled `start_gui` in
# _gui.py ALSO accepts `--force` (kills whatever holds the port, then sleeps
# before handing off) and tolerates `-y/--yes` for back-compat. `gui open` has
# neither option, so the swap turns `start-gui --force` into a usage error and
# silently drops the port-kill — a functional regression taken to silence a
# WARN.
#
# §12 is WARN-tier and does not gate (measured: audit-all exits 0 with WARN
# findings present), so the honest trade is to keep the working alias and
# carry the warning. Reported upstream: the prescribed remedy assumes an alias
# is a pure forward, and loses behaviour for any alias that accepts options
# its target does not.
#
# `skills` IS moved, in _cli/__init__.py — that one is a pure forward, so the
# helper costs nothing there.

# audit-cli §1a — wire install-shell-completion + print-shell-completion
# so `figrecipe <TAB>` works without the user copy-pasting boilerplate.
# figrecipe's own helper generates the script IN-PROCESS (click.shell_
# completion) so it works even when no `figrecipe` console-script is on
# $PATH — e.g. the PYTHONPATH/--target SIF install used by self-hosted CI,
# where shelling out to the bare binary previously died with FileNotFound.
attach_shell_completion(main, prog_name="figrecipe")


if __name__ == "__main__":
    main()
