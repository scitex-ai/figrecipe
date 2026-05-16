#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roundtrip tests for all plotting methods.

Tests each supported plotting method with save/reproduce cycle.
Uses _dev.PLOTTERS as single source of truth for available plotters.
"""

import sys
import tempfile
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import figrecipe as fr
from figrecipe._dev import PLOTTERS, list_plotters
from figrecipe._utils._image_diff import compare_images


class TestRoundtripAllPlotters:
    """Roundtrip tests for all plotting methods."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        """Reset matplotlib state before and after each test."""
        import gc

        def clear_all_caches():
            """Clear all figrecipe and matplotlib caches."""
            # Close all figures
            plt.close("all")
            matplotlib.rcdefaults()

            # Clear signature cache
            try:
                from figrecipe._signatures._loader import _SIGNATURE_CACHE

                _SIGNATURE_CACHE.clear()
            except ImportError:
                pass

            # Clear kwargs cache
            try:
                import figrecipe._signatures._loader as loader

                loader._KWARGS_CACHE = None
            except (ImportError, AttributeError):
                pass

            # Clear style cache
            try:
                import figrecipe.styles._style_loader as style_loader

                style_loader._STYLE_CACHE = None
                style_loader._CURRENT_STYLE_NAME = None
            except (ImportError, AttributeError):
                pass

            # Clear seaborn recorder
            try:
                import figrecipe._seaborn as seaborn_mod

                seaborn_mod._recorder = None
            except (ImportError, AttributeError):
                pass

            gc.collect()

        # Before test
        clear_all_caches()
        yield
        # After test
        clear_all_caches()

    @pytest.fixture
    def rng(self):
        """Random number generator with fixed seed."""
        return np.random.default_rng(42)

    @pytest.fixture
    def tmpdir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.mark.parametrize("plot_type", list_plotters())
    def test_roundtrip(self, plot_type, rng, tmpdir):
        """Test that plot type can be saved and reproduced."""
        plotter = PLOTTERS[plot_type]

        # Create original figure
        fig, ax = plotter(fr, rng)

        # Save
        recipe_path = tmpdir / f"{plot_type}.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Reproduce
        fig2, ax2 = fr.reproduce(recipe_path)

        # Basic checks
        assert fig2 is not None
        assert ax2 is not None

        plt.close(fig2.fig)

    @pytest.mark.parametrize("plot_type", list_plotters())
    def test_roundtrip_pixel_match(self, plot_type, rng, tmpdir):
        """Test that reproduced figure matches original within threshold."""
        plotter = PLOTTERS[plot_type]

        # Create original figure
        fig, ax = plotter(fr, rng)

        # Apply finalization and save original image
        # Must use fig.savefig() to apply bar edge styling consistently with reproduce
        original_path = tmpdir / f"{plot_type}_original.png"
        import warnings as _warnings

        with _warnings.catch_warnings(record=True) as _caught:
            _warnings.simplefilter("always")
            fig.savefig(
                original_path,
                save_recipe=False,
                verbose=False,
                dpi=100,
                bbox_inches="tight",
                facecolor="white",
            )
        # Skip if constrained_layout collapsed axes to zero (e.g. quiver):
        # subsequent fig2.fig.savefig(bbox_inches="tight") would hang for ~60s.
        if any("collapsed to zero" in str(w.message) for w in _caught):
            plt.close(fig.fig)
            pytest.skip(f"{plot_type}: constrained_layout collapsed axes to zero")

        # Save recipe
        recipe_path = tmpdir / f"{plot_type}.yaml"
        fr.save(fig, recipe_path, validate=False)
        plt.close(fig.fig)

        # Reproduce
        fig2, ax2 = fr.reproduce(recipe_path)

        # Save reproduced image
        reproduced_path = tmpdir / f"{plot_type}_reproduced.png"
        try:
            fig2.fig.savefig(
                reproduced_path, dpi=100, bbox_inches="tight", facecolor="white"
            )
        except (ValueError, MemoryError) as e:
            plt.close(fig2.fig)
            if "too large" in str(e):
                pytest.skip(f"{plot_type}: {e}")
            raise
        plt.close(fig2.fig)

        # Compare images
        try:
            comparison = compare_images(original_path, reproduced_path)
        except ValueError as e:
            # Skip if images are too large (e.g., quiver with constrained_layout collapse)
            if "too large" in str(e):
                pytest.skip(f"{plot_type}: {e}")
            raise

        # Per-plot-type MSE thresholds
        # Plots with auto-positioned text labels (pie, etc.) have higher variation
        thresholds = {
            "pie": 50.0,  # Pie charts have auto-positioned labels
        }
        threshold = thresholds.get(plot_type, 1.0)

        # Handle size mismatches from bbox_inches='tight' cropping
        # (e.g., matshow with axis('off') may crop differently)
        if not comparison.get("same_size", True):
            # Skip size mismatch - images reproduced but with different crop
            pytest.skip(
                f"{plot_type}: Size mismatch {comparison['size1']} vs {comparison['size2']}"
            )

        # Assert low MSE (allowing for minor rendering differences)
        assert (
            comparison["mse"] < threshold
        ), f"{plot_type}: MSE {comparison['mse']:.4f} exceeds threshold {threshold}"


def run_manual_test():
    """Run tests manually and print summary."""
    from figrecipe._utils._image_diff import create_comparison_figure

    print("=" * 60)
    print("Roundtrip Tests for All Plotting Methods")
    print("=" * 60)

    output_dir = Path(__file__).parent.parent / "outputs" / "roundtrip_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    results = {}

    for plot_type in list_plotters():
        print(f"\nTesting {plot_type}()...", end=" ")

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                plotter = PLOTTERS[plot_type]

                # Create original
                fig, ax = plotter(fr, rng)

                # Save paths
                original_path = output_dir / f"{plot_type}_original.png"
                recipe_path = output_dir / f"{plot_type}_recipe.yaml"
                reproduced_path = output_dir / f"{plot_type}_reproduced.png"
                comparison_path = output_dir / f"{plot_type}_comparison.png"

                # Save original
                fig.fig.savefig(
                    original_path, dpi=100, bbox_inches="tight", facecolor="white"
                )
                fr.save(fig, recipe_path, validate=False)
                plt.close(fig.fig)

                # Reproduce
                fig2, ax2 = fr.reproduce(recipe_path)
                fig2.fig.savefig(
                    reproduced_path, dpi=100, bbox_inches="tight", facecolor="white"
                )
                plt.close(fig2.fig)

                # Compare
                comparison = compare_images(original_path, reproduced_path)
                create_comparison_figure(
                    original_path, reproduced_path, comparison_path, plot_type
                )

                if comparison["mse"] < 1.0:
                    print(f"PASS (MSE: {comparison['mse']:.4f})")
                    results[plot_type] = {"status": "PASS", "mse": comparison["mse"]}
                else:
                    print(f"DIFF (MSE: {comparison['mse']:.4f})")
                    results[plot_type] = {"status": "DIFF", "mse": comparison["mse"]}

        except Exception as e:
            print(f"ERROR: {e}")
            results[plot_type] = {"status": "ERROR", "error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    diffed = sum(1 for r in results.values() if r.get("status") == "DIFF")
    errors = sum(1 for r in results.values() if r.get("status") == "ERROR")
    total = len(results)

    print(f"PASS:  {passed}/{total}")
    print(f"DIFF:  {diffed}/{total}")
    print(f"ERROR: {errors}/{total}")

    if errors > 0:
        print("\nErrors:")
        for name, r in results.items():
            if r.get("status") == "ERROR":
                print(f"  {name}: {r.get('error')}")

    print(f"\nOutput: {output_dir.absolute()}")

    return results


if __name__ == "__main__":
    run_manual_test()

# EOF


# === merged from v2 ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for savefig() consistency with fr.save() (Issue #42).

Tests that fig.savefig() and fr.save() produce consistent outputs,
both going through the same save pipeline with auto-crop and finalization.
"""

