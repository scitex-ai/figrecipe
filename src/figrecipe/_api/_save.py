#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save function helpers for the public API."""

from pathlib import Path
from typing import Optional, Tuple

# Import helpers from separate module
from ._save_helpers import _capture_axes_bboxes
from ._save_helpers import (
    save_hitmap as _save_hitmap,
)

# Image extensions supported for saving
IMAGE_EXTENSIONS = {
    ".png",
    ".pdf",
    ".svg",
    ".jpg",
    ".jpeg",
    ".eps",
    ".tiff",
    ".tif",
}
YAML_EXTENSIONS = {".yaml", ".yml"}


def resolve_save_paths(
    path: Path,
    image_format: Optional[str] = None,
) -> Tuple[Path, Path, str]:
    """Resolve image and YAML paths from the provided path.

    Parameters
    ----------
    path : Path
        User-provided output path.
    image_format : str, optional
        Explicit image format when path is YAML.

    Returns
    -------
    tuple
        (image_path, yaml_path, img_format)
    """
    suffix_lower = path.suffix.lower()

    if suffix_lower in IMAGE_EXTENSIONS:
        # User provided image path
        image_path = path
        yaml_path = path.with_suffix(".yaml")
        img_format = suffix_lower[1:]  # Remove leading dot
    elif suffix_lower in YAML_EXTENSIONS:
        # User provided YAML path
        yaml_path = path
        img_format = _get_default_image_format(image_format)
        image_path = path.with_suffix(f".{img_format}")
    else:
        # Unknown extension - treat as base name, add both extensions
        yaml_path = path.with_suffix(".yaml")
        img_format = _get_default_image_format(image_format)
        image_path = path.with_suffix(f".{img_format}")

    return image_path, yaml_path, img_format


def _get_default_image_format(explicit_format: Optional[str] = None) -> str:
    """Get default image format from style or fallback to png."""
    if explicit_format is not None:
        return explicit_format.lower().lstrip(".")

    # Check global style for preferred format
    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.format.lower()
        except (KeyError, AttributeError):
            pass
    return "png"


def get_save_dpi(explicit_dpi: Optional[int] = None) -> int:
    """Get DPI for saving, using style default if not specified."""
    if explicit_dpi is not None:
        return explicit_dpi

    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.dpi
        except (KeyError, AttributeError):
            pass
    return 300


def get_save_transparency() -> bool:
    """Get transparency setting from style."""
    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.transparent
        except (KeyError, AttributeError):
            pass
    return False


def _is_opaque_facecolor(facecolor) -> bool:
    """Check if facecolor is an opaque color (not transparent/none)."""
    if facecolor is None:
        return False
    if isinstance(facecolor, str):
        if facecolor.lower() in ("none", "transparent"):
            return False
    return True


def _make_patches_opaque(fig):
    """Temporarily make figure and axes patches opaque. Returns restore function."""
    original_alphas = []

    # Store and set figure patch alpha
    fig_patch = fig.fig.patch
    original_alphas.append(("fig", fig_patch.get_alpha()))
    fig_patch.set_alpha(1.0)

    # Store and set axes patch alphas
    for ax in fig.fig.get_axes():
        ax_patch = ax.patch
        original_alphas.append(("ax", ax, ax_patch.get_alpha()))
        ax_patch.set_alpha(1.0)

    def restore():
        for item in original_alphas:
            if item[0] == "fig":
                fig_patch.set_alpha(item[1])
            else:
                item[1].patch.set_alpha(item[2])

    return restore


