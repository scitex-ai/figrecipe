#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SciTeX compatibility module (internal, not public API).

Contains scientific plot implementations ported from scitex.plt.
These are wired into RecordingAxes as stx_* methods.
Code is preserved here for easy recovery and maintenance.
"""

from ._heatmap import stx_heatmap
from ._scientific import stx_conf_mat, stx_ecdf, stx_raster, stx_scatter_hist
from ._shaded_lines import (
    stx_line,
    stx_mean_ci,
    stx_mean_std,
    stx_median_iqr,
    stx_shaded_line,
)
from ._simple import (
    stx_fillv,
    stx_image,
    stx_rectangle,
    stx_scalebar,
    stx_violin,
)

__all__ = [
    "stx_conf_mat",
    "stx_ecdf",
    "stx_fillv",
    "stx_heatmap",
    "stx_image",
    "stx_line",
    "stx_mean_ci",
    "stx_mean_std",
    "stx_median_iqr",
    "stx_raster",
    "stx_rectangle",
    "stx_scalebar",
    "stx_scatter_hist",
    "stx_shaded_line",
    "stx_violin",
]

# _csv_formatters/ subpackage: SigmaPlot-compatible CSV export handlers (65 files).
# Preserved from scitex.plt._subplots._export_as_csv_formatters.
# Deferred — not imported here, not part of public API.
# See _csv_formatters/README.md for details.

# EOF
