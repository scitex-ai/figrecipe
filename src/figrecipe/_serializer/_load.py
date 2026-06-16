#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load-side serialization for recipe files (YAML + data files)."""

from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
from ruamel.yaml import YAML

from .._recorder import FigureRecord
from .._utils._numpy_io import (
    _sanitize_trace_id,
    load_array,
    load_single_csv,
)


def _convert_diagram_to_figure_recipe(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert standalone diagram YAML to figure recipe format.

    Standalone diagram recipes have ``type: diagram`` with the diagram
    specification under the ``diagram`` key.  This wraps them into the
    standard figure recipe structure so that the editor, composer, and
    reproducer can handle them uniformly.

    Parameters
    ----------
    data : dict
        Raw YAML data with ``type: diagram``.

    Returns
    -------
    dict
        Figure recipe data with embedded diagram call.
    """
    diagram_data = dict(data.get("diagram", {}))
    dpi = data.get("dpi", 200)

    # Compute figsize from diagram dimensions (mm -> inches)
    width_mm = diagram_data.get("width_mm", 200.0)
    height_mm = diagram_data.get("height_mm", 120.0)
    if "xlim" in diagram_data:
        xlim = diagram_data["xlim"]
        width_mm = (xlim[1] if isinstance(xlim, list) else xlim) - (
            xlim[0] if isinstance(xlim, list) else 0
        )
    if "ylim" in diagram_data:
        ylim = diagram_data["ylim"]
        height_mm = (ylim[1] if isinstance(ylim, list) else ylim) - (
            ylim[0] if isinstance(ylim, list) else 0
        )
    figsize = [width_mm / 25.4, height_mm / 25.4]

    return {
        "figrecipe": data.get("figrecipe", "1.0"),
        "id": data.get("id", "fig_diagram"),
        "created": data.get("created", ""),
        "matplotlib_version": "",
        "figure": {
            "figsize": figsize,
            "dpi": dpi,
        },
        "axes": {
            "ax_0_0": {
                "calls": [
                    {
                        "id": "diagram_0",
                        "function": "diagram",
                        "args": [],
                        "kwargs": {"diagram_data": diagram_data},
                        "timestamp": data.get("created", ""),
                    }
                ],
                "decorations": [],
            }
        },
    }


def load_recipe(path: Union[str, Path]) -> FigureRecord:
    """Load a figure record from YAML file.

    Handles both standard figure recipes and standalone diagram recipes
    (``type: diagram``).  Diagram recipes are converted to figure recipe
    format transparently so the editor, composer, and reproducer all
    work without special-casing.

    Parameters
    ----------
    path : str or Path
        Path to .yaml recipe file.

    Returns
    -------
    FigureRecord
        Loaded figure record.
    """
    path = Path(path)

    yaml = YAML()
    with open(path) as f:
        data = yaml.load(f)

    # Convert standalone diagram recipes to figure recipe format
    if data.get("type") == "diagram":
        data = _convert_diagram_to_figure_recipe(data)

    # Resolve data file references
    data = _resolve_data_references(data, path.parent)

    return FigureRecord.from_dict(data)


def _resolve_data_references(
    data: Dict[str, Any],
    base_dir: Path,
) -> Dict[str, Any]:
    """Resolve file references to actual array data.

    Parameters
    ----------
    data : dict
        Data dictionary with file references.
    base_dir : Path
        Base directory for resolving relative paths.

    Returns
    -------
    dict
        Data with arrays loaded.
    """
    # Check if this recipe uses single CSV format
    data_info = data.get("data", {})
    if isinstance(data_info, dict) and data_info.get("csv_format") == "single":
        return _resolve_single_csv_references(data, base_dir, data_info)

    # Original behavior: resolve individual file references
    for ax_key, ax_data in data.get("axes", {}).items():
        for call_list in [ax_data.get("calls", []), ax_data.get("decorations", [])]:
            for call in call_list:
                for arg in call.get("args", []):
                    data_ref = arg.get("data")

                    # Check if it's a file reference
                    if isinstance(data_ref, str) and (
                        data_ref.endswith(".npy")
                        or data_ref.endswith(".npz")
                        or data_ref.endswith(".csv")
                    ):
                        file_path = base_dir / data_ref
                        if file_path.exists():
                            # Get dtype from YAML to ensure proper type conversion
                            dtype = arg.get("dtype")
                            arr = load_array(file_path, dtype=dtype)

                            # Check if this was a list of arrays
                            if arg.get("_is_array_list"):
                                # Reconstruct list of arrays from 2D array
                                n_arrays = arg.get(
                                    "_n_arrays", arr.shape[1] if arr.ndim > 1 else 1
                                )
                                array_lengths = arg.get("_array_lengths")

                                arrays = []
                                for i in range(n_arrays):
                                    if arr.ndim > 1:
                                        col = arr[:, i]
                                    else:
                                        col = arr

                                    # Trim to original length (remove NaN padding)
                                    if array_lengths and i < len(array_lengths):
                                        col = col[: array_lengths[i]]
                                        col = col[~np.isnan(col)]
                                    arrays.append(col)

                                arg["data"] = [a.tolist() for a in arrays]
                                arg["_loaded_array"] = arrays
                            else:
                                arg["data"] = arr.tolist()
                                arg["_loaded_array"] = arr

                            # Store source file path for symlink support
                            arg["_source_file"] = str(file_path.resolve())
                        else:
                            # Fail loud: a referenced data file that does not
                            # exist (e.g. a broken/stale compose symlink) must
                            # NOT silently fall through and leave the path string
                            # as the arg -- that surfaces later as a cryptic
                            # "not a valid format string" deep in matplotlib.
                            raise FileNotFoundError(
                                f"recipe data file not found: {file_path} "
                                f"(referenced as '{data_ref}'). Fix the source "
                                f"data; do not reproduce from a broken recipe."
                            )

    return data


def _resolve_single_csv_references(
    data: Dict[str, Any],
    base_dir: Path,
    data_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Resolve references from single CSV format.

    Parameters
    ----------
    data : dict
        Data dictionary with file references.
    base_dir : Path
        Base directory for resolving relative paths.
    data_info : dict
        Data section from recipe with csv_path and csv_format.

    Returns
    -------
    dict
        Data with arrays loaded from single CSV.
    """
    csv_path = base_dir / data_info.get("csv_path", "")
    if not csv_path.exists():
        return data

    # Load all arrays from single CSV
    arrays_by_trace = load_single_csv(csv_path)

    # Map loaded arrays back to args
    for ax_key, ax_data in data.get("axes", {}).items():
        trace_data = arrays_by_trace.get(ax_key, {})

        for call_list in [ax_data.get("calls", []), ax_data.get("decorations", [])]:
            for call in call_list:
                call_id = call.get("id", "unknown")
                sanitized_id = _sanitize_trace_id(call_id)
                trace_arrays = trace_data.get(sanitized_id, {})

                for arg in call.get("args", []):
                    var_name = arg.get("name", "").lower()

                    if var_name in trace_arrays:
                        arr = trace_arrays[var_name]
                        dtype = arg.get("dtype")
                        if dtype is not None:
                            arr = arr.astype(dtype)
                        arg["data"] = arr.tolist()
                        arg["_loaded_array"] = arr

    return data


def recipe_to_dict(path: Union[str, Path]) -> Dict[str, Any]:
    """Load recipe as raw dictionary (for inspection).

    Parameters
    ----------
    path : str or Path
        Path to .yaml recipe file.

    Returns
    -------
    dict
        Raw recipe data.
    """
    path = Path(path)

    yaml = YAML()
    with open(path) as f:
        return dict(yaml.load(f))
