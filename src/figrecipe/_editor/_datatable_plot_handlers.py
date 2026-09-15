#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot handlers for datatable plotting functionality."""

import numpy as np


def dispatch_plot(ax, plot_type, plot_data, columns, x_mode="guess"):
    """Dispatch plot based on type and data.

    Args:
        ax: Matplotlib axes object
        plot_type: Frontend plot type name
        plot_data: Dict mapping column names to data arrays
        columns: List of column names in order
        x_mode: How X is chosen for x/y plots (see ``_handle_standard_xy``)

    Returns:
        True on success

    Raises:
        ValueError: If plot type is unknown
    """
    # Map frontend names to matplotlib method names
    method_name = plot_type
    if plot_type == "line":
        method_name = "plot"
    elif plot_type == "histogram":
        method_name = "hist"

    # Get the plotting method
    plot_method = getattr(ax, method_name, None)
    if plot_method is None:
        raise ValueError(f"Unknown plot type: {plot_type}")

    # Prepare data arrays
    data_arrays = [np.array(plot_data.get(c, [])) for c in columns]

    # Handle decoration methods
    if _handle_decoration(ax, method_name, data_arrays):
        return True

    # Handle specialized plot types
    if _handle_specialized(ax, plot_method, method_name, data_arrays, columns):
        return True

    # Handle standard xy plots
    _handle_standard_xy(ax, plot_method, method_name, data_arrays, columns, x_mode)
    return True


def _handle_decoration(ax, method_name, data_arrays):
    """Handle decoration methods (scalar-based, iterate over rows)."""
    decoration_methods = {
        "text",
        "annotate",
        "arrow",
        "axhline",
        "axvline",
        "axhspan",
        "axvspan",
    }

    if method_name not in decoration_methods:
        return False

    n_rows = len(data_arrays[0]) if data_arrays else 0

    for row_idx in range(n_rows):
        row_vals = [arr[row_idx] for arr in data_arrays]

        if method_name == "text" and len(row_vals) >= 2:
            s = str(row_vals[2]) if len(row_vals) >= 3 else ""
            ax.text(row_vals[0], row_vals[1], s)

        elif method_name == "annotate":
            if len(row_vals) >= 3:
                ax.annotate(str(row_vals[0]), xy=(row_vals[1], row_vals[2]))
            elif len(row_vals) == 2:
                ax.annotate("", xy=(row_vals[0], row_vals[1]))

        elif method_name == "arrow" and len(row_vals) >= 4:
            ax.arrow(
                row_vals[0],
                row_vals[1],
                row_vals[2],
                row_vals[3],
                head_width=0.1,
                head_length=0.05,
            )

        elif method_name == "axhline" and len(row_vals) >= 1:
            ax.axhline(y=row_vals[0])

        elif method_name == "axvline" and len(row_vals) >= 1:
            ax.axvline(x=row_vals[0])

        elif method_name == "axhspan" and len(row_vals) >= 2:
            ax.axhspan(row_vals[0], row_vals[1], alpha=0.3)

        elif method_name == "axvspan" and len(row_vals) >= 2:
            ax.axvspan(row_vals[0], row_vals[1], alpha=0.3)

    return True


