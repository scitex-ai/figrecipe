#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data extraction helpers for the public API."""

from typing import Any, Dict, Set

import numpy as np

# Decoration functions to skip when extracting data
DECORATION_FUNCS: Set[str] = {
    "set_xlabel",
    "set_ylabel",
    "set_title",
    "set_xlim",
    "set_ylim",
    "legend",
    "grid",
    "axhline",
    "axvline",
    "text",
    "annotate",
}


def to_array(data: Any) -> np.ndarray:
    """Convert data to numpy array, handling YAML types.

    Parameters
    ----------
    data : any
        Data to convert.

    Returns
    -------
    np.ndarray
        Converted numpy array.
    """
    # Handle dict with 'data' key (serialized array format)
    if isinstance(data, dict) or (hasattr(data, "keys") and "data" in data):
        return np.array(data["data"])
    if hasattr(data, "tolist"):  # Already array-like
        return np.array(data)
    return np.array(
        list(data) if hasattr(data, "__iter__") and not isinstance(data, str) else data
    )


def extract_call_data(call) -> Dict[str, Any]:
    """Extract data arrays from a single call record.

    Parameters
    ----------
    call : CallRecord
        The call to extract data from.

    Returns
    -------
    dict
        Dictionary with extracted data arrays.
    """
    call_data = {}

    # Extract positional arguments based on function type
    if call.function in ("plot", "scatter", "fill_between"):
        if len(call.args) >= 1:
            call_data["x"] = to_array(call.args[0])
        if len(call.args) >= 2:
            call_data["y"] = to_array(call.args[1])

    elif call.function == "bar":
        if len(call.args) >= 1:
            call_data["x"] = to_array(call.args[0])
        if len(call.args) >= 2:
            call_data["height"] = to_array(call.args[1])

    elif call.function == "hist":
        if len(call.args) >= 1:
            call_data["x"] = to_array(call.args[0])

    elif call.function == "errorbar":
        if len(call.args) >= 1:
            call_data["x"] = to_array(call.args[0])
        if len(call.args) >= 2:
            call_data["y"] = to_array(call.args[1])

    # Extract relevant kwargs
    for key in ("c", "s", "yerr", "xerr", "weights", "bins"):
        if key in call.kwargs:
            val = call.kwargs[key]
            if (
                isinstance(val, (list, tuple))
                or hasattr(val, "__iter__")
                and not isinstance(val, str)
            ):
                call_data[key] = to_array(val)
            else:
                call_data[key] = val

    return call_data


def extract_record_data(record) -> Dict[str, Dict[str, Any]]:
    """Extract existing function-specific fields without loading a recipe."""
    result = {}

    for ax_key, ax_record in record.axes.items():
        for call in ax_record.calls:
            if call.function in DECORATION_FUNCS:
                continue
            call_data = extract_call_data(call)
            if call_data:
                result[call.id] = call_data

    return result


def to_json_serializable(obj):
    """Convert numpy arrays and other non-serializable objects to JSON-safe types."""
    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    # Handle pandas Series
    elif hasattr(obj, "values") and hasattr(obj, "tolist"):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    return obj