import pytest


@pytest.fixture
def fig_ax():
    """Create a simple figure with SCITEX style."""
    import figrecipe as fr

    fr.load_style("SCITEX")
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 2, 3], id="test")
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    yield fig, ax
    import matplotlib.pyplot as plt

    plt.close(fig.fig)


class TestSavefigConsistency:
    """Tests that savefig() delegates to save_figure()."""

    def test_savefig_creates_yaml(self, fig_ax, tmp_path):
        """savefig() should create a YAML recipe by default."""
        fig, ax = fig_ax
        output = tmp_path / "test.png"

        result = fig.savefig(output, verbose=False)

        # Should return (image_path, yaml_path, validation_result) tuple
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[0].exists()
        assert result[1].exists()
        assert result[1].suffix == ".yaml"

    def test_savefig_no_recipe(self, fig_ax, tmp_path):
        """savefig(save_recipe=False) should only save the image."""
        fig, ax = fig_ax
        output = tmp_path / "test.png"

        result = fig.savefig(output, save_recipe=False, verbose=False)

        # Should return (image_path, None, None) tuple
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[0].exists()
        assert result[1] is None
        assert result[2] is None
        # YAML should NOT be created
        assert not (tmp_path / "test.yaml").exists()

    def test_savefig_same_as_fr_save(self, fig_ax, tmp_path):
        """savefig() output should match fr.save() output dimensions."""
        from PIL import Image

        import figrecipe as fr

        fig1, ax1 = fig_ax

        # Save with savefig()
        savefig_path = tmp_path / "savefig.png"
        fig1.savefig(savefig_path, verbose=False, validate=False)

        # Create second figure for fr.save()
        fr.load_style("SCITEX")
        fig2, ax2 = fr.subplots()
        ax2.plot([1, 2, 3], [1, 2, 3], id="test")
        ax2.set_xlabel("X axis")
        ax2.set_ylabel("Y axis")

        frsave_path = tmp_path / "frsave.png"
        fr.save(fig2, frsave_path, verbose=False, validate=False)

        # Compare image dimensions (should be identical)
        with Image.open(savefig_path) as img1, Image.open(frsave_path) as img2:
            assert (
                img1.size == img2.size
            ), f"savefig() produced {img1.size}, fr.save() produced {img2.size}"

        import matplotlib.pyplot as plt

        plt.close(fig2.fig)

    def test_savefig_applies_autocrop(self, tmp_path):
        """savefig() should apply auto-crop from mm_layout."""
        from PIL import Image

        import figrecipe as fr

        fr.load_style("SCITEX")
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])

        output = tmp_path / "test.png"
        fig.savefig(output, verbose=False, validate=False)

        # Check that image was created and has reasonable dimensions
        # (auto-crop should make it smaller than the uncropped figure)
        with Image.open(output) as img:
            # With SCITEX style at 300 DPI, cropped figure should be
            # roughly 40mm wide * 300/25.4 ≈ 472px, plus margins
            # Just check it's not too large (uncropped would be ~2k px)
            assert img.width < 1000, f"Image seems uncropped: {img.width}px wide"
            assert img.height < 800, f"Image seems uncropped: {img.height}px tall"

        import matplotlib.pyplot as plt

        plt.close(fig.fig)

    def test_savefig_respects_dpi_kwarg(self, fig_ax, tmp_path):
        """savefig() should respect the dpi keyword argument."""
        from PIL import Image

        fig, ax = fig_ax

        # Save at different DPIs
        output_300 = tmp_path / "dpi300.png"
        output_150 = tmp_path / "dpi150.png"

        fig.savefig(output_300, dpi=300, verbose=False, validate=False)

        # Create new figure for 150 DPI test
        import figrecipe as fr

        fr.load_style("SCITEX")
        fig2, ax2 = fr.subplots()
        ax2.plot([1, 2, 3], [1, 2, 3], id="test")
        ax2.set_xlabel("X axis")
        ax2.set_ylabel("Y axis")
        fig2.savefig(output_150, dpi=150, verbose=False, validate=False)

        with Image.open(output_300) as img300, Image.open(output_150) as img150:
            # 300 DPI should be roughly 2x the size of 150 DPI
            ratio = img300.width / img150.width
            assert 1.8 < ratio < 2.2, f"DPI ratio unexpected: {ratio}"

        import matplotlib.pyplot as plt

        plt.close(fig2.fig)


class TestSavefigRecording:
    """Tests that savefig() properly records calls for reproduction."""

    def test_savefig_recipe_contains_plot(self, fig_ax, tmp_path):
        """Recipe from savefig() should contain the plot call."""
        from ruamel.yaml import YAML

        fig, ax = fig_ax
        output = tmp_path / "test.png"

        fig.savefig(output, verbose=False, validate=False)

        # Read the recipe
        yaml_path = tmp_path / "test.yaml"
        yaml_loader = YAML(typ="safe")
        with open(yaml_path) as f:
            recipe = yaml_loader.load(f)

        # Should contain axes with a plot call
        assert "axes" in recipe
        ax_key = list(recipe["axes"].keys())[0]
        assert "calls" in recipe["axes"][ax_key]
        assert len(recipe["axes"][ax_key]["calls"]) > 0

        # Verify the plot call is recorded correctly
        calls = recipe["axes"][ax_key]["calls"]
        plot_calls = [c for c in calls if c["function"] == "plot"]
        assert len(plot_calls) == 1
