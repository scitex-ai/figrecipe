#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ``stx_annotate_n`` sample-size annotation helper."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest


class TestAnnotateN:
    """Tests for the standalone ``stx_annotate_n`` implementation."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    def test_returns_a_text_artist(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 2])
        # Act
        out = stx_annotate_n(ax, 1, 1, 340)
        # Assert
        assert isinstance(out, matplotlib.text.Text)

    def test_default_text_is_n_equals(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 2])
        # Act
        out = stx_annotate_n(ax, 1, 1, 340)
        # Assert
        assert out.get_text() == "n=340"

    def test_integer_n_gets_comma_formatted(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 12340)
        # Assert
        assert out.get_text() == "n=12,340"

    def test_comma_false_disables_grouping(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 12340, comma=False)
        # Assert
        assert out.get_text() == "n=12340"

    def test_custom_prefix_capital_n(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 12, prefix="N")
        # Assert
        assert out.get_text() == "N=12"

    def test_string_n_used_verbatim_with_suffix_semantics(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, "12 patients", prefix="N")
        # Assert
        assert out.get_text() == "N=12 patients"

    def test_suffix_is_appended_to_label(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 12, suffix=" patients")
        # Assert
        assert out.get_text() == "n=12 patients"

    def test_default_color_is_black(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 5)
        # Assert
        assert matplotlib.colors.to_hex(out.get_color()) == "#000000"

    def test_custom_color_applied(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 5, color="red")
        # Assert
        assert matplotlib.colors.to_hex(out.get_color()) == "#ff0000"

    def test_default_fontsize_is_small_annotation_size(self):
        # Arrange: the default (SCITEX) style's fonts.annotation_pt is 6.
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 5)
        # Assert
        assert out.get_fontsize() == 6

    def test_explicit_fontsize_respected(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0, 0, 5, fontsize=9)
        # Assert
        assert out.get_fontsize() == 9

    def test_label_offset_from_anchor_point(self):
        # Arrange: overlap avoidance should move the label off the exact
        # data coordinate, not stack it directly on the point.
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], marker="o")
        # Act
        out = stx_annotate_n(ax, 0.5, 0.5, 10)
        # Assert
        xd, yd = out.get_position()
        assert (xd, yd) != (0.5, 0.5)

    def test_avoid_overlap_false_still_offsets_by_offset_pt(self):
        # Arrange
        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # Act
        out = stx_annotate_n(ax, 0.5, 0.5, 10, avoid_overlap=False)
        # Assert
        xd, yd = out.get_position()
        assert (xd, yd) != (0.5, 0.5)

    def test_crowded_axes_emits_warning_not_silent(self):
        # Arrange
        # Box the annotation in on all sides with dense ink so the ring
        # search exhausts its reach and must fall back -- this must warn,
        # never fail silently.
        import numpy as np

        from figrecipe._scitex_compat._annotate_n import stx_annotate_n

        fig, ax = plt.subplots(figsize=(1.0, 1.0))
        xx, yy = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 60))
        ax.pcolormesh(xx, yy, xx + yy)
        # Act
        warns_on_fallback = pytest.warns(UserWarning)
        # Assert
        with warns_on_fallback:
            stx_annotate_n(ax, 0.5, 0.5, 10, max_radius=8.0)

    def test_recording_axes_method_returns_result(self):
        # Arrange
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 2])
        # Act
        out = ax.stx_annotate_n(1, 1, 340)
        # Assert
        assert out is not None

    def test_recording_axes_roundtrip(self, tmp_path):
        # Arrange: the composite stx_* call must survive save -> reproduce.
        import figrecipe as fr

        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 2], id="trace")
        ax.stx_annotate_n(1, 1, 340, id="n_label")
        output_path = tmp_path / "annotate_n.yaml"
        # Act
        fr.save(fig, output_path)
        plt.close("all")
        fig2, ax2 = fr.reproduce(output_path)
        # Assert
        assert fig2 is not None
