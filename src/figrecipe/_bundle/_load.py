#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load and reproduce from bundle (ZIP format)."""

import json
import warnings
import zipfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import pandas as pd

from ._paths import DATA_FILENAME, SPEC_FILENAME, STYLE_FILENAME
from .._reproducer._warnings import ReplayFailureWarning


def load_bundle(
    path: Union[str, Path],
) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[pd.DataFrame]]:
    """Load bundle components from ZIP file.

    Parameters
    ----------
    path : str or Path
        Path to bundle ZIP file.

    Returns
    -------
    tuple
        (spec, style, data) where data is DataFrame or None.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Bundle not found: {path}")

    # Handle both ZIP and directory formats
    if path.is_dir():
        return _load_from_directory(path)
    else:
        return _load_from_zip(path)


def _load_from_zip(path: Path) -> Tuple[Dict, Dict, Optional[pd.DataFrame]]:
    """Load bundle from ZIP file.

    Supports both formats:
    - New format: files inside root directory (e.g., figure/spec.json)
    - Legacy format: files at root (e.g., spec.json)
    """
    with zipfile.ZipFile(path, "r") as zf:
        # Determine prefix (new format uses zip stem as root directory)
        namelist = zf.namelist()
        root_dir = path.stem

        # Check if files are in root directory (new format) or at root (legacy)
        if f"{root_dir}/{SPEC_FILENAME}" in namelist:
            prefix = f"{root_dir}/"
        elif SPEC_FILENAME in namelist:
            prefix = ""
        else:
            # Try to find spec.json in any subdirectory
            spec_files = [n for n in namelist if n.endswith(SPEC_FILENAME)]
            if spec_files:
                prefix = spec_files[0].replace(SPEC_FILENAME, "")
            else:
                raise FileNotFoundError(f"spec.json not found in bundle: {path}")

        # Load spec
        try:
            with zf.open(f"{prefix}{SPEC_FILENAME}") as f:
                spec = json.load(f)
        except KeyError:
            raise FileNotFoundError(f"spec.json not found in bundle: {path}")

        # Load style
        style = {}
        try:
            with zf.open(f"{prefix}{STYLE_FILENAME}") as f:
                style = json.load(f)
        except KeyError:
            pass  # style.json is optional

        # Load data
        data = None
        try:
            with zf.open(f"{prefix}{DATA_FILENAME}") as f:
                data = pd.read_csv(StringIO(f.read().decode("utf-8")))
        except KeyError:
            pass  # data.csv is optional

    return spec, style, data


def _load_from_directory(path: Path) -> Tuple[Dict, Dict, Optional[pd.DataFrame]]:
    """Load bundle from directory (legacy support)."""
    spec_path = path / SPEC_FILENAME
    if not spec_path.exists():
        raise FileNotFoundError(f"spec.json not found in bundle: {path}")

    with open(spec_path) as f:
        spec = json.load(f)

    style = {}
    style_path = path / STYLE_FILENAME
    if style_path.exists():
        with open(style_path) as f:
            style = json.load(f)

    data = None
    data_path = path / DATA_FILENAME
    if data_path.exists():
        data = pd.read_csv(data_path)

    return spec, style, data


def reproduce_bundle(
    path: Union[str, Path],
    apply_style: bool = True,
):
    """Reproduce figure from bundle.

    Parameters
    ----------
    path : str or Path
        Path to bundle (ZIP file or directory).
    apply_style : bool
        Whether to apply saved style (default: True).

    Returns
    -------
    tuple
        (fig, axes) reproduced from bundle.
    """
    spec, style, data = load_bundle(path)

    # Create figure
    from .. import subplots

    fig_spec = spec.get("figure", {})
    mm_layout = fig_spec.get("mm_layout")

    if mm_layout:
        # Use mm-based layout
        fig, axes = subplots(
            nrows=mm_layout.get("nrows", 1),
            ncols=mm_layout.get("ncols", 1),
            axes_width_mm=mm_layout.get("axes_width_mm"),
            axes_height_mm=mm_layout.get("axes_height_mm"),
            margin_left_mm=mm_layout.get("margin_left_mm"),
            margin_right_mm=mm_layout.get("margin_right_mm"),
            margin_bottom_mm=mm_layout.get("margin_bottom_mm"),
            margin_top_mm=mm_layout.get("margin_top_mm"),
            space_w_mm=mm_layout.get("space_w_mm"),
            space_h_mm=mm_layout.get("space_h_mm"),
        )
    else:
        # Use figsize
        figsize = None
        if fig_spec.get("width_inches") and fig_spec.get("height_inches"):
            figsize = (fig_spec["width_inches"], fig_spec["height_inches"])

        fig, axes = subplots(figsize=figsize)

    # Ensure axes is iterable
    if not hasattr(axes, "__iter__"):
        axes = [axes]

    # Replay traces
    _replay_traces(spec, style, data, axes, apply_style)

    return fig, axes


def _replay_traces(spec, style, data, axes, apply_style):
    """Replay traces from spec onto axes."""
    for ax_key, ax_spec in spec.get("axes", {}).items():
        # Find matching axes (simple mapping for now)
        ax = axes[0] if len(axes) == 1 else axes.flat[0]

        for trace in ax_spec.get("traces", []):
            func_name = trace["function"]
            func = getattr(ax, func_name, None)

            if func is None:
                warnings.warn(f"Unknown function: {func_name}")
                continue

            # Get data from DataFrame
            data_cols = trace.get("data_columns", {})
            args = []
            for arg_name, col_name in data_cols.items():
                if data is not None and col_name in data.columns:
                    arr = data[col_name].dropna().values
                    args.append(arr)

            # Get kwargs
            kwargs = trace.get("kwargs", {})

            # Apply style overrides
            if apply_style:
                trace_style = (
                    style.get("axes", {})
                    .get(ax_key, {})
                    .get("traces", {})
                    .get(trace["id"], {})
                )
                kwargs.update(trace_style)

            # Add ID
            kwargs["id"] = trace["id"]

            try:
                func(*args, **kwargs)
            except Exception as e:
                warnings.warn(
                    f"Failed to replay {func_name}: {e}", ReplayFailureWarning
                )

        # Replay decorations
        for dec in ax_spec.get("decorations", []):
            func_name = dec["function"]
            func = getattr(ax, func_name, None)

            if func is None:
                continue

            args = []
            for arg in dec.get("args", []):
                if "value" in arg:
                    args.append(arg["value"])

            kwargs = dec.get("kwargs", {})
            kwargs["id"] = dec["id"]

            try:
                func(*args, **kwargs)
            except Exception:
                pass
