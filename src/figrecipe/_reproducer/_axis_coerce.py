#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coercion for replayed axis-limit / axis-line values."""

import warnings
from datetime import datetime
from typing import Any


def coerce_axis_value(value: Any) -> Any:
    """Coerce a recorded axis-limit / axis-line value back to a usable type.

    ``set_xlim`` / ``set_ylim`` / ``axvline`` / ``axhline`` are inherently
    numeric or datetime -- a category string is never a valid argument. A recipe
    can nonetheless carry such a value as a *string*:

    - ISO datetime strings, for datetime axes (recorded that way on purpose); or
    - a stringified number like ``'0'`` from recipes written before numpy
      scalars were serialized natively (figrecipe < 0.28.21, see
      ``_recorder/_utils._process_scalar``).

    matplotlib cannot convert a raw string to axis units on replay and raises
    "Failed to convert value(s) to axis units". Parse ISO datetimes to
    ``datetime`` and numeric strings to ``float`` (warning loudly, since the
    latter only happens for stale recipes); otherwise return ``value`` unchanged.
    """
    if not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        pass
    try:
        coerced = float(value)
    except (ValueError, TypeError):
        return value
    warnings.warn(
        f"Coerced stringified numeric axis value {value!r} to float on replay. "
        "This recipe predates native numpy-scalar serialization; re-record with "
        "figrecipe >= 0.28.21 to store numeric coordinates as numbers.",
        stacklevel=2,
    )
    return coerced
