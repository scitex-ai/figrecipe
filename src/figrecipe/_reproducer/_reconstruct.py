#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Value reconstruction utilities for recipe reproduction.

These functions handle converting serialized recipe data back into
Python objects (numpy arrays, lists, etc.) that matplotlib can use.
"""

from typing import Any, Dict, Optional

import numpy as np


def reconstruct_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct kwargs, converting 2D lists back to numpy arrays.

    Parameters
    ----------
    kwargs : dict
        Raw kwargs from call record.

    Returns
    -------
    dict
        Kwargs with arrays properly reconstructed.
    """
    result = {}
    for key, value in kwargs.items():
        # Handle 'colors' parameter specially - must be a list for pie/bar/etc.
        # A single color string like 'red' would be interpreted as ['r','e','d']
        if key == "colors" and isinstance(value, str):
            result[key] = [value]
        elif isinstance(value, list) and len(value) > 0:
            # Check if it's a 2D list (list of lists) - should be numpy array.
            # Only promote to ndarray when EVERY element is a list and
            # np.array succeeds on them; heterogeneous sequences (e.g. a
            # mix of RGBA tuples and 'none' strings coming from per-bar
            # color lists) must stay as plain Python lists so matplotlib
            # can interpret each entry on its own.
            if all(isinstance(v, list) for v in value):
                try:
                    result[key] = np.array(value)
                except (ValueError, TypeError):
                    result[key] = value
            else:
                result[key] = value
        else:
            result[key] = value
    return result


def coerce_sequence_arg(value: Any) -> Any:
    """Coerce a plain Python sequence to a numpy array for replay.

    Used by the inset/embed replay path. Sub-panel array args are inlined into
    the host YAML (the data-file loader does not descend into subpanels), so
    they round-trip as ruamel ``CommentedSeq`` lists rather than numpy arrays.
    Plotters like ``streamplot``/``contour``/``imshow`` call ``.shape`` on their
    inputs and raise on a raw list; promoting such sequences to ``np.asarray``
    makes any array-arg plotter work through nesting.

    Only homogeneous *numeric* sequences are promoted: if ``np.asarray`` would
    yield an object dtype (e.g. a per-element color list mixing tuples and
    ``'none'``, or inhomogeneous boxplot groups), the original sequence is
    returned unchanged so matplotlib can interpret each entry on its own --
    mirroring the defensive promotion in ``reconstruct_kwargs``/``reconstruct_value``.
    """
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, (list, tuple)) and len(value) > 0:
        try:
            arr = np.asarray(value)
        except (TypeError, ValueError):
            return value
        if arr.dtype != object:
            return arr
    return value


def reconstruct_value(
    arg_data: Dict[str, Any], result_cache: Optional[Dict[str, Any]] = None
) -> Any:
    """Reconstruct a value from serialized arg data.

    Parameters
    ----------
    arg_data : dict
        Serialized argument data.
    result_cache : dict, optional
        Cache mapping call_id -> result for resolving references.

    Returns
    -------
    Any
        Reconstructed value.
    """
    if result_cache is None:
        result_cache = {}

    # Check if we have a pre-loaded array (from YAML loading)
    if "_loaded_array" in arg_data:
        return arg_data["_loaded_array"]

    # Check if we have a raw array (direct from recording, not yet serialized)
    # This handles the __FILE__ placeholder case when reproducing from record
    if "_array" in arg_data:
        return arg_data["_array"]

    data = arg_data.get("data")

    # Check if it's a reference to another call's result (e.g., ContourSet for clabel)
    if isinstance(data, dict) and "__ref__" in data:
        ref_id = data["__ref__"]
        if ref_id in result_cache:
            return result_cache[ref_id]
        else:
            import warnings

            warnings.warn(f"Could not resolve reference to {ref_id}")
            return None

    # Check if it's a list of arrays (e.g., boxplot, violinplot)
    if arg_data.get("_is_array_list") and isinstance(data, list):
        dtype = arg_data.get("dtype")
        # Convert each inner list to numpy array
        return [
            np.array(arr_data, dtype=dtype if isinstance(dtype, str) else None)
            for arr_data in data
        ]

    # If data is a list, convert to numpy array
    if isinstance(data, list):
        dtype = arg_data.get("dtype")
        try:
            return np.array(data, dtype=dtype if dtype else None)
        except (TypeError, ValueError):
            # Handle inhomogeneous arrays (e.g., boxplot data with different group sizes)
            # Return as list for methods that accept list input
            return data

    return data


# EOF
