#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style command - Style management subcommands."""

import click
from rich.console import Console

from .._utils._console import render_rich

console = Console()

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _print_command_help(cmd, prefix: str, parent_ctx) -> None:
    """Print help for a command."""
    render_rich(f"\n[bold cyan]━━━ {prefix} ━━━[/bold cyan]", __name__)
    sub_ctx = click.Context(cmd, info_name=prefix.split()[-1], parent=parent_ctx)
    render_rich(cmd.get_help(sub_ctx), __name__)


def _show_recursive_help(ctx: click.Context) -> None:
    """Display recursive help for all style subcommands."""
    render_rich("[bold cyan]━━━ figrecipe style ━━━[/bold cyan]", __name__)
    render_rich(ctx.get_help(), __name__)

    for name, cmd in sorted(style.commands.items()):
        if name == "help-recursive":
            continue
        _print_command_help(cmd, f"figrecipe style {name}", ctx)


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option("--help-recursive", is_flag=True, help="Show help for all subcommands.")
@click.pass_context
def style(ctx: click.Context, help_recursive: bool) -> None:
    """Manage figure styles and presets."""
    if help_recursive:
        _show_recursive_help(ctx)
        ctx.exit(0)

    if ctx.invoked_subcommand is None and not help_recursive:
        click.echo(ctx.get_help())


@style.command("list")
@click.option(
    "--json", "as_json", is_flag=True, help="Emit JSON instead of plain text."
)
def list_styles(as_json: bool) -> None:
    """List available style presets.

    \b
    Example:
      $ figrecipe style list
      $ figrecipe style list --json
    """
    from .. import list_presets

    presets = list_presets()

    if as_json:
        import json as _json

        click.echo(_json.dumps({"presets": list(presets)}, indent=2))
        return

    click.echo("Available style presets:")
    for preset in presets:
        click.echo(f"  - {preset}")


@style.command("show")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of YAML.")
def show_style(name: str, as_json: bool) -> None:
    """Show details of a style preset.

    NAME is the preset name (e.g., SCITEX, MATPLOTLIB).

    \b
    Example:
      $ figrecipe style show SCITEX
      $ figrecipe style show MATPLOTLIB --json
    """
    from ruamel.yaml import YAML

    from ..styles._style_loader import load_preset

    try:
        style_dict = load_preset(name)
    except Exception as e:
        raise click.ClickException(f"Failed to load preset '{name}': {e}") from e

    if as_json:
        import json as _json

        click.echo(
            _json.dumps({"name": name, "style": style_dict}, indent=2, default=str)
        )
        return

    yaml = YAML()
    yaml.default_flow_style = False

    click.echo(f"Style preset: {name}\n")

    import io

    stream = io.StringIO()
    yaml.dump(style_dict, stream)
    click.echo(stream.getvalue())


@style.command("apply")
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Print plan without applying.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def apply_style_cmd(name: str, dry_run: bool, yes: bool) -> None:
    """Apply a style preset globally.

    NAME is the preset name (e.g., SCITEX, MATPLOTLIB).

    \b
    Example:
      $ figrecipe style apply SCITEX
      $ figrecipe style apply MATPLOTLIB --dry-run
    """
    if dry_run:
        click.echo(f"DRY RUN — would apply style: {name}")
        return
    from .. import load_style

    try:
        load_style(name)
        click.echo(f"Applied style: {name}")
    except Exception as e:
        raise click.ClickException(f"Failed to apply style: {e}") from e


@style.command("reset")
@click.option("--dry-run", is_flag=True, help="Print plan without resetting.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def reset_style(dry_run: bool, yes: bool) -> None:
    """Reset to default matplotlib style.

    \b
    Example:
      $ figrecipe style reset
      $ figrecipe style reset --dry-run
    """
    if dry_run:
        click.echo("DRY RUN — would reset style to matplotlib defaults")
        return
    from .. import unload_style

    unload_style()
    click.echo("Style reset to defaults.")


@style.command("help-recursive", context_settings=CONTEXT_SETTINGS)
@click.pass_context
def help_recursive_cmd(ctx: click.Context) -> None:
    """Show help for all style subcommands.

    \b
    Example:
      $ figrecipe style help-recursive
    """
    _show_recursive_help(ctx.parent)
