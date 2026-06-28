#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared utilities for recipe serialization."""

from typing import Any

import numpy as np


def _convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.generic):
        # Catch-all for any remaining numpy scalar — np.str_, np.bytes_,
        # np.complex*, np.datetime64, etc. `.item()` returns the native Python
        # equivalent. Labels/ticks coming from a DataFrame column or numpy array
        # commonly arrive as np.str_ / np.float64; without this they reach the
        # YAML representer untouched and crash recipe save (ruamel
        # RepresenterError: cannot represent np.str_(...)).
        return obj.item()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        converted = [_convert_numpy_types(item) for item in obj]
        return type(obj)(converted) if isinstance(obj, tuple) else converted
    else:
        return obj


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for safe use in filenames.

    Replaces dots (except for extensions) to avoid Path.with_suffix() issues.
    """
    return name.replace(".", "_")
