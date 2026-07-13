#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for thousands-separator comma tick formatting."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest


class TestCommaFormatter:
    """Tests for the ``CommaFormatter`` class."""

    def test_default_format_adds_commas(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import CommaFormatter

        formatter = CommaFormatter()
        # Act
        result = formatter(12000)
        # Assert
        assert result == "12,000"

    def test_default_format_small_number_no_commas(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import CommaFormatter

        formatter = CommaFormatter()
        # Act
        result = formatter(42)
        # Assert
        assert result == "42"

    def test_custom_fformat_decimal_places(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import CommaFormatter

        formatter = CommaFormatter(fformat="{:,.2f}")
        # Act
        result = formatter(1234.5)
        # Assert
        assert result == "1,234.50"

    def test_millions_get_two_commas(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import CommaFormatter

        formatter = CommaFormatter()
        # Act
        result = formatter(1234567)
        # Assert
        assert result == "1,234,567"


class TestCommaFormat:
    """Tests for the ``comma_format(ax, ...)`` helper."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    def test_returns_same_axes(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import comma_format

        fig, ax = plt.subplots()
        ax.plot([0, 12000, 24000], [0, 1, 2])
        # Act
        out = comma_format(ax, x=True)
        # Assert
        assert out is ax

    def test_x_axis_formatter_applied(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import (
            CommaFormatter,
            comma_format,
        )

        fig, ax = plt.subplots()
        ax.plot([0, 12000, 24000], [0, 1, 2])
        # Act
        comma_format(ax, x=True)
        # Assert
        assert isinstance(ax.xaxis.get_major_formatter(), CommaFormatter)

    def test_y_axis_formatter_applied(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import (
            CommaFormatter,
            comma_format,
        )

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 12000])
        # Act
        comma_format(ax, y=True)
        # Assert
        assert isinstance(ax.yaxis.get_major_formatter(), CommaFormatter)

    def test_default_neither_axis_touched(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import (
            CommaFormatter,
            comma_format,
        )

        fig, ax = plt.subplots()
        ax.plot([0, 12000], [0, 12000])
        # Act
        comma_format(ax)
        # Assert
        assert not isinstance(ax.xaxis.get_major_formatter(), CommaFormatter)
        assert not isinstance(ax.yaxis.get_major_formatter(), CommaFormatter)

    def test_rendered_tick_label_has_comma(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import comma_format

        fig, ax = plt.subplots()
        ax.plot([0, 24000], [0, 1])
        ax.set_xticks([12000])
        comma_format(ax, x=True)
        # Act
        fig.canvas.draw()
        label = ax.get_xticklabels()[0].get_text()
        # Assert
        assert label == "12,000"

    def test_recording_axes_method(self):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.plot([0, 12000, 24000], [0, 1, 2])
        # Act
        out = ax.comma_format(x=True)
        # Assert
        assert out is not None

    def test_rejects_non_axes(self):
        # Arrange
        from figrecipe.styles._axis_helpers._comma_format import comma_format

        # Act / Assert
        with pytest.raises(TypeError):
            comma_format("not an axes", x=True)
