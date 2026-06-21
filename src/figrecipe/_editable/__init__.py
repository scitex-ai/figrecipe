#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: figrecipe/_editable/__init__.py

"""
Editable-figure export (schema ``scitex.plt.figure.editable``, v0.3).

This subsystem introspects a matplotlib (or figrecipe ``RecordingFigure``)
figure and emits a JSON-serializable dict describing per-element pixel
geometry, suitable for the GUI / web figure editor.

It is a figrecipe-native artifact: the only dependencies are matplotlib and
numpy. The public entry point is :func:`export_editable`.
"""

from ._editable_export import export_editable_figure
from ._editable_export import export_editable_figure as export_editable
from ._save import save_editable

__all__ = [
    "export_editable",
    "export_editable_figure",
    "save_editable",
]

# EOF
