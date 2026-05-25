"""Regression test for figrecipe#110 — stx_line (x, y) convention."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np

import figrecipe


class TestStxLineSignature:
    def test_two_arg_x_then_y_part_1(self):
        """#110: `ax.stx_line(x, y)` must match matplotlib's `ax.plot(x, y)`."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.sin(x)
        _, df = ax.stx_line(x, y)
        assert abs(df["x"].min() - 0.0) < 1e-9

    def test_two_arg_x_then_y_part_2(self):
        """#110: `ax.stx_line(x, y)` must match matplotlib's `ax.plot(x, y)`."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.sin(x)
        _, df = ax.stx_line(x, y)
        assert abs(df["x"].max() - 2 * np.pi) < 1e-9

    def test_two_arg_x_then_y_part_3(self):
        """#110: `ax.stx_line(x, y)` must match matplotlib's `ax.plot(x, y)`."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.sin(x)
        _, df = ax.stx_line(x, y)
        assert abs(df["y"].iloc[0] - 0.0) < 1e-9  # sin(0)

    def test_two_arg_x_then_y_part_4(self):
        """#110: `ax.stx_line(x, y)` must match matplotlib's `ax.plot(x, y)`."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        x = np.linspace(0, 2 * np.pi, 50)
        y = np.sin(x)
        _, df = ax.stx_line(x, y)
        assert abs(df["y"].iloc[-1] - 0.0) < 1e-6  # sin(2π)

    def test_single_arg_backward_compat_part_1(self):
        """Single-arg `ax.stx_line(y)` still generates x as arange(len(y))."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        y = np.array([10.0, 20.0, 30.0, 40.0])
        _, df = ax.stx_line(y)
        assert list(df["x"]) == [0, 1, 2, 3]

    def test_single_arg_backward_compat_part_2(self):
        """Single-arg `ax.stx_line(y)` still generates x as arange(len(y))."""
        # Arrange
        # Act
        # Assert
        fig, ax = figrecipe.subplots()
        y = np.array([10.0, 20.0, 30.0, 40.0])
        _, df = ax.stx_line(y)
        assert list(df["y"]) == [10.0, 20.0, 30.0, 40.0]


# EOF
