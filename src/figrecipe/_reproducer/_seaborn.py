#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seaborn plot replay for figure reproduction."""

from typing import Any

from matplotlib.axes import Axes

from .._recorder import CallRecord
from ._warnings import ReplayFailureWarning


def replay_seaborn_call(ax: Axes, call: CallRecord) -> Any:
    """Replay a seaborn call on an axes.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes.
    call : CallRecord
        The seaborn call to replay.

    Returns
    -------
    Any
        Result of the seaborn call.
    """
    try:
        import pandas as pd
        import seaborn as sns
    except ImportError:
        import warnings

        warnings.warn("seaborn/pandas required to replay seaborn calls")
        return None

    # Get the seaborn function name (remove "sns." prefix)
    func_name = call.function[4:]  # Remove "sns."
    func = getattr(sns, func_name, None)

    if func is None:
        import warnings

        warnings.warn(f"Seaborn function {func_name} not found")
        return None

    # Reconstruct data from args
    # Args contain column data with "param" field indicating the parameter name
    data_dict = {}
    param_mapping = {}  # Maps param name to column name

    from ._reconstruct import reconstruct_value

    for arg_data in call.args:
        param = arg_data.get("param")
        name = arg_data.get("name")
        value = reconstruct_value(arg_data)

        if param is not None:
            # This is a DataFrame column
            col_name = name if name else param
            data_dict[col_name] = value
            param_mapping[param] = col_name

    # Build kwargs
    kwargs = call.kwargs.copy()

    # Remove internal keys
    internal_keys = [k for k in kwargs.keys() if k.startswith("_")]
    for key in internal_keys:
        kwargs.pop(key, None)

    # If we have data columns, create a DataFrame
    if data_dict:
        df = pd.DataFrame(data_dict)
        kwargs["data"] = df

        # Update column name references in kwargs
        for param, col_name in param_mapping.items():
            if param in ["x", "y", "hue", "size", "style", "row", "col"]:
                kwargs[param] = col_name

    # Add the axes
    kwargs["ax"] = ax

    # Convert certain list parameters back to tuples (YAML serializes tuples as lists)
    # 'sizes' in seaborn expects a tuple (min, max) for range, not a list
    if "sizes" in kwargs and isinstance(kwargs["sizes"], list):
        kwargs["sizes"] = tuple(kwargs["sizes"])

    # Call the seaborn function
    try:
        return func(**kwargs)
    except Exception as e:
        import warnings

        warnings.warn(
            f"Failed to replay sns.{func_name}: {e}", ReplayFailureWarning
        )
        return None


__all__ = ["replay_seaborn_call"]
