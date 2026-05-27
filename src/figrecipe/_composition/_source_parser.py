#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source parsing for composition: image files, YAML recipes, FigureRecords.

When an image file (PNG, etc.) has a companion YAML recipe alongside it,
the recipe is preferred so that individual plot elements are preserved
for hitmap selection in the editor.
"""

from pathlib import Path
from typing import Optional, Tuple, Union

from .._recorder import FigureRecord
from .._serializer import load_recipe
from .._utils._grid import grid_id

_DEFAULT_AX_KEY = grid_id(0, 0)

# Supported image file extensions for raw image composition
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
# SVG requires special handling (vector format)
VECTOR_EXTENSIONS = {".svg"}


def is_image_file(path: Path) -> bool:
    """Check if path is a supported image file."""
    suffix = path.suffix.lower()
    return suffix in IMAGE_EXTENSIONS or suffix in VECTOR_EXTENSIONS


def find_companion_recipe(image_path: Path) -> Optional[Path]:
    """Find a companion YAML recipe for an image file.

    Checks for .yaml alongside the image (e.g., panel_a.png -> panel_a.yaml).
    Returns the recipe path if found, None otherwise.
    """
    yaml_path = image_path.with_suffix(".yaml")
    if yaml_path.exists():
        return yaml_path
    return None


def create_image_record(image_path: Path) -> FigureRecord:
    """Create a FigureRecord from a raw image file."""
    from datetime import datetime

    import matplotlib
    import numpy as np
    from PIL import Image

    from .._recorder import AxesRecord, CallRecord

    suffix = image_path.suffix.lower()
    if suffix == ".svg":
        try:
            import io

            import cairosvg

            png_data = cairosvg.svg2png(url=str(image_path))
            img = Image.open(io.BytesIO(png_data))
        except ImportError:
            raise ImportError(
                "cairosvg is required for SVG support. Install with: pip install cairosvg"
            )
    else:
        img = Image.open(image_path)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    img_array = np.array(img)

    imshow_call = CallRecord(
        id=f"imshow_{image_path.stem}",
        function="imshow",
        args=[{"name": "X", "dtype": "ndarray", "data": img_array.tolist()}],
        kwargs={"aspect": "equal"},
        timestamp=datetime.now().isoformat(),
        ax_position=(0, 0),
    )

    axis_off_call = CallRecord(
        id="axis_off",
        function="axis",
        args=[{"name": "arg0", "data": "off"}],
        kwargs={},
        timestamp=datetime.now().isoformat(),
        ax_position=(0, 0),
    )

    ax_record = AxesRecord(
        position=(0, 0),
        calls=[imshow_call],
        decorations=[axis_off_call],
    )

    height, width = img_array.shape[:2]
    dpi = 100
    figsize = (width / dpi, height / dpi)

    record = FigureRecord(
        figsize=figsize,
        dpi=dpi,
        matplotlib_version=matplotlib.__version__,
    )
    record.axes[_DEFAULT_AX_KEY] = ax_record

    return record


def parse_source_spec(
    spec: Union[str, Path, FigureRecord, Tuple],
) -> Tuple[FigureRecord, str]:
    """Parse source specification into (FigureRecord, ax_key)."""
    record, ax_key, _ = parse_source_spec_with_path(spec)
    return record, ax_key


def parse_source_spec_with_path(
    spec: Union[str, Path, FigureRecord, Tuple],
) -> Tuple[FigureRecord, str, Optional[Path]]:
    """Parse source specification into (FigureRecord, ax_key, source_path).

    When an image file has a companion YAML recipe, the recipe is preferred
    so individual plot elements are preserved for editor hitmap selection.
    """
    if isinstance(spec, (str, Path)):
        path = Path(spec)
        if is_image_file(path):
            recipe = find_companion_recipe(path)
            if recipe is not None:
                return load_recipe(recipe), _DEFAULT_AX_KEY, recipe
            return create_image_record(path), _DEFAULT_AX_KEY, path
        return load_recipe(path), _DEFAULT_AX_KEY, path
    elif isinstance(spec, FigureRecord):
        return spec, _DEFAULT_AX_KEY, None
    elif isinstance(spec, tuple) and len(spec) == 2:
        source, ax_key = spec
        if isinstance(source, (str, Path)):
            path = Path(source)
            if is_image_file(path):
                recipe = find_companion_recipe(path)
                if recipe is not None:
                    return load_recipe(recipe), ax_key, recipe
                return create_image_record(path), _DEFAULT_AX_KEY, path
            return load_recipe(path), ax_key, path
        elif isinstance(source, FigureRecord):
            return source, ax_key, None
        raise TypeError(f"Invalid source in tuple: {type(source)}")
    raise TypeError(f"Invalid source spec type: {type(spec)}")


__all__ = [
    "is_image_file",
    "find_companion_recipe",
    "create_image_record",
    "parse_source_spec",
    "parse_source_spec_with_path",
]

# EOF
