#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for composition feature (Phase 1).

Tests for compose() and import_axes() functions.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe import utils
from figrecipe._wrappers import RecordingFigure


class TestCompose:
    """Tests for compose() function."""

    @pytest.fixture
    def temp_recipes(self, tmp_path):
        """Create temporary recipe files for testing."""
        # Create first figure with a line plot
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9], id="line1")
        ax1.set_xlabel("X1")
        recipe1 = tmp_path / "fig1.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        # Create second figure with a bar plot
        fig2, ax2 = fr.subplots()
        ax2.bar([1, 2, 3], [3, 1, 4], id="bar1")
        ax2.set_ylabel("Y2")
        recipe2 = tmp_path / "fig2.yaml"
        fr.save(fig2, recipe2, validate=False, verbose=False)

        return recipe1, recipe2

    def test_compose_two_figures(self, temp_recipes):
        """Compose two single-panel figures into 1x2 layout."""
        recipe1, recipe2 = temp_recipes

        fig, axes = fr.compose(
            layout=(1, 2),
            sources={
                (0, 0): recipe1,
                (0, 1): recipe2,
            },
        )

        assert fig is not None
        assert hasattr(fig, "record")
        assert len(axes) == 2

    def test_compose_creates_recording_figure(self, temp_recipes):
        """Composed figure is a RecordingFigure."""
        recipe1, recipe2 = temp_recipes

        fig, axes = fr.compose(
            layout=(1, 2),
            sources={(0, 0): recipe1, (0, 1): recipe2},
        )

        assert isinstance(fig, RecordingFigure)

    def test_compose_with_specific_axes(self, tmp_path):
        """Compose selecting specific axes from multi-panel source."""
        # Create 2x2 source figure
        fig_src, axes_src = fr.subplots(2, 2)
        axes_src[0, 0].plot([1, 2], [1, 2], id="plot_a")
        axes_src[0, 1].bar([1, 2], [2, 1], id="bar_b")
        axes_src[1, 0].scatter([1, 2], [3, 4], id="scatter_c")
        recipe = tmp_path / "multi.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Compose using specific axes
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={
                (0, 0): (recipe, "ax_0_0"),
                (0, 1): (recipe, "ax_0_1"),
            },
        )

        assert len(axes) == 2
        # Check that the correct axes were imported
        assert "ax_0_0" in fig.record.axes
        assert "ax_0_1" in fig.record.axes

    def test_compose_with_figure_record(self, tmp_path):
        """Compose using FigureRecord directly."""
        # Create and save a figure
        fig_src, ax_src = fr.subplots()
        ax_src.plot([1, 2, 3], [1, 2, 3], id="direct")
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Load as FigureRecord
        record = utils.load_recipe(recipe)

        # Compose using record directly
        fig, axes = fr.compose(
            layout=(1, 1),
            sources={(0, 0): record},
        )

        assert fig is not None
        assert "ax_0_0" in fig.record.axes

    def test_compose_invalid_axes_key_raises(self, tmp_path):
        """Compose with invalid axes key raises ValueError."""
        fig_src, ax_src = fr.subplots()
        ax_src.plot([1, 2], [1, 2])
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        with pytest.raises(ValueError, match="not found"):
            fr.compose(
                layout=(1, 1),
                sources={(0, 0): (recipe, "ax_99_99")},
            )

    def test_compose_preserves_mm_layout(self, temp_recipes):
        """Compose respects mm layout parameters."""
        recipe1, recipe2 = temp_recipes

        fig, axes = fr.compose(
            layout=(1, 2),
            sources={(0, 0): recipe1, (0, 1): recipe2},
            axes_width_mm=50,
            axes_height_mm=40,
        )

        assert fig is not None
        # Figure should have reasonable size based on mm params
        figsize = fig.fig.get_size_inches()
        assert figsize[0] > 0
        assert figsize[1] > 0


