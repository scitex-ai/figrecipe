#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crop command - Crop image to content."""

from pathlib import Path
from typing import Optional

import click


@click.command()
@click.argument("image", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output path for cropped image.",
)
@click.option(
    "--margin",
    type=str,
    default="1mm",
    help="Margin around content (e.g., '2mm' or '10px'). Default: 1mm.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite the input file.",
)
def crop(
    image: str,
    output: Optional[str],
    margin: str,
    overwrite: bool,
) -> None:
    """Crop an image to its content area.

    IMAGE is a Pillow-supported raster image, such as PNG or JPEG.
    PDF input is not supported. The margin is uniform on all sides.

    \b
    Example:
      $ figrecipe crop figure.png
      $ figrecipe crop figure.png -o trimmed.png --margin 2mm
      $ figrecipe crop figure.png --overwrite --margin 5px
    """
    try:
        from .. import crop as fr_crop
    except ImportError:
        raise click.ClickException(
            "Crop requires Pillow. Install with: pip install figrecipe[imaging]"
        ) from None

    image_path = Path(image)

    # Parse margin
    margin_mm = None
    margin_px = None

    if margin.endswith("mm"):
        margin_mm = float(margin[:-2])
    elif margin.endswith("px"):
        margin_px = int(margin[:-2])
    else:
        # Default to mm
        try:
            margin_mm = float(margin)
        except ValueError:
            raise click.ClickException(f"Invalid margin format: {margin}") from None

    # Determine output path
    if output:
        output_path = Path(output)
    elif overwrite:
        output_path = None  # Will overwrite in place
    else:
        output_path = image_path.with_stem(f"{image_path.stem}_cropped")

    try:
        result = fr_crop(
            image_path,
            output_path=output_path,
            margin_mm=margin_mm,
            margin_px=margin_px,
            overwrite=overwrite,
        )
        click.echo(f"Cropped: {result}")
    except Exception as e:
        raise click.ClickException(f"Crop failed: {e}") from e
