#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public API wrapper functions for figrecipe.

These functions provide the main user-facing API with full docstrings.
They are re-exported from figrecipe.__init__.py.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .._recorder import FigureRecord
from .._reproducer import get_recipe_info
from .._reproducer import reproduce as _reproduce_core
from .._serializer import load_recipe
from .._utils._numpy_io import CsvFormat, DataFormat
from .._validator import ValidationResult
from .._wrappers import RecordingAxes, RecordingFigure


def subplots(
    nrows: int = 1,
    ncols: int = 1,
    axes_width_mm: Optional[float] = None,
    axes_height_mm: Optional[float] = None,
    margin_left_mm: Optional[float] = None,
    margin_right_mm: Optional[float] = None,
    margin_bottom_mm: Optional[float] = None,
    margin_top_mm: Optional[float] = None,
    space_w_mm: Optional[float] = None,
    space_h_mm: Optional[float] = None,
    style: Optional[Dict[str, Any]] = None,
    apply_style_mm: bool = True,
    panel_labels: Optional[bool] = None,
    **kwargs,
) -> Tuple[RecordingFigure, Union[RecordingAxes, NDArray]]:
    """Create a figure with recording-enabled axes.

    This is a drop-in replacement for plt.subplots() that wraps the
    returned figure and axes with recording capabilities.

    Supports mm-based layout control for publication-quality figures.

    Parameters
    ----------
    nrows, ncols : int
        Number of rows and columns of subplots.
    axes_width_mm, axes_height_mm : float, optional
        Axes dimensions in mm.
    margin_left_mm, margin_right_mm : float, optional
        Left/right margins in mm.
    margin_bottom_mm, margin_top_mm : float, optional
        Bottom/top margins in mm.
    space_w_mm, space_h_mm : float, optional
        Horizontal/vertical spacing between axes in mm.
    style : dict, optional
        Style configuration dictionary.
    apply_style_mm : bool
        If True (default), apply loaded style to axes.
    panel_labels : bool or None
        If True, add panel labels (A, B, C, ...).
    **kwargs
        Additional arguments passed to plt.subplots().

    Returns
    -------
    fig : RecordingFigure
        Wrapped figure object.
    axes : RecordingAxes or ndarray
        Wrapped axes.
    """
    from ._subplots import create_subplots

    return create_subplots(
        nrows=nrows,
        ncols=ncols,
        axes_width_mm=axes_width_mm,
        axes_height_mm=axes_height_mm,
        margin_left_mm=margin_left_mm,
        margin_right_mm=margin_right_mm,
        margin_bottom_mm=margin_bottom_mm,
        margin_top_mm=margin_top_mm,
        space_w_mm=space_w_mm,
        space_h_mm=space_h_mm,
        style=style,
        apply_style_mm=apply_style_mm,
        panel_labels=panel_labels,
        **kwargs,
    )


def save(
    fig: Union[RecordingFigure, Figure],
    path: Union[str, Path],
    save_recipe: bool = True,
    include_data: bool = True,
    data_format: DataFormat = "csv",
    csv_format: CsvFormat = "separate",
    validate: bool = True,
    validate_mse_threshold: float = 100.0,
    validate_error_level: str = "error",
    verbose: bool = True,
    dpi: Optional[int] = None,
    image_format: Optional[str] = None,
    facecolor: Optional[str] = None,
    save_hitmap: bool = False,
    save_editable: bool = False,
):
    """Save a figure as image and recipe. Unified API with fig.savefig().

    Parameters
    ----------
    fig : RecordingFigure or Figure
        The figure to save.
    path : str or Path
        Output path (.png, .pdf, .svg, .yaml, etc.)
    save_recipe : bool
        If True (default), save YAML recipe alongside the image.
    include_data : bool
        If True (default), save large arrays to separate files.
    data_format : str
        Format for data files: 'csv', 'npz', or 'inline'.
    csv_format : str
        CSV structure: 'separate' (default) or 'single' (scitex-compatible).
    validate : bool
        If True (default), validate reproducibility after saving.
    validate_mse_threshold : float
        Maximum acceptable MSE for validation (default: 100).
    validate_error_level : str
        How to handle failures: 'error', 'warning', or 'debug'.
    verbose : bool
        If True (default), print save status.
    dpi : int, optional
        DPI for image output.
    image_format : str, optional
        Image format when path is YAML.
    facecolor : str, optional
        Background color. When opaque, patches are made visible.
    save_hitmap : bool
        If True (default), save hitmap image for GUI editor element selection.
    save_editable : bool
        If True, write the editable-figure JSON (schema
        ``scitex.plt.figure.editable``) to ``<stem>.json`` next to the image.
        Default False — opt in for the GUI / web editor.

    Returns
    -------
    tuple
        If save_recipe=True: (image_path, yaml_path, ValidationResult or None)
        If save_recipe=False: (image_path, None, None)
    """
    from ._save import save_figure

    result = save_figure(
        fig=fig,
        path=path,
        save_recipe=save_recipe,
        include_data=include_data,
        data_format=data_format,
        csv_format=csv_format,
        validate=validate,
        validate_mse_threshold=validate_mse_threshold,
        validate_error_level=validate_error_level,
        verbose=verbose,
        dpi=dpi,
        image_format=image_format,
        facecolor=facecolor,
        save_hitmap=save_hitmap,
    )

    # Editable-figure JSON sidecar (schema scitex.plt.figure.editable).
    # Written next to the saved image; opt-in (default False).
    if save_editable:
        from .._editable import save_editable as _save_editable

        image_path = result[0] if isinstance(result, tuple) else result
        _save_editable(fig, image_path, verbose=verbose)

    return result


