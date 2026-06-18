#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save function helpers for the public API."""

from pathlib import Path
from typing import Optional

# figrecipe routes its save / reproducibility-validation status through
# scitex-logging when available, so those lines carry the same INFO:/SUCC:/WARN:
# prefixes + colours as scitex.io and @stx.session scripts (no more bare,
# uncoloured print() output next to scitex-logging lines). Loosely coupled --
# the same try-import policy as the scitex-clew integration; falls back to
# print() when scitex-logging is absent.
from .._logging import get_logger

# Import helpers from separate module
from ._save_capture import _capture_colorbar_geometry

# Save settings / path / transparency helpers live in _save_config; re-exported
# here so existing ``from .._api._save import get_save_dpi`` (etc.) keep working.
from ._save_config import (  # noqa: F401
    IMAGE_EXTENSIONS,
    YAML_EXTENSIONS,
    _get_default_image_format,
    _is_opaque_facecolor,
    _make_patches_opaque,
    format_saved_target,
    get_save_dpi,
    get_save_transparency,
    resolve_save_paths,
)
from ._save_crop import dispatch_crop, wants_content_crop
from ._save_helpers import (
    _capture_axes_bboxes,
    _capture_content_layout,
)
from ._save_helpers import (
    save_hitmap as _save_hitmap,
)

