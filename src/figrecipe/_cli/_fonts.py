#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fonts command - Font management."""

from typing import Optional

import click


@click.command("list-fonts")
@click.option(
    "--check",
    type=str,
    help="Check if a specific font is available.",
)
@click.option(
    "--search",
    type=str,
    help="Search for fonts matching a pattern.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
def fonts(check: Optional[str], search: Optional[str], as_json: bool) -> None:
    """List or check available fonts.

    \b
    Example:
      $ figrecipe list-fonts
      $ figrecipe list-fonts --search arial
      $ figrecipe list-fonts --check "DejaVu Sans"
      $ figrecipe list-fonts --json
    """
    import json

    from ..styles._style_applier import check_font, list_available_fonts

    if check:
        available = check_font(check)
        if as_json:
            click.echo(json.dumps({"font": check, "available": bool(available)}))
        else:
            click.echo(
                f"Font '{check}' is {'available' if available else 'NOT available'}."
            )
        if not available:
            raise SystemExit(1)
        return

    all_fonts = sorted(list_available_fonts())

    if search:
        pattern = search.lower()
        matching = [f for f in all_fonts if pattern in f.lower()]
        if as_json:
            click.echo(json.dumps({"search": search, "fonts": matching}))
        else:
            click.echo(f"Fonts matching '{search}':")
            for font in matching:
                click.echo(f"  {font}")
            click.echo(f"\nFound {len(matching)} matching fonts.")
    else:
        if as_json:
            click.echo(json.dumps({"fonts": all_fonts}))
        else:
            click.echo("Available fonts:")
            for font in all_fonts:
                click.echo(f"  {font}")
            click.echo(f"\nTotal: {len(all_fonts)} fonts.")