def save_figure(
    fig,
    path,
    save_recipe: bool = True,
    include_data: bool = True,
    data_format: str = "csv",
    csv_format: str = "separate",
    validate: bool = True,
    validate_mse_threshold: float = 100.0,
    validate_error_level: str = "error",
    validate_axis_range_alignment: bool = True,
    validate_axis_range_alignment_error_level: str = "warning",
    verbose: bool = True,
    dpi: Optional[int] = None,
    image_format: Optional[str] = None,
    crop_margin_mm: Optional[float] = None,
    facecolor: Optional[str] = None,
    save_hitmap: bool = False,
):
    """Core save implementation.

    Supports multiple output formats:
    - Image file (.png, .pdf, etc.): Saves image + .yaml recipe (if save_recipe=True)
    - YAML file (.yaml): Saves recipe + image
    - ZIP file (.zip): Saves as layered bundle (spec.json + style.json + data.csv)
    - Directory (path/): Saves as directory bundle with recipe.yaml

    Parameters
    ----------
    fig : RecordingFigure
        The figure to save.
    path : str or Path
        Output path (.png, .pdf, .svg, .yaml, etc.)
    save_recipe : bool
        If True (default), save YAML recipe alongside the image.
    include_data : bool
        If True (default), save large arrays to separate files.
    data_format : str
        Format for data files: 'csv' (default), 'npz', or 'inline'.
    csv_format : str
        CSV file structure: 'separate' (default) or 'single'.
        - 'separate': One CSV file per variable
        - 'single': Single CSV with all columns (scitex/SigmaPlot-compatible)
    validate : bool
        If True (default), validate reproducibility after saving.
        Only applies when save_recipe=True.
    validate_mse_threshold : float
        Maximum acceptable MSE for validation (default: 100).
    validate_error_level : str
        How to handle validation failures: 'error', 'warning', or 'debug'.
    validate_axis_range_alignment : bool
        If True (default), run the runtime ``axis_range_alignment``
        check on the rendered figure before saving. Complements the
        static ``STX-FIG001`` lint rule by catching the autoscale-
        with-different-data case.
    validate_axis_range_alignment_error_level : str
        Dispatch level for the axis-range-alignment check:
        'warning' (default — never kills the script), 'error', or
        'debug' (silent).
    verbose : bool
        If True (default), print save status.
    dpi : int, optional
        DPI for image output.
    image_format : str, optional
        Image format when path is YAML.
    crop_margin_mm : float, optional
        If specified, auto-crop saved image to all ink/content plus this margin.
    facecolor : str, optional
        Background color for the saved image. When set to an opaque color,
        figure and axes patches are temporarily made opaque before saving.
    save_hitmap : bool
        If True (default), save a hitmap image alongside the figure for GUI
        editor use. For diagrams, generates element-ID-based hitmap with JSON
        sidecar. Saved as {basename}_hitmap.png.

    Returns
    -------
    tuple
        If save_recipe=True: (image_path, yaml_path, ValidationResult or None)
        If save_recipe=False: (image_path, None, None)
    """
    from .._wrappers import RecordingFigure

    path = Path(path)

    if not isinstance(fig, RecordingFigure):
        raise TypeError(
            "Expected RecordingFigure. Use fr.subplots() to create "
            "a recording-enabled figure."
        )

    # Get DPI and transparency from style if not specified
    dpi = get_save_dpi(dpi)
    transparent = get_save_transparency()

    # Finalize tick configuration and special plot types for all axes
    from ..styles._kwargs_converter import to_subplots_kwargs
    from ..styles._style_applier import finalize_special_plots, finalize_ticks

    style_dict = to_subplots_kwargs()

    for ax in fig.fig.get_axes():
        finalize_ticks(ax)
        finalize_special_plots(ax, style_dict)

    # Runtime axis-range-alignment check (complements static STX-FIG001).
    # Default warning-level — per operator preference (figrecipe #134), never
    # kill the script after the PNG has been written.
    if validate_axis_range_alignment:
        from .._quality._axis_range_alignment import run_axis_range_alignment

        run_axis_range_alignment(
            fig.fig,
            validate_error_level=validate_axis_range_alignment_error_level,
        )

    # Check for .fig.zip (multi-panel Figz bundle) or .plt.zip (single-plot Pltz bundle)
    suffixes = [s.lower() for s in path.suffixes]
    if suffixes[-2:] == [".fig", ".zip"]:
        from .._bundle._figz import Figz
        from .._bundle._pltz import Pltz

        # Create a Figz bundle with the current figure as a single panel
        figz = Figz.create(path, name=path.stem.split(".")[0])
        # Save figure as a temporary .plt.zip, then add as panel
        import tempfile

        tmp_pltz = Path(tempfile.mktemp(suffix=".plt.zip"))
        try:
            Pltz.create(tmp_pltz, fig)
            figz.add_panel("A", tmp_pltz)
        finally:
            if tmp_pltz.exists():
                tmp_pltz.unlink()
        if verbose:
            print(f"Saved: {path} (Figz bundle)")
        return path, None, None

    if suffixes[-2:] == [".plt", ".zip"]:
        from .._bundle._pltz import Pltz

        Pltz.create(path, fig)
        if verbose:
            print(f"Saved: {path} (Pltz bundle)")
        return path, None, None

    # Bare .zip (no .plt./.fig. infix) and directory-bundle dispatch are
    # intentionally NOT supported. figrecipe owns I/O via .plt.zip / .fig.zip;
    # anything else routes to standard image+recipe save below.

    # Resolve paths for standard save
    image_path, yaml_path, _ = resolve_save_paths(path, image_format)

    # Check for diagram validation errors (stored by ax.diagram())
    _diagram_errors = getattr(fig.fig, "_diagram_validation_errors", None)
    if _diagram_errors:
        image_path = image_path.with_stem(f"{image_path.stem}_FAILED")

    # Check if using constrained_layout - need different save strategy
    use_constrained = fig.fig.get_constrained_layout()

    # Get crop margins from mm_layout
    mm_layout = getattr(fig, "_mm_layout", None)
    crop_margin_left_mm = 1
    crop_margin_right_mm = 1
    crop_margin_top_mm = 1
    crop_margin_bottom_mm = 1
    if mm_layout is not None and "crop_margin_left_mm" in mm_layout:
        crop_margin_left_mm = mm_layout.get("crop_margin_left_mm", 1)
        crop_margin_right_mm = mm_layout.get("crop_margin_right_mm", 1)
        crop_margin_top_mm = mm_layout.get("crop_margin_top_mm", 1)
        crop_margin_bottom_mm = mm_layout.get("crop_margin_bottom_mm", 1)

    # Handle facecolor override - make patches opaque if needed
    restore_patches = None
    if _is_opaque_facecolor(facecolor):
        restore_patches = _make_patches_opaque(fig)

    pad_inches = 0.0  # updated below if use_constrained

    try:
        if use_constrained:
            # For constrained_layout, use bbox_inches='tight' to crop at save time
            avg_margin_mm = (
                crop_margin_left_mm
                + crop_margin_right_mm
                + crop_margin_top_mm
                + crop_margin_bottom_mm
            ) / 4
            pad_inches = avg_margin_mm / 25.4  # mm to inches

            # Pre-flight: draw figure to detect constrained_layout collapse
            # before attempting bbox_inches="tight" save (which hangs for e.g. quiver
            # when axes collapse to zero and draw_path loops endlessly on degenerate paths).
            import warnings as _warnings

            _collapse_detected = False
            with _warnings.catch_warnings(record=True) as _w:
                _warnings.simplefilter("always")
                try:
                    fig.fig.canvas.draw()
                except Exception:
                    pass
                if any("collapsed to zero" in str(w.message) for w in _w):
                    _collapse_detected = True

            try:
                if _collapse_detected:
                    raise ValueError("constrained_layout collapsed axes to zero")
                fig.fig.savefig(
                    image_path,
                    dpi=dpi,
                    transparent=transparent,
                    bbox_inches="tight",
                    pad_inches=pad_inches,
                    facecolor=facecolor,
                )
            except (MemoryError, ValueError):
                # constrained_layout may fail for some plot types (e.g., quiver)
                # ValueError: image size too large on older matplotlib
                # Fall back to standard save without bbox_inches
                import warnings

                warnings.warn(
                    "constrained_layout save failed, falling back to standard save"
                )
                fig.fig.savefig(
                    image_path, dpi=dpi, transparent=transparent, facecolor=facecolor
                )
                # Mark for cropping since we couldn't use bbox_inches="tight"
                use_constrained = False
        else:
            # Standard save without bbox_inches to preserve mm layout
            fig.fig.savefig(
                image_path, dpi=dpi, transparent=transparent, facecolor=facecolor
            )
    finally:
        # Restore original patch alphas
        if restore_patches is not None:
            restore_patches()

    # Auto-crop using stored crop margins from mm_layout (or explicit parameter)
    # Raster formats: pixel-based content-aware crop (post-processing)
    # SVG: viewBox adjustment via tightbbox query (post-processing, no bbox_inches)
    # Skip for constrained_layout (already cropped at save time)
    croppable_formats = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
    is_croppable = image_path.suffix.lower() in croppable_formats
    is_svg = image_path.suffix.lower() == ".svg"

    crop_offset = None
    if is_croppable and not use_constrained:
        if crop_margin_mm is not None:
            # Explicit uniform crop margin
            from .._utils._crop import crop

            _, crop_offset = crop(
                image_path,
                margin_mm=crop_margin_mm,
                output_path=image_path,
                return_offset=True,
            )
        elif mm_layout is not None and "crop_margin_left_mm" in mm_layout:
            # Standard content-based cropping for mm_layout figures
            from .._utils._crop import crop

            _, crop_offset = crop(
                image_path,
                margin_left_mm=crop_margin_left_mm,
                margin_right_mm=crop_margin_right_mm,
                margin_top_mm=crop_margin_top_mm,
                margin_bottom_mm=crop_margin_bottom_mm,
                output_path=image_path,
                return_offset=True,
            )

    elif is_svg and not use_constrained:
        # SVG: adjust viewBox post-save using tightbbox query (not bbox_inches='tight')
        from .._utils._crop import crop_svg

        avg_margin_mm = (
            crop_margin_left_mm
            + crop_margin_right_mm
            + crop_margin_top_mm
            + crop_margin_bottom_mm
        ) / 4
        if crop_margin_mm is not None:
            avg_margin_mm = crop_margin_mm
        crop_svg(image_path, fig.fig, margin_mm=avg_margin_mm)

    # Capture axes bounding boxes (adjusted for crop if cropping occurred)
    _capture_axes_bboxes(fig, crop_offset)

    # Store crop info in record for future reference
    if crop_offset is not None:
        fig.record.crop_info = crop_offset

    # Store mm_layout in record for consistent cropping on reproduce
    if hasattr(fig, "_mm_layout") and fig._mm_layout is not None:
        fig.record.mm_layout = fig._mm_layout

    # Save hitmap if requested (for GUI editor element selection)
    # Pass bbox_inches="tight" when the image was saved that way (constrained_layout)
    # so the hitmap crop matches the saved image exactly (critical for pie/imshow).
    if save_hitmap:
        _hitmap_bbox = "tight" if use_constrained else None
        _hitmap_pad = pad_inches if use_constrained else 0.0
        _save_hitmap(fig, image_path, dpi, verbose, _hitmap_bbox, _hitmap_pad)

    # If not saving recipe, return early
    if not save_recipe:
        if verbose:
            print(f"Saved: {image_path}")
        if _diagram_errors:
            raise ValueError("\n  ".join(_diagram_errors))
        return image_path, None, None

    # Raise diagram validation errors after saving image (before recipe)
    if _diagram_errors:
        if verbose:
            print(f"Saved (with errors): {image_path}")
        raise ValueError("\n  ".join(_diagram_errors))

    # Save the recipe
    saved_yaml = fig.save_recipe(
        yaml_path,
        include_data=include_data,
        data_format=data_format,
        csv_format=csv_format,
    )

    # Validate if requested
    if validate:
        from .._quality._validator import validate_on_save

        result = validate_on_save(fig, saved_yaml, mse_threshold=validate_mse_threshold)
        status = "PASSED" if result.valid else "FAILED"
        if verbose:
            print(
                f"Saved: {image_path} + {yaml_path} (Reproducible Validation: {status})"
            )
        if not result.valid:
            msg = f"Reproducibility validation failed (MSE={result.mse:.1f}): {result.message}"
            if validate_error_level == "error":
                raise ValueError(msg)
            elif validate_error_level == "warning":
                import warnings

                warnings.warn(msg, UserWarning)
            # "debug" level: silent, just return the result
        return image_path, yaml_path, result

    if verbose:
        print(f"Saved: {image_path} + {yaml_path}")
    return image_path, yaml_path, None


__all__ = [
    "IMAGE_EXTENSIONS",
    "YAML_EXTENSIONS",
    "resolve_save_paths",
    "get_save_dpi",
    "get_save_transparency",
    "save_figure",
]
