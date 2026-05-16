#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seaborn wrapper for figrecipe recording."""

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import numpy as np
import pandas as pd
from scitex_dev import try_import_optional

sns = try_import_optional("seaborn", extra="seaborn", pkg="figrecipe")
HAS_SEABORN = sns is not None

if TYPE_CHECKING:
    pass


# Seaborn axes-level plotting functions to wrap
SEABORN_PLOT_FUNCTIONS = {
    # Relational
    "scatterplot",
    "lineplot",
    # Distribution
    "histplot",
    "kdeplot",
    "ecdfplot",
    "rugplot",
    # Categorical
    "stripplot",
    "swarmplot",
    "boxplot",
    "violinplot",
    "boxenplot",
    "pointplot",
    "barplot",
    "countplot",
    # Regression
    "regplot",
    "residplot",
    # Matrix
    "heatmap",
    "clustermap",
}


def _check_seaborn():
    """Check if seaborn is available."""
    if not HAS_SEABORN:
        raise ImportError(
            "seaborn is required for this functionality. "
            "Install it with: pip install seaborn"
        )


def _extract_data_from_dataframe(
    data: Optional["pd.DataFrame"],
    x: Optional[str] = None,
    y: Optional[str] = None,
    hue: Optional[str] = None,
    size: Optional[str] = None,
    style: Optional[str] = None,
    row: Optional[str] = None,
    col: Optional[str] = None,
    weight: Optional[str] = None,
    weights: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract relevant columns from DataFrame for serialization.

    Parameters
    ----------
    data : DataFrame or None
        The data source.
    x, y, hue, size, style, row, col, weight, weights : str or None
        Column names to extract.

    Returns
    -------
    dict
        Extracted data with column arrays.
    """
    if data is None:
        return {}

    extracted = {}
    columns_to_extract = []

    # All column parameters
    param_values = [
        ("x", x),
        ("y", y),
        ("hue", hue),
        ("size", size),
        ("style", style),
        ("row", row),
        ("col", col),
        ("weight", weight),
        ("weights", weights),
    ]

    for param_name, col_name in param_values:
        if col_name is not None and isinstance(col_name, str):
            if col_name in data.columns:
                columns_to_extract.append((param_name, col_name))

    # Extract columns
    for param_name, col_name in columns_to_extract:
        arr = data[col_name].values
        extracted[f"_col_{param_name}"] = arr
        extracted[f"_colname_{param_name}"] = col_name

    return extracted


def _serialize_seaborn_args(
    func_name: str,
    args: tuple,
    kwargs: Dict[str, Any],
) -> tuple:
    """Serialize seaborn function arguments.

    Parameters
    ----------
    func_name : str
        Name of seaborn function.
    args : tuple
        Positional arguments.
    kwargs : dict
        Keyword arguments.

    Returns
    -------
    tuple
        (processed_args, processed_kwargs, data_arrays)
    """
    processed_kwargs = {}
    data_arrays = {}

    # Handle 'data' parameter (DataFrame)
    data = kwargs.get("data")
    if data is not None and hasattr(data, "columns"):
        # Extract column data
        extracted = _extract_data_from_dataframe(
            data,
            x=kwargs.get("x"),
            y=kwargs.get("y"),
            hue=kwargs.get("hue"),
            size=kwargs.get("size"),
            style=kwargs.get("style"),
            row=kwargs.get("row"),
            col=kwargs.get("col"),
            weight=kwargs.get("weight"),
            weights=kwargs.get("weights"),
        )
        data_arrays.update(extracted)

        # Store column names (not the DataFrame itself)
        processed_kwargs["_has_dataframe"] = True

    # Process other kwargs
    for key, value in kwargs.items():
        if key == "data":
            continue  # Handled above
        elif key == "ax":
            continue  # Will be handled separately
        elif isinstance(value, np.ndarray):
            data_arrays[f"_kwarg_{key}"] = value
            processed_kwargs[key] = "__ARRAY__"
        elif hasattr(value, "values"):  # pandas Series
            data_arrays[f"_kwarg_{key}"] = np.asarray(value)
            processed_kwargs[key] = "__ARRAY__"
        elif _is_serializable(value):
            processed_kwargs[key] = value
        else:
            try:
                processed_kwargs[key] = str(value)
            except Exception:
                pass

    # Process positional args (less common for seaborn)
    processed_args = []
    for i, arg in enumerate(args):
        if isinstance(arg, np.ndarray):
            data_arrays[f"_arg_{i}"] = arg
            processed_args.append("__ARRAY__")
        elif hasattr(arg, "values"):
            data_arrays[f"_arg_{i}"] = np.asarray(arg)
            processed_args.append("__ARRAY__")
        elif _is_serializable(arg):
            processed_args.append(arg)
        else:
            processed_args.append(str(arg))

    return tuple(processed_args), processed_kwargs, data_arrays


def _is_serializable(value: Any) -> bool:
    """Check if value is directly serializable."""
    if value is None:
        return True
    if isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_serializable(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_serializable(v) for k, v in value.items())
    return False


class SeabornRecorder:
    """Wrapper that records seaborn plotting calls."""

    def __init__(self):
        _check_seaborn()

    def __getattr__(self, name: str) -> Callable:
        """Get a wrapped seaborn function."""
        if name.startswith("_"):
            raise AttributeError(name)

        if not hasattr(sns, name):
            raise AttributeError(f"seaborn has no attribute '{name}'")

        original_func = getattr(sns, name)

        if name not in SEABORN_PLOT_FUNCTIONS:
            # Return unwrapped for non-plotting functions
            return original_func

        @wraps(original_func)
        def wrapped(*args, **kwargs):
            return self._record_and_call(name, original_func, args, kwargs)

        return wrapped

    def _record_and_call(
        self,
        func_name: str,
        func: Callable,
        args: tuple,
        kwargs: Dict[str, Any],
    ) -> Any:
        """Record the seaborn call and execute it.

        Parameters
        ----------
        func_name : str
            Name of the seaborn function.
        func : callable
            The actual seaborn function.
        args : tuple
            Positional arguments.
        kwargs : dict
            Keyword arguments.

        Returns
        -------
        Any
            Result from the seaborn function.
        """
        from ._wrappers._axes import RecordingAxes

        # Extract custom ID if provided
        call_id = kwargs.pop("id", None)

        # Get the axes
        ax = kwargs.get("ax")

        # If we have a RecordingAxes, disable recording during seaborn call
        # to prevent recording the underlying matplotlib calls (e.g., scatter)
        # that seaborn makes internally. We only want to record the seaborn call.
        if isinstance(ax, RecordingAxes):
            with ax._no_record():
                result = func(*args, **kwargs)

            # Serialize arguments
            proc_args, proc_kwargs, data_arrays = _serialize_seaborn_args(
                func_name, args, kwargs
            )

            # Record as a seaborn call (outside _no_record context)
            ax._record_seaborn_call(
                func_name=func_name,
                args=proc_args,
                kwargs=proc_kwargs,
                data_arrays=data_arrays,
                call_id=call_id,
            )
        else:
            # No recording axes, just call the function
            result = func(*args, **kwargs)

        return result


# Module-level instance for convenient access
_recorder: Optional[SeabornRecorder] = None


def get_seaborn_recorder() -> SeabornRecorder:
    """Get or create the seaborn recorder instance."""
    global _recorder
    if _recorder is None:
        _recorder = SeabornRecorder()
    return _recorder
