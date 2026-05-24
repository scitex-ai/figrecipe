#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save figure as bundle (ZIP format)."""

import hashlib
import json
import tempfile
import warnings
import zipfile
from pathlib import Path
from typing import Optional, Union

from ._extract import (
    extract_data_from_record,
    extract_spec_from_record,
    extract_style_from_record,
)
from ._paths import DATA_FILENAME, EXPORTS_DIR, SPEC_FILENAME, STYLE_FILENAME


def save_bundle(
    fig,
    path: Union[str, Path],
    dpi: Optional[int] = None,
    image_formats: Optional[list] = None,
    save_hitmap: bool = False,
    verbose: bool = True,
) -> Path:
    """Save figure as a layered bundle (ZIP format).

    Bundle structure inside ZIP::

        spec.json      # WHAT (semantic specification)
        style.json     # HOW (appearance settings)
        data.csv       # DATA (immutable source data)
        recipe.yaml    # Reproducible recipe (for fr.reproduce())
        exports/
            figure.png
            figure_hitmap.png   # only if save_hitmap=True

    Parameters
    ----------
    fig : RecordingFigure
        The figure to save.
    path : str or Path
        Output path (.zip will be added if not present).
    dpi : int, optional
        DPI for exports (default from style or 300).
    image_formats : list, optional
        Image formats to export (default: ['png']).
    save_hitmap : bool
        Whether to save the per-pixel hitmap PNG used by the GUI editor
        for diff visualisation (default: False). Hitmap rendering is
        expensive and the typical save() caller doesn't need it; opt in
        with save_hitmap=True when persisting bundles for the editor.
    verbose : bool
        Whether to print status (default: True).

    Returns
    -------
    Path
        Path to saved ZIP bundle.
    """
    from .._wrappers import RecordingFigure

    if not isinstance(fig, RecordingFigure):
        raise TypeError(
            "Expected RecordingFigure. Use fr.subplots() to create "
            "a recording-enabled figure."
        )

    # Ensure .zip extension
    path = Path(path)
    if path.suffix.lower() != ".zip":
        path = path.with_suffix(".zip")

    # Get DPI
    if dpi is None:
        from .._api._save import get_save_dpi

        dpi = get_save_dpi()

    # Create temporary directory for bundle contents
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        exports_dir = tmpdir / EXPORTS_DIR
        exports_dir.mkdir()

        # Extract and save spec
        spec = extract_spec_from_record(fig.record)

        # Extract and save data
        df = extract_data_from_record(fig.record)
        if not df.empty:
            # Add data hash for integrity tracking
            data_hash = hashlib.sha256(df.to_csv().encode()).hexdigest()[:16]
            spec["data_hash"] = data_hash
            df.to_csv(tmpdir / DATA_FILENAME, index=False)

        # Save spec (after adding data_hash)
        with open(tmpdir / SPEC_FILENAME, "w") as f:
            json.dump(spec, f, indent=2, default=str)

        # Extract and save style
        style = extract_style_from_record(fig.record)
        with open(tmpdir / STYLE_FILENAME, "w") as f:
            json.dump(style, f, indent=2, default=str)

        # Export images
        image_formats = image_formats or ["png"]
        for fmt in image_formats:
            export_path = exports_dir / f"figure.{fmt}"
            fig.fig.savefig(export_path, dpi=dpi)

        # Save recipe.yaml for reproducibility
        try:
            recipe_path = tmpdir / "recipe.yaml"
            fig.save_recipe(
                recipe_path,
                include_data=True,
                data_format="csv",
                csv_format="separate",
            )
        except Exception as e:
            if verbose:
                warnings.warn(f"Recipe saving in bundle failed: {e}")

        # Save hitmap (diagram-specific if diagram detected, generic otherwise)
        if save_hitmap:
            try:
                mpl_fig = fig.fig if hasattr(fig, "fig") else fig
                diagram = getattr(mpl_fig, "_figrecipe_diagram", None)
                hitmap_path = exports_dir / "figure_hitmap.png"
                if diagram is not None:
                    from .._diagram._diagram._hitmap import save_diagram_hitmap

                    save_diagram_hitmap(diagram, hitmap_path, dpi=min(dpi, 150))
                else:
                    from .._editor._hitmap import generate_hitmap

                    hitmap_img, _ = generate_hitmap(fig, dpi=min(dpi, 150))
                    hitmap_img.save(hitmap_path)
            except Exception as e:
                if verbose:
                    warnings.warn(f"Hitmap generation failed: {e}")

        # Create ZIP file with root directory matching zip filename
        path.parent.mkdir(parents=True, exist_ok=True)
        root_dir = path.stem  # e.g., "figure" from "figure.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file():
                    arcname = Path(root_dir) / file.relative_to(tmpdir)
                    zf.write(file, arcname)

    if verbose:
        print(f"Saved bundle: {path}")
        print(f"  (extracts to: {path.stem}/)")
        with zipfile.ZipFile(path, "r") as zf:
            for info in zf.infolist():
                if not info.is_dir():
                    print(f"  {info.filename}: {info.file_size} bytes")

    return path
