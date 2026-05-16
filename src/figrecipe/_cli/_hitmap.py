#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hitmap command - Generate hitmap visualization from image comparison."""

from pathlib import Path
from typing import Optional

import click


@click.command("show-hitmap")
@click.argument("original", type=click.Path(exists=True))
@click.argument("reproduced", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output path for hitmap image.",
)
@click.option(
    "--mode",
    type=click.Choice(["diff", "binary", "heatmap"]),
    default="diff",
    help="Visualization mode. Default: diff.",
)
@click.option(
    "--threshold",
    type=int,
    default=0,
    help="Pixel difference threshold (0-255). Default: 0 (exact match).",
)
@click.option(
    "--no-bbox",
    is_flag=True,
    help="Disable bounding boxes around diff regions.",
)
@click.option(
    "--min-region",
    type=int,
    default=10,
    help="Minimum pixel area for bounding box. Default: 10.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
def hitmap(
    original: str,
    reproduced: str,
    output: Optional[str],
    mode: str,
    threshold: int,
    no_bbox: bool,
    min_region: int,
    as_json: bool,
) -> None:
    """Generate hitmap visualization from two images.

    ORIGINAL is the path to the original image.
    REPRODUCED is the path to the reproduced image.

    The hitmap shows pixel differences:
    - diff mode: Green=match, red intensity=difference magnitude
    - binary mode: Green=match, red=mismatch
    - heatmap mode: Colormap showing difference magnitude

    Examples:
        figrecipe hitmap original.png reproduced.png
        figrecipe hitmap original.png reproduced.png -o hitmap.png --mode binary
        figrecipe hitmap original.png reproduced.png --threshold 5
    """
    try:
        from .._utils._hitmap import create_hitmap
    except ImportError:
        raise click.ClickException(
            "Hitmap requires Pillow. Install with: pip install figrecipe[imaging]"
        ) from None

    original_path = Path(original)
    reproduced_path = Path(reproduced)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = original_path.with_stem(f"{original_path.stem}_hitmap")

    import json

    try:
        _, stats = create_hitmap(
            original_path,
            reproduced_path,
            output_path=output_path,
            mode=mode,
            threshold=threshold,
            show_bbox=not no_bbox,
            min_region_area=min_region,
        )

        if as_json:
            click.echo(
                json.dumps({"output": str(output_path), "mode": mode, "stats": stats})
            )
        else:
            click.echo(f"Hitmap saved: {output_path}")
            click.echo(f"  Mode: {mode}")
            click.echo(f"  Diff regions: {stats['num_regions']}")

    except Exception as e:
        raise click.ClickException(f"Hitmap generation failed: {e}") from e
