#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recipe metadata inspection (without reproducing the figure).

Extracted from ``_core.py`` -- reading a recipe's metadata is a distinct
concern from replaying it, and keeping it here keeps ``_core.py`` within the
project's per-file line budget.
"""

from pathlib import Path
from typing import Any, Dict, Union

from .._serializer import load_recipe


def get_recipe_info(path: Union[str, Path]) -> Dict[str, Any]:
    """Get recipe metadata (id, figsize, dpi, n_axes, calls) without reproducing."""
    record = load_recipe(path)

    all_calls = []
    for ax_record in record.axes.values():
        for call in ax_record.calls:
            all_calls.append(
                {
                    "id": call.id,
                    "function": call.function,
                    "n_args": len(call.args),
                    "kwargs": list(call.kwargs.keys()),
                }
            )
        for call in ax_record.decorations:
            all_calls.append(
                {
                    "id": call.id,
                    "function": call.function,
                    "type": "decoration",
                }
            )

    return {
        "id": record.id,
        "created": record.created,
        "matplotlib_version": record.matplotlib_version,
        "figsize": record.figsize,
        "dpi": record.dpi,
        "n_axes": len(record.axes),
        "calls": all_calls,
    }


__all__ = ["get_recipe_info"]