def reproduce(
    path: Union[str, Path],
    calls: Optional[List[str]] = None,
    skip_decorations: bool = False,
    apply_style: bool = True,
) -> Tuple[Figure, Union[Axes, List[Axes]]]:
    """Reproduce a figure from a recipe file or bundle.

    Parameters
    ----------
    path : str or Path
        Path to recipe. Supports multiple formats:
        - .yaml/.yml file: Direct recipe file
        - .png/.jpg/etc: Image with associated .yaml
        - Directory: Bundle containing recipe.yaml
        - .zip: ZIP bundle (both old recipe.yaml format and new spec.json format)
    calls : list of str, optional
        If provided, only reproduce these specific call IDs.
    skip_decorations : bool
        If True, skip decoration calls.
    apply_style : bool
        If True (default), apply saved style.

    Returns
    -------
    fig : matplotlib.figure.Figure
        Reproduced figure.
    axes : Axes or list of Axes
        Reproduced axes.
    """
    import zipfile

    path = Path(path)

    # Check if this is a new-format bundle (ZIP with spec.json)
    if path.suffix.lower() == ".zip" and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()
            # Check for spec.json (new bundle format)
            has_spec = any(n.endswith("spec.json") for n in namelist)
            has_recipe = any(
                n.endswith("recipe.yaml") or n.endswith("recipe.yml") for n in namelist
            )

            if has_spec and not has_recipe:
                # Use new bundle reproduction
                from .._bundle._load import reproduce_bundle

                return reproduce_bundle(path, apply_style=apply_style)

    # Use old recipe-based reproduction
    return _reproduce_core(path, calls=calls, skip_decorations=skip_decorations)


def info(path: Union[str, Path]) -> Dict[str, Any]:
    """Get information about a recipe without reproducing."""
    return get_recipe_info(path)


def load_record(path: Union[str, Path]) -> FigureRecord:
    """Load a recipe as a FigureRecord object (advanced use)."""
    return load_recipe(path)


def extract_data(path: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
    """Extract data arrays from a saved recipe.

    Returns
    -------
    dict
        Nested dictionary: {call_id: {'x': array, 'y': array, ...}}
    """
    from ._extract import DECORATION_FUNCS, extract_call_data

    record = load_recipe(path)
    result = {}

    for ax_key, ax_record in record.axes.items():
        for call in ax_record.calls:
            if call.function in DECORATION_FUNCS:
                continue
            call_data = extract_call_data(call)
            if call_data:
                result[call.id] = call_data

    return result


def validate(
    path: Union[str, Path],
    mse_threshold: float = 100.0,
) -> ValidationResult:
    """Validate that a saved recipe can reproduce its original figure.

    Parameters
    ----------
    path : str or Path
        Path to .yaml recipe file.
    mse_threshold : float
        Maximum acceptable MSE for validation to pass (default: 100).

    Returns
    -------
    ValidationResult
        Detailed comparison results.
    """
    from ._validate import validate_recipe as _validate

    return _validate(path, mse_threshold)


# Backward compatibility alias
validate_recipe = validate


def crop(
    input_path,
    output_path=None,
    margin_mm=1.0,
    margin_px=None,
    overwrite=False,
    verbose=False,
    return_offset=False,
):
    """Crop a figure image to its content area with a specified margin.

    Parameters
    ----------
    input_path : str or Path
        Path to the input image.
    output_path : str or Path, optional
        Path to save the cropped image.
    margin_mm : float, optional
        Margin in millimeters (default: 1.0mm).
    margin_px : int, optional
        Margin in pixels (overrides margin_mm if provided).
    overwrite : bool, optional
        Whether to overwrite the input file (default: False)
    verbose : bool, optional
        Whether to print detailed information (default: False)
    return_offset : bool, optional
        If True, also return crop offset info dict (default: False)

    Returns
    -------
    Path or tuple
        Path to the saved cropped image. If return_offset=True,
        returns (path, offset_dict).
    """
    from .._utils._crop import crop as _crop

    return _crop(
        input_path,
        output_path,
        margin_mm=margin_mm,
        margin_px=margin_px,
        overwrite=overwrite,
        verbose=verbose,
        return_offset=return_offset,
    )


def gui(
    source=None,
    style=None,
    port: int = 5050,
    host: str = "127.0.0.1",
    open_browser: bool = True,
    hot_reload: bool = False,
    working_dir=None,
    desktop: bool = False,
):
    """Launch interactive GUI editor for figure styling.

    Parameters
    ----------
    source : RecordingFigure, str, Path, or None
        Either a live RecordingFigure object, path to a .yaml recipe file,
        or None to create a new blank figure.
    style : str or dict, optional
        Style preset name or style dict.
    port : int, optional
        Django server port (default: 5050).
    host : str, optional
        Host to bind server (default: "127.0.0.1", use "0.0.0.0" for Docker).
    open_browser : bool, optional
        Whether to open browser automatically (default: True).
    hot_reload : bool, optional
        Enable hot reload (default: False).
    working_dir : str or Path, optional
        Working directory for file browser (default: directory containing source).
    desktop : bool, optional
        Launch as native desktop window using pywebview (default: False).
        Requires: pip install figrecipe[desktop]

    Returns
    -------
    dict
        Final style overrides after editing session.
    """
    from .._editor import gui as _gui

    return _gui(
        source,
        style=style,
        port=port,
        host=host,
        open_browser=open_browser,
        hot_reload=hot_reload,
        working_dir=working_dir,
        desktop=desktop,
    )


# Alias for intuitive save/load symmetry
load = reproduce

__all__ = [
    "subplots",
    "save",
    "reproduce",
    "load",
    "info",
    "load_record",
    "extract_data",
    "validate",
    "validate_recipe",  # backward compat alias
    "crop",
    "gui",
]