def csv_bytes_from_record(record):
    """Keep the existing combined CSV projection of live recorded calls."""
    import csv
    import io

    all_data = {}
    decoration_funcs = {
        "set_xlabel",
        "set_ylabel",
        "set_title",
        "set_xlim",
        "set_ylim",
        "legend",
        "grid",
        "axhline",
        "axvline",
        "text",
        "annotate",
    }

    for ax_key, ax_record in record.axes.items():
        for call in getattr(ax_record, "calls", []):
            if getattr(call, "function", "") in decoration_funcs:
                continue

            call_id = (
                getattr(call, "id", None)
                or f"{ax_key}_{getattr(call, 'function', '')}_{id(call)}"
            )
            call_data = {}

            def _extract(val):
                if isinstance(val, dict) and "data" in val:
                    return val["data"]
                if isinstance(val, list):
                    return val
                return None

            args = to_json_serializable(getattr(call, "args", []))
            kwargs = to_json_serializable(getattr(call, "kwargs", {}))

            if args:
                if len(args) >= 2:
                    x = _extract(args[0])
                    y = _extract(args[1])
                    if x:
                        call_data["x"] = x
                    if y:
                        call_data["y"] = y
                elif len(args) == 1:
                    y = _extract(args[0])
                    if y:
                        call_data["y"] = y
                        call_data["x"] = list(range(len(y)))

            for key in ["x", "y", "height", "width", "c", "s"]:
                if key in kwargs:
                    val = _extract(kwargs[key])
                    if val:
                        call_data[key] = val

            if call_data:
                all_data[call_id] = call_data

    if not all_data:
        return None

    output = io.StringIO()
    max_len = max(max(len(v) for v in data.values()) for data in all_data.values())
    headers = [
        f"{cid}_{key}" for cid, data in all_data.items() for key in sorted(data.keys())
    ]
    writer = csv.writer(output)
    writer.writerow(headers)

    for i in range(max_len):
        row = []
        for cid, data in all_data.items():
            for key in sorted(data.keys()):
                vals = data[key]
                row.append(vals[i] if i < len(vals) else "")
        writer.writerow(row)

    csv_bytes = output.getvalue().encode("utf-8")
    return csv_bytes


def table_from_record(record):
    """Keep the existing live-record x/y column and row projection."""
    columns = []
    data_rows = []

    def _values(value):
        """Reduce a recorded plot argument to a JSON-safe list.

        A recorded arg is not the bare array: it is a mapping. Two shapes
        occur, depending on whether the figure is live (in memory) or was
        `reproduce`d from a recipe:
          - inline / reproduced-CSV: ``{"name", "data": <list>, "dtype"}``
          - file-backed live:        ``{"name", "data": "__FILE__", "dtype",
            "_array": <ndarray>}``  (the values sit in ``_array`` until saved)
        Passing the whole mapping to `to_json_serializable` returns the mapping
        itself, so the caller's `isinstance(list)` check silently fails and the
        row is never built — columns registered, data empty. Pull the payload:
        ``_array`` when present (the live case), else ``data``; skip the
        ``"__FILE__"`` sentinel, which carries no values of its own.
        """
        if value is None:
            return None
        if isinstance(value, dict):
            payload = value.get("_array")
            if payload is None:
                payload = value.get("data")
            if payload is None:
                return None
            # The "__FILE__" sentinel is a string and carries no values of its
            # own (the real data lives in _array, handled above); compare it
            # as a string only so an ndarray payload never hits `==`.
            if isinstance(payload, str) and payload == "__FILE__":
                return None
            value = payload
        return to_json_serializable(value)

    for ax_key, ax_record in record.axes.items():
        for call in getattr(ax_record, "calls", []):
            kwargs = getattr(call, "kwargs", {})
            args = getattr(call, "args", [])
            func = getattr(call, "function", "")

            x_data = kwargs.get("x") or (args[0] if len(args) > 0 else None)
            y_data = kwargs.get("y") or (args[1] if len(args) > 1 else None)

            if x_data is not None and y_data is not None:
                call_id = (
                    getattr(call, "call_id", None) or getattr(call, "id", None) or func
                )
                x_col = f"{call_id}_x"
                y_col = f"{call_id}_y"
                if x_col not in columns:
                    columns.extend([x_col, y_col])
                x_list = _values(x_data)
                y_list = _values(y_data)
                if isinstance(x_list, list) and isinstance(y_list, list):
                    for i, (xv, yv) in enumerate(zip(x_list, y_list)):
                        while len(data_rows) <= i:
                            data_rows.append({})
                        data_rows[i][x_col] = xv
                        data_rows[i][y_col] = yv

    rows = [[row.get(col) for col in columns] for row in data_rows]
    return columns, rows


def _dtype(values):
    present = [v for v in values if v is not None and v != ""]
    numeric = all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in present
    )
    return "numeric" if numeric else "string"


def table_columns(names, rows):
    """Keep existing named columns and numeric/string inference."""
    columns = [
        {"name": name, "dtype": _dtype([row[i] for row in rows if i < len(row)])}
        for i, name in enumerate(names)
    ]
    return columns


__all__ = [
    "DECORATION_FUNCS",
    "to_array",
    "extract_call_data",
]

# EOF
