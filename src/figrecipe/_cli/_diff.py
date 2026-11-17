#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diff command - Compare two images and report differences."""

from pathlib import Path

import click


@click.command()
@click.argument("original", type=click.Path(exists=True))
@click.argument("reproduced", type=click.Path(exists=True))
@click.option(
    "--threshold",
    type=int,
    default=0,
    help="Pixel difference threshold (0-255). Default: 0 (exact match).",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output statistics as JSON.",
)
def diff(
    original: str,
    reproduced: str,
    threshold: int,
    json_output: bool,
) -> None:
    """Compare two images and report pixel differences.

    ORIGINAL is the path to the original image.
    REPRODUCED is the path to the reproduced image.

    Reports match/mismatch statistics. For visualization, use 'figrecipe hitmap'.

    Examples:
        figrecipe diff original.png reproduced.png
        figrecipe diff original.png reproduced.png --threshold 5
        figrecipe diff original.png reproduced.png --json
        figrecipe --json diff original.png reproduced.png
    """
    context = click.get_current_context(silent=True)
    root_options = context.find_root().obj if context is not None else None
    json_output = json_output or (
        isinstance(root_options, dict) and bool(root_options.get("as_json"))
    )

    try:
        from .._utils._hitmap import compute_diff_stats
    except ImportError:
        raise click.ClickException(
            "Diff requires Pillow. Install with: pip install figrecipe[imaging]"
        ) from None

    original_path = Path(original)
    reproduced_path = Path(reproduced)

    try:
        stats = compute_diff_stats(
            original_path,
            reproduced_path,
            threshold=threshold,
        )

        if json_output:
            import json

            output_stats = {
                "match_ratio": stats["match_ratio"],
                "mismatch_ratio": stats["mismatch_ratio"],
                "match_pixels": stats["match_pixels"],
                "mismatch_pixels": stats["mismatch_pixels"],
                "total_pixels": stats["total_pixels"],
                "max_diff": stats["max_diff"],
                "mean_diff": stats["mean_diff"],
                "mse": stats["mse"],
                "is_match": stats["mismatch_pixels"] == 0,
            }
            click.echo(json.dumps(output_stats, indent=2))
        else:
            # Human-readable output
            is_match = stats["mismatch_pixels"] == 0
            status = (
                click.style("MATCH", fg="green")
                if is_match
                else click.style("MISMATCH", fg="red")
            )

            click.echo(f"Comparison: {status}")
            click.echo(
                f"  Match ratio:     {stats['match_ratio']:.4f} ({stats['match_pixels']:,} pixels)"
            )
            click.echo(
                f"  Mismatch ratio:  {stats['mismatch_ratio']:.4f} ({stats['mismatch_pixels']:,} pixels)"
            )
            click.echo(f"  Max difference:  {stats['max_diff']:.1f}")
            click.echo(f"  Mean difference: {stats['mean_diff']:.4f}")
            click.echo(f"  MSE:             {stats['mse']:.4f}")

    except Exception as e:
        raise click.ClickException(f"Comparison failed: {e}") from e