class TestImportAxes:
    """Tests for import_axes() function."""

    def test_import_into_empty_panel(self, tmp_path):
        """Import axes into existing figure's empty panel."""
        # Create source
        fig_src, ax_src = fr.subplots()
        ax_src.scatter([1, 2, 3], [1, 4, 9], id="scatter_import")
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Create target with empty second panel
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2], id="existing")

        # Import into second panel
        result = utils.import_axes(fig, (0, 1), recipe)

        assert result is not None
        assert "ax_0_1" in fig.record.axes

    def test_import_replaces_content(self, tmp_path):
        """Import replaces existing panel content."""
        # Create source
        fig_src, ax_src = fr.subplots()
        ax_src.plot([1, 2], [3, 4], id="new_line")
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Create target with existing content
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2], id="old_line")

        # Import replaces content
        utils.import_axes(fig, (0, 0), recipe)

        # Check that the imported calls are present
        calls = fig.record.axes["ax_0_0"].calls
        call_ids = [c.id for c in calls]
        assert "new_line" in call_ids

    def test_import_specific_axes(self, tmp_path):
        """Import specific axes from multi-panel source."""
        # Create multi-panel source
        fig_src, axes_src = fr.subplots(1, 2)
        axes_src[0].plot([1, 2], [1, 2], id="left_plot")
        axes_src[1].bar([1, 2], [2, 1], id="right_bar")
        recipe = tmp_path / "multi_source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Create target
        fig, ax = fr.subplots()

        # Import the second panel (ax_0_1) from source
        utils.import_axes(fig, (0, 0), recipe, source_axes="ax_0_1")

        calls = fig.record.axes["ax_0_0"].calls
        call_ids = [c.id for c in calls]
        assert "right_bar" in call_ids

    def test_import_from_figure_record(self, tmp_path):
        """Import from FigureRecord object."""
        # Create and save source
        fig_src, ax_src = fr.subplots()
        ax_src.plot([1, 2, 3], [3, 2, 1], id="from_record")
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        # Load as record
        record = utils.load_recipe(recipe)

        # Create target and import
        fig, ax = fr.subplots()
        utils.import_axes(fig, (0, 0), record)

        calls = fig.record.axes["ax_0_0"].calls
        call_ids = [c.id for c in calls]
        assert "from_record" in call_ids

    def test_import_invalid_source_raises(self):
        """Import with invalid source type raises TypeError."""
        fig, ax = fr.subplots()

        with pytest.raises(TypeError):
            utils.import_axes(fig, (0, 0), 12345)  # Invalid source

    def test_import_missing_axes_raises(self, tmp_path):
        """Import with missing source axes raises ValueError."""
        fig_src, ax_src = fr.subplots()
        ax_src.plot([1, 2], [1, 2])
        recipe = tmp_path / "source.yaml"
        fr.save(fig_src, recipe, validate=False, verbose=False)

        fig, ax = fr.subplots()

        with pytest.raises(ValueError, match="not found"):
            utils.import_axes(fig, (0, 0), recipe, source_axes="ax_99_99")


class TestComposeAndSave:
    """Integration tests for compose + save workflow."""

    def test_compose_save_reproduce(self, tmp_path):
        """Composed figure can be saved and reproduced."""
        # Create source figures
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9], id="source1")
        recipe1 = tmp_path / "src1.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        fig2, ax2 = fr.subplots()
        ax2.bar([1, 2, 3], [3, 1, 4], id="source2")
        recipe2 = tmp_path / "src2.yaml"
        fr.save(fig2, recipe2, validate=False, verbose=False)

        # Compose
        composed_fig, axes = fr.compose(
            layout=(1, 2),
            sources={(0, 0): recipe1, (0, 1): recipe2},
        )

        # Save composed figure
        composed_recipe = tmp_path / "composed.yaml"
        fr.save(composed_fig, composed_recipe, validate=False, verbose=False)

        # Reproduce
        repro_fig, repro_axes = fr.reproduce(composed_recipe)

        assert repro_fig is not None
        assert "ax_0_0" in repro_fig.record.axes
        assert "ax_0_1" in repro_fig.record.axes


