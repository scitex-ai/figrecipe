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


#: Sequence types that are safe to materialise at record time because reading
#: them does not CONSUME them — iterate twice and you get the same values. They
#: are not list/tuple, so they miss every array branch below and would otherwise
#: reach the ``str(value)`` fallback and be recorded as text.
RE_ITERABLE_SEQUENCES = (range, type({}.keys()), type({}.values()))


class UnrecordableArgumentError(TypeError):
    """An argument cannot be recorded faithfully, and guessing would be worse.

    Raised at RECORD time — the only moment the caller can still fix it — rather
    than letting the value reach the recipe as text that no replay can undo.
    """


def _refuse_one_shot_iterator(name: str, value: Any) -> None:
    """Refuse a one-shot iterator instead of silently recording its repr.

    A generator / ``map`` / ``filter`` / ``zip`` cannot be recorded faithfully,
    and neither available option is acceptable silently:

    - materialising it here would CONSUME it, so the caller's own plot call
      would receive an exhausted iterator and draw nothing. The recipe would be
      right and the figure empty — we would have broken the picture to fix its
      description.
    - recording ``str(value)`` stores ``<generator object ...>``, which no
      replay can turn back into data. The figure is drawn but not reproducible,
      which is the exact failure figrecipe exists to prevent.

    So we stop and say what to do about it. ``list(...)`` at the call site costs
    the caller one word and makes the argument recordable and re-iterable.
    """
    if isinstance(value, (str, bytes, bytearray)):
        return
    if hasattr(value, "__len__"):
        return
    if not hasattr(value, "__iter__") or not hasattr(value, "__next__"):
        return
    raise UnrecordableArgumentError(
        f"figrecipe cannot record argument {name!r}: it is a one-shot iterator "
        f"({type(value).__name__}), which can be read only once. Recording it "
        f"would either consume the data before your plot draws it, or store an "
        f"unusable placeholder that replay cannot turn back into numbers. "
        f"Wrap it at the call site — e.g. list({name}) — so the values can be "
        f"both plotted and recorded."
    )


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

    if isinstance(value, RE_ITERABLE_SEQUENCES):
        # `range` (and friends) reach here as themselves, match none of the
        # branches above, and would fall to _process_scalar's str() — recorded
        # as the TEXT "range(0, 10)". Replay then hands matplotlib a string
        # where a format spec is legal, so `ax.plot(range(10), ys)` cannot be
        # saved at all. These types are RE-iterable, so materialising them is
        # free and invisible to the caller; re-dispatch so they take the same
        # proven path as the equivalent list.
        return _process_single_arg(
            name,
            list(value),
            should_store_inline,
            to_serializable,
            is_serializable_func,
        )

    _refuse_one_shot_iterator(name, value)

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
    """Process scalar or other value."""
    # numpy scalars (np.int64, np.float64, np.bool_, …) are not natively
    # serializable. np.float64 happens to subclass Python float so it slips
    # through, but np.int64 does NOT subclass int -> it falls to the str(value)
    # branch and serializes as e.g. '0'. A string coordinate turns the axis into
    # a category axis and breaks reproduce/compose (ConversionError: Failed to
    # convert value(s) to axis units: '0'). Coerce any numpy scalar to its native
    # Python type so coordinates round-trip as numbers.
    if isinstance(value, np.generic):
        value = value.item()
    try:
        return {
            "name": name,
            "data": value if is_serializable_func(value) else str(value),
        }
    except (TypeError, ValueError):
        return {"name": name, "data": str(value)}


__all__ = ["RE_ITERABLE_SEQUENCES", "UnrecordableArgumentError", "process_args"]

# EOF