_log = get_logger("figrecipe")


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
            _log.success(f"Saved: {path} (Figz bundle)")
        return path, None, None

    if suffixes[-2:] == [".plt", ".zip"]:
        from .._bundle._pltz import Pltz

        Pltz.create(path, fig)
        if verbose:
            _log.success(f"Saved: {path} (Pltz bundle)")
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

    # Output-format flags (used both to pick the save strategy and to crop).
    croppable_formats = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
    is_croppable = image_path.suffix.lower() in croppable_formats
    is_svg = image_path.suffix.lower() == ".svg"

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

    # Crop strategy. ``content_bbox`` crop (saved full-canvas, then cropped to the
    # ONE recorded, dpi-independent box) is deterministic across draw counts, so
    # the original and every reproduce land at identical pixels -- it replaces
    # BOTH the size-jittering ``bbox_inches="tight"`` (constrained_layout) and the
    # content-aware ``crop()`` (composed/mm-layout). ``use_tight`` is therefore
    # only the LEGACY constrained path used when content_bbox is unavailable; for
    # the quiver collapse case the settle below clears both flags and we fall back
    # to the content-aware crop. (#215 generalised from standalone diagrams.)
    use_content_crop = wants_content_crop(is_croppable, use_constrained, mm_layout)
    use_tight = use_constrained and not use_content_crop

    # Handle facecolor override - make patches opaque if needed
    restore_patches = None
    if _is_opaque_facecolor(facecolor):
        restore_patches = _make_patches_opaque(fig)

    pad_inches = 0.0  # updated below if use_tight

    try:
        if use_constrained:
            # Settle constrained_layout to its CONVERGED fixed point before saving.
            # constrained_layout solves the axes rectangle iteratively, so a single
            # draw leaves it part-way and any save-time ink re-measure then depends
            # on how many times the figure was drawn -- making a recipe
            # unreproducible (the original fig is drawn far more than a fresh
            # reproduce()-d one). Settling makes the geometry a pure function of the
            # content, so original and reproduced share the SAME content_bbox. The
            # first draw still surfaces the "collapsed to zero" warning used by the
            # quiver fallback (degenerate paths make a tight save loop endlessly).
            from ._save_layout import (
                freeze_layout_positions,
                settle_constrained_layout,
            )

            _collapse_detected = settle_constrained_layout(fig.fig)

            # A shared colorbar's space-steal has no single constrained_layout fixed
            # point (it drifts with draw history), so freeze the converged geometry
            # -- otherwise the original, the validator's re-render and a fresh
            # reproduce() each settle to slightly different rectangles. Only when a
            # colorbar is present (the no-colorbar path is already deterministic).
            if not _collapse_detected and getattr(fig.record, "colorbars", None):
                freeze_layout_positions(fig.fig)

            if _collapse_detected:
                # Degenerate layout: never content-crop a collapsed figure; save
                # full-canvas and fall back to the content-aware crop downstream.
                use_content_crop = False
                use_tight = False
                fig.fig.savefig(
                    image_path, dpi=dpi, transparent=transparent, facecolor=facecolor
                )
            elif use_content_crop:
                # Save FULL-CANVAS; cropped to the recorded content_bbox below so the
                # saved SIZE is a deterministic function of content (no tight re-
                # measure). Replaces bbox_inches="tight" for constrained_layout.
                fig.fig.savefig(
                    image_path, dpi=dpi, transparent=transparent, facecolor=facecolor
                )
            else:
                # LEGACY constrained path (content_bbox unavailable): crop at save
                # time via bbox_inches="tight" (size-jittering, kept for back-compat).
                avg_margin_mm = (
                    crop_margin_left_mm
                    + crop_margin_right_mm
                    + crop_margin_top_mm
                    + crop_margin_bottom_mm
                ) / 4
                pad_inches = avg_margin_mm / 25.4  # mm to inches
                try:
                    fig.fig.savefig(
                        image_path,
                        dpi=dpi,
                        transparent=transparent,
                        bbox_inches="tight",
                        pad_inches=pad_inches,
                        facecolor=facecolor,
                    )
                except (MemoryError, ValueError):
                    # constrained_layout may fail for some plot types (e.g. quiver);
                    # ValueError: image size too large on older matplotlib. Fall
                    # back to a standard save + downstream content-aware crop.
                    import warnings

                    warnings.warn(
                        "constrained_layout save failed, falling back to standard save"
                    )
                    fig.fig.savefig(
                        image_path,
                        dpi=dpi,
                        transparent=transparent,
                        facecolor=facecolor,
                    )
                    use_constrained = False
                    use_tight = False
        else:
            # Standard save without bbox_inches to preserve mm layout
            fig.fig.savefig(
                image_path, dpi=dpi, transparent=transparent, facecolor=facecolor
            )
    finally:
        # Restore original patch alphas
        if restore_patches is not None:
            restore_patches()

    # Post-save crop dispatch (see _save_crop):
    #   * content_bbox crop -- saved full-canvas above, cropped to the ONE recorded
    #     dpi-independent box so the original and every reproduce land at identical
    #     pixels (constrained_layout + composed/mm-layout). Falls back, WITH a
    #     UserWarning, to the legacy crop when content_bbox is underivable.
    #   * legacy content-aware crop() for raster, or crop_svg() for SVG.
    #   * skipped when bbox_inches="tight" already cropped at save time (use_tight).
    crop_offset = dispatch_crop(
        fig,
        image_path,
        is_croppable=is_croppable,
        is_svg=is_svg,
        use_tight=use_tight,
        use_content_crop=use_content_crop,
        crop_margin_mm=crop_margin_mm,
        crop_margins_mm=(
            crop_margin_left_mm,
            crop_margin_right_mm,
            crop_margin_top_mm,
            crop_margin_bottom_mm,
        ),
        mm_layout=mm_layout,
        dpi=dpi,
    )

    # Capture axes bounding boxes (adjusted for crop if cropping occurred)
    _capture_axes_bboxes(fig, crop_offset)
    _capture_colorbar_geometry(fig)  # pin shared-colorbar geometry for replay
    _capture_content_layout(fig)  # tight-content layout for crop-aware compose

    # Store crop info in record for future reference
    if crop_offset is not None:
        fig.record.crop_info = crop_offset

    # Store mm_layout in record for consistent cropping on reproduce
    if hasattr(fig, "_mm_layout") and fig._mm_layout is not None:
        fig.record.mm_layout = fig._mm_layout

    # Save hitmap if requested (for GUI editor element selection).
    # The hitmap must be cropped IDENTICALLY to the saved image so pixel->element
    # lookups line up:
    #   * use_tight  -> render the hitmap with the same bbox_inches="tight"+pad.
    #   * content-crop -> render full-canvas, then crop to the SAME content_bbox.
    #   * otherwise (content-aware/no crop) -> full-canvas (matches the image).
    # Standalone diagrams render their hitmap separately regardless.
    if save_hitmap:
        _hitmap_bbox = "tight" if use_tight else None
        _hitmap_pad = pad_inches if use_tight else 0.0
        _hitmap_path = _save_hitmap(
            fig, image_path, dpi, verbose, _hitmap_bbox, _hitmap_pad
        )
        if (
            use_content_crop
            and _hitmap_path is not None
            and getattr(fig.record, "content_bbox", None) is not None
        ):
            from ._save_helpers import crop_to_content_bbox

            _hm_margins = (
                {
                    "left": crop_margin_mm,
                    "right": crop_margin_mm,
                    "top": crop_margin_mm,
                    "bottom": crop_margin_mm,
                }
                if crop_margin_mm is not None
                else {
                    "left": crop_margin_left_mm,
                    "right": crop_margin_right_mm,
                    "top": crop_margin_top_mm,
                    "bottom": crop_margin_bottom_mm,
                }
            )
            crop_to_content_bbox(
                _hitmap_path, fig.record.content_bbox, _hm_margins, min(dpi, 150)
            )
    from ._separate_legend import save_separate_legends as _sl

    _sl(fig, image_path, dpi=dpi, save_recipe=save_recipe)

    # If not saving recipe, return early
    if not save_recipe:
        if verbose:
            _log.success(f"Saved: {image_path}")
        if _diagram_errors:
            raise ValueError("\n  ".join(_diagram_errors))
        return image_path, None, None

    # Raise diagram validation errors after saving image (before recipe)
    if _diagram_errors:
        if verbose:
            _log.warning(f"Saved (with errors): {image_path}")
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

        result = validate_on_save(
            fig,
            saved_yaml,
            mse_threshold=validate_mse_threshold,
            image_path=image_path,
        )
        if verbose:
            # image + recipe collapse to fig.{png,yaml}. Through scitex-logging:
            # green SUCC when reproducible, red ERROR *with the reason* otherwise
            # (not a bare "FAILED"). "Reproducibility Validation" = we validated
            # that the recipe reproduces the figure.
            target = format_saved_target(image_path, yaml_path)
            if result.valid:
                _log.success(f"Saved: {target} (Reproducibility Validation: PASSED)")
            else:
                # Point at the persisted reproduced figure so the divergence is
                # inspectable (saved beside the figure as <stem>-not-reproduced.<ext>).
                hint = ""
                if getattr(result, "not_reproduced_path", None):
                    from pathlib import Path as _P

                    hint = f"; see {_P(result.not_reproduced_path).name}"
                _log.error(
                    f"Saved: {target} "
                    f"(Reproducibility Validation: FAILED - {result.message}{hint})"
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
        _log.success(f"Saved: {format_saved_target(image_path, yaml_path)}")
    return image_path, yaml_path, None


__all__ = [
    "IMAGE_EXTENSIONS",
    "YAML_EXTENSIONS",
    "resolve_save_paths",
    "get_save_dpi",
    "get_save_transparency",
    "save_figure",
]
