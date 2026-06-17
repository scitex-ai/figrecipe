#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities for recorder argument processing."""

from typing import Any, Dict, List

import numpy as np


def process_args(
    args: tuple,
    method_name: str,
    get_arg_names_func,
    is_serializable_func,
) -> List[Dict[str, Any]]:
    """Process positional arguments for storage.

    Parameters
    ----------
    args : tuple
        Raw positional arguments.
    method_name : str
        Name of the method.
    get_arg_names_func : callable
        Function to get argument names.
    is_serializable_func : callable
        Function to check serializability.

    Returns
    -------
    list
        Processed args with name and data.
    """
    from .._utils._numpy_io import should_store_inline, to_serializable

    processed = []
    arg_names = get_arg_names_func(method_name, len(args))

    for name, value in zip(arg_names, args):
        processed_arg = _process_single_arg(
            name, value, should_store_inline, to_serializable, is_serializable_func
        )
        processed.append(processed_arg)

    return processed


def _process_single_arg(
    name: str,
    value: Any,
    should_store_inline,
    to_serializable,
    is_serializable_func,
) -> Dict[str, Any]:
    """Process a single argument value."""
    # Handle result references (e.g., ContourSet for clabel)
    if isinstance(value, dict) and "__ref__" in value:
        return {"name": name, "data": {"__ref__": value["__ref__"]}}

    if isinstance(value, np.ndarray):
        return _process_ndarray(name, value, should_store_inline, to_serializable)

    if hasattr(value, "values"):  # pandas
        arr = np.asarray(value)
        return _process_ndarray(name, arr, should_store_inline, to_serializable)

    if (
        isinstance(value, (list, tuple))
        and len(value) > 0
        and isinstance(value[0], np.ndarray)
    ):
        # List of arrays (e.g., boxplot, violinplot data)
        return _process_array_list(name, value, to_serializable)

    if isinstance(value, (list, tuple)) and len(value) > 0:
        # Check if it's a list of numbers that can be converted to array
        try:
            arr = np.asarray(value)
            if arr.dtype.kind in ("i", "f", "u", "b"):  # numeric types
                return _process_ndarray(name, arr, should_store_inline, to_serializable)
        except (ValueError, TypeError):
            pass

    # Scalar or other serializable value
    return _process_scalar(name, value, is_serializable_func)


def _process_ndarray(
    name: str, value: np.ndarray, should_store_inline, to_serializable
) -> Dict[str, Any]:
    """Process numpy array argument."""
    if should_store_inline(value):
        return {
            "name": name,
            "data": to_serializable(value),
            "dtype": str(value.dtype),
        }
    else:
        # Mark for file storage (will be handled by serializer)
        return {
            "name": name,
            "data": "__FILE__",
            "dtype": str(value.dtype),
            "_array": value,  # Temporary, removed during serialization
        }


def _process_array_list(
    name: str, value: list, to_serializable, should_store_inline=None
) -> Dict[str, Any]:
    """Process list of arrays argument.

    For list of arrays (boxplot, violinplot data), we mark them for file
    storage using _array key, same as single arrays.
    """
    # Convert list of arrays to single 2D array if possible (same length arrays)
    # Otherwise concatenate with padding or store as jagged array
    try:
        lengths = [len(arr) for arr in value]
        if len(set(lengths)) == 1:
            # All same length - can stack
            stacked = np.column_stack(value)
        else:
            # Jagged array - pad to max length
            max_len = max(lengths)
            padded = []
            for arr in value:
                if len(arr) < max_len:
                    pad_arr = np.full(max_len, np.nan)
                    pad_arr[: len(arr)] = arr
                    padded.append(pad_arr)
                else:
                    padded.append(arr)
            stacked = np.column_stack(padded)
    except Exception:
        # Fallback to original inline storage
        arrays_data = [to_serializable(arr) for arr in value]
        dtypes = [str(arr.dtype) for arr in value]
        return {
            "name": name,
            "data": arrays_data,
            "dtype": (dtypes[0] if len(set(dtypes)) == 1 else dtypes),
            "_is_array_list": True,
        }

    dtypes = [str(arr.dtype) for arr in value]
    dtype_str = dtypes[0] if len(set(dtypes)) == 1 else dtypes

    # Mark for file storage (same pattern as single arrays)
    return {
        "name": name,
        "data": "__FILE__",
        "dtype": dtype_str,
        "_array": stacked,  # Will be saved to CSV by serializer
        "_is_array_list": True,
        "_n_arrays": len(value),
        "_array_lengths": lengths,
    }


def _process_scalar(name: str, value: Any, is_serializable_func) -> Dict[str, Any]:
    """Process scalar or other value.

    NumPy scalar types are coerced to their Python equivalents first. This
    matters because ``np.floating`` subclasses ``float`` (so it survives the
    serializable check below) but ``np.integer`` does NOT subclass ``int`` --
    without this an ``np.int64`` (e.g. an ``np.arange`` index passed to
    ``ax.text``/``ax.bar``) would fall through to ``str(value)`` and serialize
    as e.g. ``'0'``. On replay that string then hits a category-unit converter
    and raises ``ConversionError: Failed to convert value(s) to axis units``.
    ``.item()`` turns any numpy scalar into the matching native Python number.
    """
    if isinstance(value, np.generic):
        value = value.item()
    try:
        return {
            "name": name,
            "data": value if is_serializable_func(value) else str(value),
        }
    except (TypeError, ValueError):
        return {"name": name, "data": str(value)}


__all__ = ["process_args"]

# EOF
