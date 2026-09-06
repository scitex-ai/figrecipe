#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pixel-perfect reproduction tests for all 47 plot types.

Run with pytest-xdist for parallel execution:
    pytest tests/test_pixel_perfect.py -n auto -v

Each test creates a figure, saves it, reproduces from recipe, and compares
pixel-by-pixel. Threshold is 0 (exact match required).
"""

import sys
import tempfile
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import figrecipe as fr
from figrecipe._dev import PLOTTERS
from figrecipe.styles._finalize import finalize_special_plots, finalize_ticks


def pixel_diff(img1_path, img2_path):
    """Compare two images pixel-by-pixel. Returns (diff, error_msg)."""
    from PIL import Image

    img1 = np.array(Image.open(img1_path).convert("RGBA"))
    img2 = np.array(Image.open(img2_path).convert("RGBA"))
    if img1.shape != img2.shape:
        return -1, f"Shape mismatch: {img1.shape} vs {img2.shape}"
    diff = np.sum(np.abs(img1.astype(float) - img2.astype(float)))
    return diff, None


def run_pixel_perfect_test(plot_type):
    """Run pixel-perfect test for a single plot type."""
    rng = np.random.default_rng(42)
    plotter = PLOTTERS[plot_type]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create original figure
        fig, ax = plotter(fr, rng)

        # Apply finalization (same as reproduction does)
        style = fig._recorder.figure_record.style or {}
        axes_list = fig.flat if hasattr(fig, "flat") else [ax]
        for a in axes_list:
            mpl_ax = getattr(a, "_ax", a)
            finalize_ticks(mpl_ax)
            finalize_special_plots(mpl_ax, style)

        # Save original with raw matplotlib (no cropping)
        orig_path = tmpdir / f"{plot_type}_orig.png"
        fig._fig.savefig(orig_path, dpi=300)

        # Save recipe
        yaml_path = tmpdir / f"{plot_type}.yaml"
        fig.save_recipe(yaml_path)
        plt.close(fig._fig)

        # Reproduce
        fig2, ax2 = fr.reproduce(yaml_path)

        # Save reproduced with raw matplotlib
        repro_path = tmpdir / f"{plot_type}_repro.png"
        fig2._fig.savefig(repro_path, dpi=300)
        plt.close(fig2._fig)

        # Compare
        diff, err = pixel_diff(orig_path, repro_path)

        if err:
            return False, err
        elif diff == 0:
            return True, "Pixel-perfect"
        else:
            return False, f"Pixel diff={diff}"


class TestPixelPerfect:
    """Pixel-perfect reproduction tests for all plot types."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset matplotlib and figrecipe state."""
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    def test_acorr_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("acorr")
        assert success, f"acorr: {msg}"

    def test_angle_spectrum_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("angle_spectrum")
        assert success, f"angle_spectrum: {msg}"

    def test_bar_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("bar")
        assert success, f"bar: {msg}"

    def test_barbs_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("barbs")
        assert success, f"barbs: {msg}"

    def test_barh_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("barh")
        assert success, f"barh: {msg}"

    def test_boxplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("boxplot")
        assert success, f"boxplot: {msg}"

    def test_cohere_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("cohere")
        assert success, f"cohere: {msg}"

    def test_contour_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("contour")
        assert success, f"contour: {msg}"

    def test_contourf_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("contourf")
        assert success, f"contourf: {msg}"

    def test_csd_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("csd")
        assert success, f"csd: {msg}"

    def test_ecdf_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("ecdf")
        assert success, f"ecdf: {msg}"

    def test_errorbar_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("errorbar")
        assert success, f"errorbar: {msg}"

    def test_eventplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("eventplot")
        assert success, f"eventplot: {msg}"

    def test_fill_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("fill")
        assert success, f"fill: {msg}"

    def test_fill_between_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("fill_between")
        assert success, f"fill_between: {msg}"

    def test_fill_betweenx_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("fill_betweenx")
        assert success, f"fill_betweenx: {msg}"

    def test_graph_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("graph")
        assert success, f"graph: {msg}"

    def test_hexbin_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("hexbin")
        assert success, f"hexbin: {msg}"

    def test_hist_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("hist")
        assert success, f"hist: {msg}"

    def test_hist2d_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("hist2d")
        assert success, f"hist2d: {msg}"

    def test_hlines_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("hlines")
        assert success, f"hlines: {msg}"

    def test_imshow_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("imshow")
        assert success, f"imshow: {msg}"

    def test_loglog_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("loglog")
        assert success, f"loglog: {msg}"

    def test_magnitude_spectrum_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("magnitude_spectrum")
        assert success, f"magnitude_spectrum: {msg}"

    def test_matshow_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("matshow")
        assert success, f"matshow: {msg}"

    def test_pcolor_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("pcolor")
        assert success, f"pcolor: {msg}"

    def test_pcolormesh_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("pcolormesh")
        assert success, f"pcolormesh: {msg}"

    def test_phase_spectrum_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("phase_spectrum")
        assert success, f"phase_spectrum: {msg}"

    def test_pie_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("pie")
        assert success, f"pie: {msg}"

    def test_plot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("plot")
        assert success, f"plot: {msg}"

    def test_psd_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("psd")
        assert success, f"psd: {msg}"

    def test_quiver_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("quiver")
        assert success, f"quiver: {msg}"

    def test_scatter_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("scatter")
        assert success, f"scatter: {msg}"

    def test_semilogx_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("semilogx")
        assert success, f"semilogx: {msg}"

    def test_semilogy_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("semilogy")
        assert success, f"semilogy: {msg}"

    def test_specgram_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("specgram")
        assert success, f"specgram: {msg}"

    def test_spy_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("spy")
        assert success, f"spy: {msg}"

    def test_stackplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("stackplot")
        assert success, f"stackplot: {msg}"

    def test_stairs_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("stairs")
        assert success, f"stairs: {msg}"

    def test_stem_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("stem")
        assert success, f"stem: {msg}"

    def test_step_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("step")
        assert success, f"step: {msg}"

    def test_streamplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("streamplot")
        assert success, f"streamplot: {msg}"

    def test_tricontour_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("tricontour")
        assert success, f"tricontour: {msg}"

    def test_tricontourf_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("tricontourf")
        assert success, f"tricontourf: {msg}"

    def test_tripcolor_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("tripcolor")
        assert success, f"tripcolor: {msg}"

    def test_triplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("triplot")
        assert success, f"triplot: {msg}"

    def test_violinplot_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("violinplot")
        assert success, f"violinplot: {msg}"

    def test_vlines_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("vlines")
        assert success, f"vlines: {msg}"

    def test_xcorr_pixel_perfect(self):
        # Arrange
        # Act
        # Assert
        success, msg = run_pixel_perfect_test("xcorr")
        assert success, f"xcorr: {msg}"


