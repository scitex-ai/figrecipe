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

    def test_acorr(self):
        success, msg = run_pixel_perfect_test("acorr")
        assert success, f"acorr: {msg}"

    def test_angle_spectrum(self):
        success, msg = run_pixel_perfect_test("angle_spectrum")
        assert success, f"angle_spectrum: {msg}"

    def test_bar(self):
        success, msg = run_pixel_perfect_test("bar")
        assert success, f"bar: {msg}"

    def test_barbs(self):
        success, msg = run_pixel_perfect_test("barbs")
        assert success, f"barbs: {msg}"

    def test_barh(self):
        success, msg = run_pixel_perfect_test("barh")
        assert success, f"barh: {msg}"

    def test_boxplot(self):
        success, msg = run_pixel_perfect_test("boxplot")
        assert success, f"boxplot: {msg}"

    def test_cohere(self):
        success, msg = run_pixel_perfect_test("cohere")
        assert success, f"cohere: {msg}"

    def test_contour(self):
        success, msg = run_pixel_perfect_test("contour")
        assert success, f"contour: {msg}"

    def test_contourf(self):
        success, msg = run_pixel_perfect_test("contourf")
        assert success, f"contourf: {msg}"

    def test_csd(self):
        success, msg = run_pixel_perfect_test("csd")
        assert success, f"csd: {msg}"

    def test_ecdf(self):
        success, msg = run_pixel_perfect_test("ecdf")
        assert success, f"ecdf: {msg}"

    def test_errorbar(self):
        success, msg = run_pixel_perfect_test("errorbar")
        assert success, f"errorbar: {msg}"

    def test_eventplot(self):
        success, msg = run_pixel_perfect_test("eventplot")
        assert success, f"eventplot: {msg}"

    def test_fill(self):
        success, msg = run_pixel_perfect_test("fill")
        assert success, f"fill: {msg}"

    def test_fill_between(self):
        success, msg = run_pixel_perfect_test("fill_between")
        assert success, f"fill_between: {msg}"

    def test_fill_betweenx(self):
        success, msg = run_pixel_perfect_test("fill_betweenx")
        assert success, f"fill_betweenx: {msg}"

    def test_graph(self):
        success, msg = run_pixel_perfect_test("graph")
        assert success, f"graph: {msg}"

    def test_hexbin(self):
        success, msg = run_pixel_perfect_test("hexbin")
        assert success, f"hexbin: {msg}"

    def test_hist(self):
        success, msg = run_pixel_perfect_test("hist")
        assert success, f"hist: {msg}"

    def test_hist2d(self):
        success, msg = run_pixel_perfect_test("hist2d")
        assert success, f"hist2d: {msg}"

    def test_imshow(self):
        success, msg = run_pixel_perfect_test("imshow")
        assert success, f"imshow: {msg}"

    def test_loglog(self):
        success, msg = run_pixel_perfect_test("loglog")
        assert success, f"loglog: {msg}"

    def test_magnitude_spectrum(self):
        success, msg = run_pixel_perfect_test("magnitude_spectrum")
        assert success, f"magnitude_spectrum: {msg}"

    def test_matshow(self):
        success, msg = run_pixel_perfect_test("matshow")
        assert success, f"matshow: {msg}"

    def test_pcolor(self):
        success, msg = run_pixel_perfect_test("pcolor")
        assert success, f"pcolor: {msg}"

    def test_pcolormesh(self):
        success, msg = run_pixel_perfect_test("pcolormesh")
        assert success, f"pcolormesh: {msg}"

    def test_phase_spectrum(self):
        success, msg = run_pixel_perfect_test("phase_spectrum")
        assert success, f"phase_spectrum: {msg}"

    def test_pie(self):
        success, msg = run_pixel_perfect_test("pie")
        assert success, f"pie: {msg}"

    def test_plot(self):
        success, msg = run_pixel_perfect_test("plot")
        assert success, f"plot: {msg}"

    def test_psd(self):
        success, msg = run_pixel_perfect_test("psd")
        assert success, f"psd: {msg}"

    def test_quiver(self):
        success, msg = run_pixel_perfect_test("quiver")
        assert success, f"quiver: {msg}"

    def test_scatter(self):
        success, msg = run_pixel_perfect_test("scatter")
        assert success, f"scatter: {msg}"

    def test_semilogx(self):
        success, msg = run_pixel_perfect_test("semilogx")
        assert success, f"semilogx: {msg}"

    def test_semilogy(self):
        success, msg = run_pixel_perfect_test("semilogy")
        assert success, f"semilogy: {msg}"

    def test_specgram(self):
        success, msg = run_pixel_perfect_test("specgram")
        assert success, f"specgram: {msg}"

    def test_spy(self):
        success, msg = run_pixel_perfect_test("spy")
        assert success, f"spy: {msg}"

    def test_stackplot(self):
        success, msg = run_pixel_perfect_test("stackplot")
        assert success, f"stackplot: {msg}"

    def test_stairs(self):
        success, msg = run_pixel_perfect_test("stairs")
        assert success, f"stairs: {msg}"

    def test_stem(self):
        success, msg = run_pixel_perfect_test("stem")
        assert success, f"stem: {msg}"

    def test_step(self):
        success, msg = run_pixel_perfect_test("step")
        assert success, f"step: {msg}"

    def test_streamplot(self):
        success, msg = run_pixel_perfect_test("streamplot")
        assert success, f"streamplot: {msg}"

    def test_tricontour(self):
        success, msg = run_pixel_perfect_test("tricontour")
        assert success, f"tricontour: {msg}"

    def test_tricontourf(self):
        success, msg = run_pixel_perfect_test("tricontourf")
        assert success, f"tricontourf: {msg}"

    def test_tripcolor(self):
        success, msg = run_pixel_perfect_test("tripcolor")
        assert success, f"tripcolor: {msg}"

    def test_triplot(self):
        success, msg = run_pixel_perfect_test("triplot")
        assert success, f"triplot: {msg}"

    def test_violinplot(self):
        success, msg = run_pixel_perfect_test("violinplot")
        assert success, f"violinplot: {msg}"

    def test_xcorr(self):
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