class TestPanelVisibility:
    """Tests for hide/show/toggle panel functions (Phase 2)."""

    def test_hide_panel(self):
        """Hidden panel not visible but data preserved."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2], id="left")
        axes[1].bar([1, 2], [2, 1], id="right")

        utils.hide_panel(fig, (0, 1))

        # Check visibility flag in record
        assert not fig.record.axes["ax_0_1"].visible

        # Check matplotlib axes visibility
        assert not axes[1]._ax.get_visible()

        # Data should still be preserved
        assert len(fig.record.axes["ax_0_1"].calls) > 0

    def test_show_panel(self):
        """Show restores visibility."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])  # Add content to create axes record

        utils.hide_panel(fig, (0, 1))
        assert not fig.record.axes["ax_0_1"].visible

        utils.show_panel(fig, (0, 1))
        assert fig.record.axes["ax_0_1"].visible
        assert axes[1]._ax.get_visible()

    def test_toggle_panel(self):
        """Toggle switches visibility state."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        # First toggle: visible -> hidden
        result1 = utils.toggle_panel(fig, (0, 0))
        assert result1 is False  # Now hidden
        assert not fig.record.axes["ax_0_0"].visible

        # Second toggle: hidden -> visible
        result2 = utils.toggle_panel(fig, (0, 0))
        assert result2 is True  # Now visible
        assert fig.record.axes["ax_0_0"].visible

    def test_toggle_nonexistent_panel(self):
        """Toggle on nonexistent panel returns False."""
        fig, ax = fr.subplots()
        result = utils.toggle_panel(fig, (99, 99))
        assert result is False

    def test_visibility_serialization(self, tmp_path):
        """Visibility state persists in recipe."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2], id="visible_plot")
        axes[1].bar([1, 2], [2, 1], id="hidden_bar")

        utils.hide_panel(fig, (0, 1))

        recipe = tmp_path / "hidden.yaml"
        fr.save(fig, recipe, validate=False, verbose=False)

        # Reproduce and check
        fig2, axes2 = fr.reproduce(recipe)
        assert fig2.record.axes["ax_0_0"].visible is True
        assert fig2.record.axes["ax_0_1"].visible is False

    def test_hidden_panel_not_rendered(self, tmp_path):
        """Hidden panels are skipped during reproduction."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [3, 4])

        utils.hide_panel(fig, (0, 1))

        recipe = tmp_path / "hidden.yaml"
        fr.save(fig, recipe, validate=False, verbose=False)

        # Reproduce
        fig2, axes2 = fr.reproduce(recipe)

        # Hidden panel should not be visible
        mpl_ax = axes2[1]._ax if hasattr(axes2[1], "_ax") else axes2[1]
        assert not mpl_ax.get_visible()

    def test_hide_multiple_panels(self):
        """Can hide multiple panels."""
        fig, axes = fr.subplots(2, 2)
        for i in range(2):
            for j in range(2):
                axes[i, j].plot([1, 2], [i + j, i + j + 1])

        utils.hide_panel(fig, (0, 1))
        utils.hide_panel(fig, (1, 0))

        assert fig.record.axes["ax_0_0"].visible is True
        assert fig.record.axes["ax_0_1"].visible is False
        assert fig.record.axes["ax_1_0"].visible is False
        assert fig.record.axes["ax_1_1"].visible is True


class TestVisibilityWithComposition:
    """Integration tests for visibility with composition."""

    def test_compose_then_hide(self, tmp_path):
        """Can hide panels after composition."""
        # Create sources
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2], [1, 2], id="src1")
        recipe1 = tmp_path / "src1.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        fig2, ax2 = fr.subplots()
        ax2.bar([1, 2], [2, 1], id="src2")
        recipe2 = tmp_path / "src2.yaml"
        fr.save(fig2, recipe2, validate=False, verbose=False)

        # Compose
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={(0, 0): recipe1, (0, 1): recipe2},
        )

        # Hide one panel
        utils.hide_panel(fig, (0, 1))

        assert fig.record.axes["ax_0_0"].visible is True
        assert fig.record.axes["ax_0_1"].visible is False

    def test_compose_hide_save_reproduce(self, tmp_path):
        """Full workflow: compose, hide, save, reproduce."""
        # Create source
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9], id="data")
        recipe1 = tmp_path / "src.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        # Compose into 2x2 with only one source
        fig, axes = fr.compose(
            layout=(2, 2),
            sources={(0, 0): recipe1},
        )

        # Hide empty panels
        utils.hide_panel(fig, (0, 1))
        utils.hide_panel(fig, (1, 0))
        utils.hide_panel(fig, (1, 1))

        # Save
        output = tmp_path / "composed.yaml"
        fr.save(fig, output, validate=False, verbose=False)

        # Reproduce
        fig2, axes2 = fr.reproduce(output)

        # Check visibility states
        assert fig2.record.axes["ax_0_0"].visible is True
        assert (
            fig2.record.axes.get("ax_0_1", None) is None
            or not fig2.record.axes["ax_0_1"].visible
        )


class TestComposeRawImages:
    """Tests for compose() with raw image files (Issue #75)."""

    @pytest.fixture
    def temp_image(self, tmp_path):
        """Create a temporary test image."""
        import numpy as np
        from PIL import Image

        # Create a simple test image (100x100 RGB)
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        img_array[:50, :, 0] = 255  # Red top half
        img_array[50:, :, 2] = 255  # Blue bottom half

        img_path = tmp_path / "test_image.png"
        img = Image.fromarray(img_array)
        img.save(img_path)

        return img_path

    @pytest.fixture
    def temp_jpg_image(self, tmp_path):
        """Create a temporary JPG test image."""
        import numpy as np
        from PIL import Image

        # Create a simple test image (80x120 RGB)
        img_array = np.zeros((80, 120, 3), dtype=np.uint8)
        img_array[:, :60, 1] = 255  # Green left half

        img_path = tmp_path / "test_image.jpg"
        img = Image.fromarray(img_array)
        img.save(img_path)

        return img_path

    def test_compose_single_raw_image(self, temp_image):
        """Compose a single raw image."""
        fig, ax = fr.compose(
            layout=(1, 1),
            sources={(0, 0): temp_image},
        )

        assert fig is not None
        assert hasattr(fig, "record")
        assert "ax_0_0" in fig.record.axes
        # Check that imshow call was created
        calls = fig.record.axes["ax_0_0"].calls
        assert len(calls) == 1
        assert calls[0].function == "imshow"

    def test_compose_multiple_raw_images(self, temp_image, temp_jpg_image):
        """Compose multiple raw images."""
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={
                (0, 0): temp_image,
                (0, 1): temp_jpg_image,
            },
        )

        assert fig is not None
        assert len(axes) == 2
        assert "ax_0_0" in fig.record.axes
        assert "ax_0_1" in fig.record.axes

    def test_compose_mixed_recipe_and_image(self, tmp_path, temp_image):
        """Compose mixing recipe files and raw images."""
        # Create a recipe file
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9], id="line1")
        recipe_path = tmp_path / "plot.yaml"
        fr.save(fig1, recipe_path, validate=False, verbose=False)

        # Compose with mixed sources
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={
                (0, 0): temp_image,  # Raw image
                (0, 1): recipe_path,  # Recipe file
            },
        )

        assert fig is not None
        assert len(axes) == 2

        # Check image panel
        img_calls = fig.record.axes["ax_0_0"].calls
        assert img_calls[0].function == "imshow"

        # Check recipe panel
        plot_calls = fig.record.axes["ax_0_1"].calls
        assert plot_calls[0].function == "plot"

    def test_compose_raw_image_has_axis_off(self, temp_image):
        """Raw images should have axis turned off."""
        fig, ax = fr.compose(
            layout=(1, 1),
            sources={(0, 0): temp_image},
        )

        # Check that axis_off decoration was added
        decorations = fig.record.axes["ax_0_0"].decorations
        axis_funcs = [d.function for d in decorations]
        assert "axis" in axis_funcs

    def test_compose_raw_image_preserves_aspect(self, temp_image):
        """Raw images should preserve aspect ratio."""
        fig, ax = fr.compose(
            layout=(1, 1),
            sources={(0, 0): temp_image},
        )

        # Check imshow was called with aspect='equal'
        imshow_call = fig.record.axes["ax_0_0"].calls[0]
        assert imshow_call.kwargs.get("aspect") == "equal"

    def test_compose_save_and_reproduce_with_image(self, tmp_path, temp_image):
        """Composed figure with raw image can be saved and reproduced."""
        # Create a recipe
        fig1, ax1 = fr.subplots()
        ax1.bar([1, 2, 3], [3, 1, 4], id="bar1")
        recipe_path = tmp_path / "bar.yaml"
        fr.save(fig1, recipe_path, validate=False, verbose=False)

        # Compose with mixed sources
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={
                (0, 0): temp_image,
                (0, 1): recipe_path,
            },
        )

        # Save composed figure
        output_path = tmp_path / "composed.yaml"
        fr.save(fig, output_path, validate=False, verbose=False)

        # Reproduce
        fig2, axes2 = fr.reproduce(output_path)

        assert fig2 is not None
        assert "ax_0_0" in fig2.record.axes
        assert "ax_0_1" in fig2.record.axes

    def test_compose_image_grid_layout(self, tmp_path):
        """Compose images in a 2x2 grid layout."""
        import numpy as np
        from PIL import Image

        # Create 4 different colored test images
        images = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        for i, color in enumerate(colors):
            img_array = np.full((50, 50, 3), color, dtype=np.uint8)
            img_path = tmp_path / f"img_{i}.png"
            Image.fromarray(img_array).save(img_path)
            images.append(img_path)

        # Compose in 2x2 grid
        fig, axes = fr.compose(
            layout=(2, 2),
            sources={
                (0, 0): images[0],
                (0, 1): images[1],
                (1, 0): images[2],
                (1, 1): images[3],
            },
        )

        assert fig is not None
        assert axes.shape == (2, 2)
        for i in range(2):
            for j in range(2):
                ax_key = f"ax_{i}_{j}"
                assert ax_key in fig.record.axes
                assert fig.record.axes[ax_key].calls[0].function == "imshow"

    def test_is_image_file_detection(self):
        """Test image file extension detection."""
        from pathlib import Path

        from figrecipe._composition._source_parser import (
            is_image_file as _is_image_file,
        )

        # Should be detected as images
        assert _is_image_file(Path("test.png"))
        assert _is_image_file(Path("test.PNG"))
        assert _is_image_file(Path("test.jpg"))
        assert _is_image_file(Path("test.jpeg"))
        assert _is_image_file(Path("test.JPEG"))
        assert _is_image_file(Path("test.tiff"))
        assert _is_image_file(Path("test.bmp"))
        assert _is_image_file(Path("test.gif"))
        assert _is_image_file(Path("test.webp"))
        assert _is_image_file(Path("test.svg"))

        # Should NOT be detected as images
        assert not _is_image_file(Path("test.yaml"))
        assert not _is_image_file(Path("test.yml"))
        assert not _is_image_file(Path("test.txt"))
        assert not _is_image_file(Path("test.py"))