if __name__ == "__main__":
    # Run quick summary
    print("Running pixel-perfect tests for all 47 plot types...")
    from figrecipe._dev import list_plotters

    passed = []
    failed = []

    for plot_type in list_plotters():
        try:
            success, msg = run_pixel_perfect_test(plot_type)
            if success:
                passed.append(plot_type)
                print(f"  {plot_type}: PASS")
            else:
                failed.append((plot_type, msg))
                print(f"  {plot_type}: FAIL - {msg}")
        except Exception as e:
            failed.append((plot_type, str(e)))
            print(f"  {plot_type}: ERROR - {e}")

    print(f"\nPassed: {len(passed)}/47")
    print(f"Failed: {len(failed)}/47")
    if failed:
        print("\nFailed tests:")
        for name, msg in failed:
            print(f"  {name}: {msg}")


# ── rcParams the caller changed AFTER fr.subplots() ──────────────────────────
#
# The original honours them: fr.subplots() applies the style, the caller's
# change lands next, the artists are created last. Replay used to invert that
# -- apply_recorded_rcparams first, then apply_style_mm, whose GLOBAL rcParams
# writes overwrote the recipe's own values -- so a correct figure came back
# wrong (measured 2026-09-06: lines.linewidth MSE 1082, axes.titlesize 1185,
# a serif font 157, plt.style.use("ggplot") 467). Each test below saves through
# the public API with validation on and asserts the verdict.


def _rc_case_verdict(tmpdir, name, build):
    """Build under a scoped rc_context, save, return the validation result."""
    with matplotlib.rc_context():
        plt.style.use("default")
        try:
            fig = build()
            _img, _yml, result = fr.save(
                fig,
                str(Path(tmpdir) / f"{name}.png"),
                validate_error_level="warning",
                verbose=False,
            )
            return result
        finally:
            plt.close("all")


def _two_lines(ax):
    x = np.linspace(0, 10, 50)
    ax.plot(x, np.sin(x), id="sin")
    ax.plot(x, np.cos(x), id="cos")


def test_linewidth_set_after_subplots_reproduces(tmp_path):
    # Arrange
    def build():
        fig, ax = fr.subplots()
        matplotlib.rcParams["lines.linewidth"] = 4
        _two_lines(ax)
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "linewidth_after", build)
    # Assert
    assert result.valid is True


def test_title_size_set_after_subplots_reproduces(tmp_path):
    # Arrange
    def build():
        fig, ax = fr.subplots()
        matplotlib.rcParams["axes.titlesize"] = 24
        _two_lines(ax)
        ax.set_title("Set after the rc change")
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "titlesize_after", build)
    # Assert
    assert result.valid is True


def test_font_family_set_after_subplots_reproduces(tmp_path):
    """The operator's shape: japanize / a font picked after the figure exists."""
    # Arrange
    def build():
        fig, ax = fr.subplots()
        matplotlib.rcParams["font.family"] = "Liberation Serif"
        ax.plot([1, 2, 3], [1, 4, 9], label="series", id="l")
        ax.legend()
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "font_after", build)
    # Assert
    assert result.valid is True


def test_control_figure_with_no_caller_rc_change_still_reproduces(tmp_path):
    """Control: the ordinary path must be untouched by the re-apply."""
    # Arrange
    def build():
        fig, ax = fr.subplots()
        _two_lines(ax)
        ax.set_title("plain")
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "plain", build)
    # Assert
    assert result.valid is True


def test_control_rc_change_before_subplots_still_reproduces(tmp_path):
    """Control: BEFORE-subplots changes always worked; keep it that way."""
    # Arrange
    def build():
        matplotlib.rcParams["font.family"] = "Liberation Serif"
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], label="series", id="l")
        ax.legend()
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "font_before", build)
    # Assert
    assert result.valid is True


def test_capstyle_rcparam_does_not_break_the_save(tmp_path):
    """A capstyle enum in rcParams used to raise and lose the whole recipe."""
    # Arrange
    def build():
        matplotlib.rcParams["lines.solid_capstyle"] = "round"
        fig, ax = fr.subplots()
        _two_lines(ax)
        return fig

    # Act
    result = _rc_case_verdict(tmp_path, "capstyle", build)
    # Assert
    assert result.valid is True


# EOF
