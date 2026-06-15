#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Factory function for creating recording-enabled subplots."""

from typing import TYPE_CHECKING, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from ._axes import RecordingAxes
from ._figure import RecordingFigure

if TYPE_CHECKING:
    from .._recorder import Recorder


def create_recording_subplots(
    nrows: int = 1,
    ncols: int = 1,
    recorder: Optional["Recorder"] = None,
    panel_labels: bool = False,
    **kwargs,
) -> Tuple[RecordingFigure, Union[RecordingAxes, NDArray]]:
    """Create a figure with recording-enabled axes.

    Parameters
    ----------
    nrows : int
        Number of rows.
    ncols : int
        Number of columns.
    recorder : Recorder, optional
        Recorder instance. Created if not provided.
    panel_labels : bool
        If True and figure has multiple panels, automatically add
        panel labels (A, B, C, D, ...). Default is False.
    **kwargs
        Passed to plt.subplots().

    Returns
    -------
    fig : RecordingFigure
        Wrapped figure.
    axes : RecordingAxes or ndarray
        Wrapped axes (single if 1x1, otherwise numpy array matching matplotlib).

    Examples
    --------
    >>> fig, axes = fr.subplots(2, 2, panel_labels=True)  # Auto-adds A, B, C, D
    """
    from .._recorder import Recorder

    if recorder is None:
        recorder = Recorder()

    # Create matplotlib figure
    import matplotlib.pyplot as plt

    fig, mpl_axes = plt.subplots(nrows, ncols, **kwargs)

    # Get figsize and dpi
    figsize = kwargs.get("figsize", fig.get_size_inches())
    dpi = kwargs.get("dpi", fig.dpi)

    # Start recording (record grid shape so panel-letter assignment for
    # data-file / legend-file naming agrees with the rendered panel labels).
    recorder.start_figure(
        figsize=tuple(figsize), dpi=int(dpi), nrows=nrows, ncols=ncols
    )

    # Wrap axes
    if nrows == 1 and ncols == 1:
        wrapped_ax = RecordingAxes(mpl_axes, recorder, position=(0, 0))
        wrapped_fig = RecordingFigure(fig, recorder, wrapped_ax)
        return wrapped_fig, wrapped_ax

    # Handle 1D or 2D arrays - reshape to (nrows, ncols) for uniform processing
    mpl_axes_arr = np.asarray(mpl_axes)
    if mpl_axes_arr.ndim == 1:
        mpl_axes_arr = mpl_axes_arr.reshape(nrows, ncols)

    wrapped_axes = []
    for i in range(nrows):
        row = []
        for j in range(ncols):
            row.append(RecordingAxes(mpl_axes_arr[i, j], recorder, position=(i, j)))
        wrapped_axes.append(row)

    wrapped_fig = RecordingFigure(fig, recorder, wrapped_axes)

    # Add panel labels if requested (multi-panel figures only)
    if panel_labels:
        wrapped_fig.add_panel_labels()

    # Return in same shape as matplotlib (numpy arrays for consistency)
    if nrows == 1:
        # 1xN -> 1D array of shape (N,)
        return wrapped_fig, np.array(wrapped_axes[0], dtype=object)
    elif ncols == 1:
        # Nx1 -> 1D array of shape (N,)
        return wrapped_fig, np.array([row[0] for row in wrapped_axes], dtype=object)
    else:
        # NxM -> 2D array
        return wrapped_fig, np.array(wrapped_axes, dtype=object)


__all__ = ["create_recording_subplots"]

# EOF
