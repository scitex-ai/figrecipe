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
from ._gui import gui
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
    ("Figure Creation", ["plot", "reproduce", "compose", "start-gui"]),
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

    Use 'figrecipe start-gui' to launch the GUI editor.

    Config is loaded with the SciTeX precedence chain:
      config.yaml -> $FIGRECIPE_CONFIG -> ~/.scitex/figrecipe/config.yaml -> defaults
    """
    # Stash --json so subcommands can read it via ctx.obj
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json

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

try:
    from scitex_dev.cli import skills_click_group

    main.add_command(skills_click_group(package="figrecipe"))
except ImportError:
    pass

# audit-cli §1a — wire install-shell-completion + print-shell-completion
# so `figrecipe <TAB>` works without the user copy-pasting boilerplate.
# figrecipe's own helper generates the script IN-PROCESS (click.shell_
# completion) so it works even when no `figrecipe` console-script is on
# $PATH — e.g. the PYTHONPATH/--target SIF install used by self-hosted CI,
# where shelling out to the bare binary previously died with FileNotFound.
attach_shell_completion(main, prog_name="figrecipe")


if __name__ == "__main__":
    main()
