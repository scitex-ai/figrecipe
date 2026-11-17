#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""version command - Show version information."""

import click

from ._json_output import json_requested


@click.command(
    "version", hidden=True, context_settings={"ignore_unknown_options": True}
)
@click.pass_context
def version(ctx) -> None:
    """(deprecated) Use `figrecipe --version` or `figrecipe show-version --full`."""
    click.echo(
        "error: `figrecipe version` was replaced by `figrecipe --version` "
        "(or `figrecipe show-version --full` for dependency info).\n"
        "Re-run with: figrecipe --version",
        err=True,
    )
    ctx.exit(2)


@click.command("show-version")
@click.option(
    "--full",
    is_flag=True,
    help="Show full version info with dependencies.",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def show_version(full: bool, as_json: bool) -> None:
    """Show figrecipe version (and dependencies with --full).

    \b
    Example:
      $ figrecipe show-version
      $ figrecipe show-version --full
      $ figrecipe show-version --full --json
    """
    as_json = json_requested(as_json)

    from .. import __version__

    if as_json:
        import json as _json

        payload: dict = {"figrecipe": __version__}
        if full:
            payload["dependencies"] = _collect_dependency_versions()
            import sys as _sys

            payload["python"] = _sys.version
        click.echo(_json.dumps(payload, indent=2))
        return

    click.echo(f"figrecipe {__version__}")

    if full:
        click.echo()
        _show_dependency_versions()


def _collect_dependency_versions() -> dict:
    deps = [
        ("matplotlib", "matplotlib"),
        ("numpy", "numpy"),
        ("ruamel.yaml", "ruamel.yaml"),
        ("scipy", "scipy"),
        ("Pillow", "PIL"),
        ("seaborn", "seaborn"),
        ("pandas", "pandas"),
        ("django", "django"),
    ]
    out = {}
    for name, module in deps:
        try:
            mod = __import__(module)
            out[name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            out[name] = "not installed"
    return out


def _show_dependency_versions() -> None:
    """Show versions of key dependencies."""
    deps = [
        ("matplotlib", "matplotlib"),
        ("numpy", "numpy"),
        ("ruamel.yaml", "ruamel.yaml"),
        ("scipy", "scipy"),
        ("Pillow", "PIL"),
        ("seaborn", "seaborn"),
        ("pandas", "pandas"),
        ("django", "django"),
    ]

    click.echo("Dependencies:")
    for name, module in deps:
        try:
            mod = __import__(module)
            ver = getattr(mod, "__version__", "unknown")
            click.echo(f"  {name}: {ver}")
        except ImportError:
            click.echo(f"  {name}: not installed")

    # Python version
    import sys

    click.echo(f"\nPython: {sys.version}")