def _handle_specialized(ax, plot_method, method_name, data_arrays, columns):
    """Handle specialized plot types that need custom argument handling."""
    if method_name in ("boxplot", "violinplot"):
        if method_name == "boxplot":
            # Matplotlib 3.9 renamed ``labels`` to ``tick_labels``.
            try:
                plot_method(data_arrays, tick_labels=columns)
            except TypeError:
                plot_method(data_arrays, labels=columns)
        else:
            plot_method(data_arrays)
            ax.set_xticks(range(1, len(columns) + 1))
            ax.set_xticklabels(columns)
        return True

    if method_name == "pie":
        labels = columns[1:] if len(columns) > 1 else None
        plot_method(data_arrays[0], labels=labels, autopct="%1.1f%%")
        return True

    if method_name in (
        "hist",
        "acorr",
        "psd",
        "specgram",
        "angle_spectrum",
        "phase_spectrum",
        "magnitude_spectrum",
    ):
        for i, arr in enumerate(data_arrays):
            plot_method(arr, label=columns[i])
        return True

    if method_name in ("hist2d", "hexbin", "xcorr", "csd", "cohere"):
        if len(data_arrays) >= 2:
            plot_method(data_arrays[0], data_arrays[1])
        return True

    if method_name in ("fill_between", "fill_betweenx"):
        if len(data_arrays) >= 3:
            plot_method(data_arrays[0], data_arrays[1], data_arrays[2], alpha=0.5)
        elif len(data_arrays) >= 2:
            plot_method(data_arrays[0], data_arrays[1], alpha=0.5)
        return True

    if method_name == "errorbar" and len(data_arrays) >= 3:
        plot_method(
            data_arrays[0], data_arrays[1], yerr=data_arrays[2], fmt="o-", capsize=3
        )
        return True

    if method_name in ("imshow", "matshow"):
        if len(data_arrays) == 1:
            arr = data_arrays[0]
            plot_method(arr.reshape(-1, 1) if arr.ndim == 1 else arr)
        else:
            plot_method(np.column_stack(data_arrays))
        return True

    if method_name in ("contour", "contourf", "pcolor", "pcolormesh"):
        if len(data_arrays) == 1:
            arr = data_arrays[0]
            plot_method(arr.reshape(-1, 1) if arr.ndim == 1 else arr)
        else:
            plot_method(np.column_stack(data_arrays))
        return True

    if method_name in ("quiver", "barbs", "streamplot"):
        if len(data_arrays) >= 4:
            plot_method(data_arrays[0], data_arrays[1], data_arrays[2], data_arrays[3])
        elif len(data_arrays) >= 2:
            x = np.arange(len(data_arrays[0]))
            y = np.arange(len(data_arrays[0]))
            plot_method(x, y, data_arrays[0], data_arrays[1])
        return True

    if method_name == "eventplot":
        plot_method(data_arrays)
        return True

    return False


def _handle_standard_xy(
    ax, plot_method, method_name, data_arrays, columns, x_mode="guess"
):
    """Handle standard x, y plots.

    ``x_mode``: ``"guess"`` finds X by column name, ``"first"`` takes
    ``columns[0]`` as X, ``"index"`` plots every column against the row number.
    """
    x_idx = None
    y_indices = []
    if x_mode == "first" and len(columns) >= 2:
        x_idx, y_indices = 0, list(range(1, len(columns)))
    elif x_mode == "guess":
        for i, col in enumerate(columns):
            if col.endswith("_x") or col.lower() == "x":
                x_idx = i
            else:
                y_indices.append(i)

    if x_idx is not None and y_indices:
        x_data = data_arrays[x_idx]
        y_arrays = [data_arrays[i] for i in y_indices]
        y_cols = [columns[i] for i in y_indices]
    elif x_mode == "guess" and len(data_arrays) >= 2:
        x_idx = 0
        x_data = data_arrays[0]
        y_arrays = data_arrays[1:]
        y_cols = columns[1:]
    else:
        x_data = np.arange(len(data_arrays[0]))
        y_arrays = data_arrays
        y_cols = columns

    for i, y_data in enumerate(y_arrays):
        if method_name == "bar" and len(y_arrays) > 1:
            width = 0.8 / len(y_arrays)
            offset = (i - len(y_arrays) / 2 + 0.5) * width
            plot_method(x_data + offset, y_data, width=width, label=y_cols[i])
        elif method_name == "barh":
            plot_method(x_data, y_data, label=y_cols[i])
        elif method_name in (
            "plot",
            "scatter",
            "step",
            "loglog",
            "semilogx",
            "semilogy",
        ):
            plot_method(x_data, y_data, label=y_cols[i])
        elif method_name == "stem":
            plot_method(x_data, y_data, label=y_cols[i])
        elif method_name == "fill":
            plot_method(x_data, y_data, alpha=0.5, label=y_cols[i])
        elif method_name == "stairs":
            plot_method(y_data, label=y_cols[i])
        elif method_name == "stackplot":
            plot_method(x_data, *y_arrays, labels=y_cols)
            break
        else:
            try:
                plot_method(x_data, y_data, label=y_cols[i])
            except TypeError:
                plot_method(y_data, label=y_cols[i])

    # Set labels
    if x_idx is not None:
        ax.set_xlabel(columns[x_idx])
    if len(y_cols) == 1:
        ax.set_ylabel(y_cols[0])
    if len(y_cols) > 1:
        ax.legend()


__all__ = ["dispatch_plot"]
