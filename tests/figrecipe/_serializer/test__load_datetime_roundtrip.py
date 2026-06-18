#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression: datetime plot data must round-trip idempotently.

``datetime64.tolist()`` yields nanosecond integers; without the ``_load.py``
fix those get re-saved INLINE on a reproduce + re-save and then reload as raw
numbers (plotting at ~1.3e18 instead of as dates), making the
save -> reproduce -> save round-trip non-idempotent and breaking reproducibility
validation. These tests pin the fix: a datetime arg stays a CSV file reference
(dtype preserved) across a reproduce + re-save instead of degrading to an inline
integer list.
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing

import matplotlib.pyplot as plt
import numpy as np


def _datetime_arg(recipe_path):
    """Return the first plot arg recorded with a datetime dtype, or None."""
    import yaml

    with open(recipe_path) as f:
        data = yaml.safe_load(f)
    for ax in data.get("axes", {}).values():
        for call in ax.get("calls", []):
            for arg in call.get("args", []):
                if "datetime" in str(arg.get("dtype", "")):
                    return arg
    return None


def _roundtrip(tmpdir):
    """Save a datetime line, reproduce it, re-save; return (first, second) recipes."""
    import figrecipe as ps

    # 300 points so the array is file-stored (CSV), not inlined.
    x = np.arange("2020-01-01", "2020-10-27", dtype="datetime64[D]").astype(
        "datetime64[ns]"
    )
    y = np.linspace(0.0, 1.0, len(x))

    fig1, ax1 = ps.subplots()
    ax1.plot(x, y, id="dt_line")
    first = Path(tmpdir) / "first.yaml"
    ps.save(fig1, first, validate=False)
    plt.close(fig1.fig if hasattr(fig1, "fig") else fig1)

    fig2, _ = ps.reproduce(first)
    second = Path(tmpdir) / "second.yaml"
    ps.save(fig2, second, validate=False)
    plt.close(fig2.fig if hasattr(fig2, "fig") else fig2)

    return first, second


class TestDatetimeRoundtrip:
    """A datetime arg stays a CSV ref across reproduce + re-save (idempotent)."""

    def test_first_save_records_datetime_dtype(self):
        # Arrange
        tmp = tempfile.TemporaryDirectory()
        # Act
        first, _ = _roundtrip(tmp.name)
        arg = _datetime_arg(first)
        # Assert
        assert arg is not None and "datetime64" in str(arg.get("dtype"))

    def test_resave_keeps_datetime_as_csv_reference(self):
        # Arrange
        tmp = tempfile.TemporaryDirectory()
        # Act
        _, second = _roundtrip(tmp.name)
        arg = _datetime_arg(second)
        # Assert
        assert (
            arg is not None
            and isinstance(arg.get("data"), str)
            and str(arg.get("data")).endswith(".csv")
        )


# EOF
