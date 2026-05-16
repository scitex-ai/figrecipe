"""Regression test for figrecipe#110 — stx_line (x, y) convention."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np

import figrecipe


class TestStxLineSignature:
    def test_two_arg_x_then_y(self):
        """#110: `ax.stx_line(x, y)` must match matplotlib's `ax.plot(x, y)`."""
        fig, ax = figrecipe.subplots()
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.sin(x)
        _, df = ax.stx_line(x, y)
        # The df stores the x/y actually sent to ax.plot. Before the fix,
        # they were swapped.
        assert abs(df["x"].min() - 0.0) < 1e-9
        assert abs(df["x"].max() - 2 * np.pi) < 1e-9
        assert abs(df["y"].iloc[0] - 0.0) < 1e-9  # sin(0)
        assert abs(df["y"].iloc[-1] - 0.0) < 1e-6  # sin(2π)

    def test_single_arg_backward_compat(self):
        """Single-arg `ax.stx_line(y)` still generates x as arange(len(y))."""
        fig, ax = figrecipe.subplots()
        y = np.array([10.0, 20.0, 30.0, 40.0])
        _, df = ax.stx_line(y)
        assert list(df["x"]) == [0, 1, 2, 3]
        assert list(df["y"]) == [10.0, 20.0, 30.0, 40.0]


# EOF
