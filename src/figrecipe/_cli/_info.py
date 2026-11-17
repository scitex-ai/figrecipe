#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info command - Inspect recipe metadata."""

import json
from pathlib import Path

import click

from ._json_output import json_requested


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as JSON.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed information.",
)
def info(source: str, as_json: bool, verbose: bool) -> None:
    """Show information about a recipe.

    SOURCE is the path to a .yaml recipe file.

    \b
    Example:
      $ figrecipe info figure.yaml
      $ figrecipe info figure.yaml --verbose
      $ figrecipe info figure.yaml --json
    """
    as_json = json_requested(as_json)

    from .. import info as fr_info

    source_path = Path(source)

    try:
        recipe_info = fr_info(source_path)
    except Exception as e:
        raise click.ClickException(f"Failed to load recipe: {e}") from e

    if as_json:
        click.echo(json.dumps(recipe_info, indent=2, default=str))
    else:
        _print_info(recipe_info, verbose)


def _print_info(info: dict, verbose: bool) -> None:
    """Print recipe info in human-readable format."""
    click.echo(f"Recipe Version: {info.get('figrecipe_version', 'unknown')}")
    click.echo(f"Figure ID: {info.get('id', 'unknown')}")
    click.echo(f"Created: {info.get('created', 'unknown')}")
    click.echo(f"Matplotlib: {info.get('matplotlib_version', 'unknown')}")

    if "figure" in info:
        fig = info["figure"]
        click.echo(f"Figure Size: {fig.get('figsize', 'unknown')}")
        click.echo(f"DPI: {fig.get('dpi', 'unknown')}")

    if "axes" in info:
        click.echo(f"Axes Count: {len(info['axes'])}")

        if verbose:
            for ax_key, ax_info in info["axes"].items():
                click.echo(f"\n  {ax_key}:")
                if "calls" in ax_info:
                    for call in ax_info["calls"]:
                        func = call.get("function", "unknown")
                        call_id = call.get("id", "")
                        click.echo(f"    - {func} ({call_id})")
