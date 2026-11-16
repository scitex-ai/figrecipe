#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate command - Verify recipe reproducibility."""

from pathlib import Path

import click


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--threshold",
    type=float,
    default=100.0,
    help="MSE threshold for validation (default: 100).",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Fail on any difference.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Only output pass/fail status.",
)
def validate(
    source: str,
    threshold: float,
    strict: bool,
    quiet: bool,
) -> None:
    """Check recipe self-consistency by comparing two replayed renders.

    SOURCE is the path to a .yaml recipe file.
    This standalone check does not compare against the original image.

    \b
    Example:
      $ figrecipe validate figure.yaml
      $ figrecipe validate figure.yaml --threshold 10 --quiet
      $ figrecipe validate figure.yaml --strict
    """
    from .. import validate as fr_validate

    source_path = Path(source)

    if strict:
        threshold = 0.0

    try:
        result = fr_validate(source_path, mse_threshold=threshold)
    except Exception as e:
        raise click.ClickException(f"Validation failed: {e}") from e

    if quiet:
        if result.valid:
            click.echo("PASS")
        else:
            click.echo("FAIL")
            raise SystemExit(1)
    else:
        click.echo(f"Validation: {'PASS' if result.valid else 'FAIL'}")
        click.echo(f"MSE: {result.mse:.6f}")
        click.echo(f"Threshold: {threshold}")

        if hasattr(result, "message") and result.message:
            click.echo(f"Message: {result.message}")

        if not result.valid:
            raise SystemExit(1)
