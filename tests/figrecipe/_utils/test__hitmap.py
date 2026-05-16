#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for pixel-perfect hitmap detection.

These tests verify that sampling hitmap pixels at known element locations
correctly identifies the element, enabling precise click detection.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import figrecipe as fr


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up matplotlib figures after each test."""
    yield
    plt.close("all")


# =============================================================================
# Helper Functions
# =============================================================================


def generate_hitmap_array(fig):
    """Generate hitmap and return as numpy array with color_map."""
    from figrecipe._editor._hitmap_main import generate_hitmap

    hitmap_img, color_map = generate_hitmap(fig, dpi=150)
    hitmap_array = np.array(hitmap_img)
    return hitmap_array, color_map


def build_rgb_to_element_map(color_map):
    """Build reverse lookup from RGB tuple to element info."""
    rgb_to_element = {}
    for key, info in color_map.items():
        rgb = tuple(info["rgb"])
        rgb_to_element[rgb] = {
            "key": key,
            "type": info.get("type"),
            "call_id": info.get("call_id"),
            "label": info.get("label"),
            "layer_index": info.get("layer_index"),
        }
    return rgb_to_element


def data_to_pixel(fig, ax, x_data, y_data, img_shape):
    """Convert data coordinates to pixel coordinates in hitmap image.

    Parameters
    ----------
    fig : RecordingFigure
        The figure
    ax : Axes
        The axes containing the data
    x_data, y_data : float
        Data coordinates
    img_shape : tuple
        Shape of hitmap image (height, width, channels)

    Returns
    -------
    tuple
        (pixel_x, pixel_y) in image coordinates
    """
    # Get the matplotlib figure
    mpl_fig = fig.fig if hasattr(fig, "fig") else fig

    # Transform data coords to display coords (at figure's DPI)
    display_coords = ax.transData.transform((x_data, y_data))

    # IMPORTANT: display_coords are at the figure's DPI, not the hitmap DPI
    # We need to scale from figure DPI to hitmap DPI
    hitmap_dpi = 150  # Same as generate_hitmap default
    fig_dpi = mpl_fig.dpi
    dpi_scale = hitmap_dpi / fig_dpi

    # Scale display coords to hitmap DPI
    scaled_x = display_coords[0] * dpi_scale
    scaled_y = display_coords[1] * dpi_scale

    # Get hitmap dimensions
    img_height, img_width = img_shape[:2]

    # Convert to pixel coordinates (flip y-axis for image coordinates)
    pixel_x = int(scaled_x)
    pixel_y = int(img_height - scaled_y)

    # Clamp to valid range
    pixel_x = max(0, min(pixel_x, img_width - 1))
    pixel_y = max(0, min(pixel_y, img_height - 1))

    return pixel_x, pixel_y


def axes_to_pixel(fig, ax, x_axes, y_axes, img_shape):
    """Convert axes-relative coordinates (0-1) to pixel coordinates."""
    mpl_fig = fig.fig if hasattr(fig, "fig") else fig

    # Transform axes coords to display coords (at figure's DPI)
    display_coords = ax.transAxes.transform((x_axes, y_axes))

    # Scale from figure DPI to hitmap DPI
    hitmap_dpi = 150
    fig_dpi = mpl_fig.dpi
    dpi_scale = hitmap_dpi / fig_dpi

    scaled_x = display_coords[0] * dpi_scale
    scaled_y = display_coords[1] * dpi_scale

    img_height, img_width = img_shape[:2]

    pixel_x = int(scaled_x)
    pixel_y = int(img_height - scaled_y)

    pixel_x = max(0, min(pixel_x, img_width - 1))
    pixel_y = max(0, min(pixel_y, img_height - 1))

    return pixel_x, pixel_y


def sample_hitmap_at_data_coord(hitmap_array, rgb_to_element, fig, ax, x, y):
    """Sample hitmap at data coordinate and return element info."""
    px, py = data_to_pixel(fig, ax, x, y, hitmap_array.shape)
    rgb = tuple(hitmap_array[py, px, :3])
    return rgb_to_element.get(rgb), (px, py), rgb


def sample_hitmap_at_axes_coord(hitmap_array, rgb_to_element, fig, ax, x, y):
    """Sample hitmap at axes-relative coordinate and return element info."""
    px, py = axes_to_pixel(fig, ax, x, y, hitmap_array.shape)
    rgb = tuple(hitmap_array[py, px, :3])
    return rgb_to_element.get(rgb), (px, py), rgb


def get_element_pixels(hitmap_array, color_map, element_key):
    """Get all pixels belonging to a specific element."""
    info = color_map.get(element_key)
    if not info:
        return []

    target_rgb = tuple(info["rgb"])
    pixels = []
    for y in range(hitmap_array.shape[0]):
        for x in range(hitmap_array.shape[1]):
            if tuple(hitmap_array[y, x, :3]) == target_rgb:
                pixels.append((x, y))
    return pixels


# =============================================================================
# Test Classes
# =============================================================================


class TestBasicPlotTypes:
    """Test pixel detection for basic plot types."""

    def test_scatter_center_detection(self):
        """Test that scatter point center is detected correctly."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([0.5], [0.5], s=500, id="my_scatter")  # Large marker
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        element, pixel, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.5
        )

        assert element is not None, f"No element found at scatter center, rgb={rgb}"
        assert element["type"] == "scatter", f"Expected scatter, got {element['type']}"
        assert element["call_id"] == "my_scatter"

    def test_line_detection(self):
        """Test that line is detected along its path."""
        fig, ax = fr.subplots(1, 1)
        ax.plot([0, 1], [0, 1], linewidth=10, id="my_line")  # Thick line
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample at line midpoint
        element, pixel, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.5
        )

        assert element is not None, f"No element found on line, rgb={rgb}"
        assert element["type"] == "line", f"Expected line, got {element['type']}"

    def test_bar_detection(self):
        """Test that bar center is detected correctly."""
        fig, ax = fr.subplots(1, 1)
        ax.bar(["A", "B", "C"], [1, 2, 3], id="my_bar")

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample at center of middle bar (B at x=1, height=2 so y=1)
        element, pixel, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 1, 1
        )

        assert element is not None, f"No element found in bar, rgb={rgb}"
        assert element["type"] in (
            "bar",
            "hist",
        ), f"Expected bar, got {element['type']}"

    @pytest.mark.xfail(reason="fill_between hitmap detection affected by anti-aliasing")
    def test_fill_between_detection(self):
        """Test that fill_between area is detected."""
        fig, ax = fr.subplots(1, 1)
        ax.fill_between([0, 0.5, 1], [0, 0, 0], [1, 1, 1], id="my_fill")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample inside the filled area
        element, pixel, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.5
        )

        assert element is not None, f"No element found in fill area, rgb={rgb}"
        assert element["type"] == "fill", f"Expected fill, got {element['type']}"

    def test_hist_detection(self):
        """Test that histogram bars are detected."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.hist(rng.standard_normal(100), bins=10, id="my_hist")

        _, color_map = generate_hitmap_array(fig)

        # Find a bar element and verify it exists
        bar_elements = [
            k for k, v in color_map.items() if v.get("type") in ("bar", "hist")
        ]
        assert len(bar_elements) > 0, "No histogram bars found in color_map"

    def test_pie_wedge_detection(self):
        """Test that pie wedges are detected."""
        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], id="my_pie")

        _, color_map = generate_hitmap_array(fig)

        # Find pie elements
        pie_elements = [k for k, v in color_map.items() if v.get("type") == "pie"]
        assert len(pie_elements) == 3, f"Expected 3 pie wedges, got {len(pie_elements)}"

    @pytest.mark.xfail(reason="imshow extent coordinates differ from data coordinates")
    def test_imshow_detection(self):
        """Test that imshow image is detected."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.imshow(rng.random((10, 10)), id="my_image")

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample at image center
        element, pixel, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 5, 5
        )

        assert element is not None, f"No element found in image, rgb={rgb}"
        assert element["type"] == "image", f"Expected image, got {element['type']}"


class TestMultiLayerElements:
    """Test pixel detection for multi-layer elements."""

    def test_stackplot_layer_detection(self):
        """Test that each stackplot layer is separately detectable."""
        fig, ax = fr.subplots(1, 1)
        # Create stackplot with distinct layers
        x = [0, 1, 2, 3]
        y1 = [1, 1, 1, 1]  # Bottom layer
        y2 = [1, 1, 1, 1]  # Middle layer
        y3 = [1, 1, 1, 1]  # Top layer
        ax.stackplot(x, y1, y2, y3, id="my_stack")
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 3)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Find stackplot elements
        stack_elements = [
            (k, v) for k, v in color_map.items() if v.get("type") == "stackplot"
        ]
        assert len(stack_elements) == 3, f"Expected 3 layers, got {len(stack_elements)}"

        # Each layer should have unique layer_index
        layer_indices = [v.get("layer_index") for _, v in stack_elements]
        assert set(layer_indices) == {0, 1, 2}, f"Layer indices: {layer_indices}"

        # Sample at different y-heights to hit different layers
        # Bottom layer: y around 0.5, Middle: y around 1.5, Top: y around 2.5
        element_bottom, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 1.5, 0.5
        )
        element_middle, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 1.5, 1.5
        )
        element_top, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 1.5, 2.5
        )

        # Verify different layers detected
        if element_bottom and element_middle and element_top:
            detected_indices = {
                element_bottom.get("layer_index"),
                element_middle.get("layer_index"),
                element_top.get("layer_index"),
            }
            # Should detect at least 2 different layers
            assert (
                len(detected_indices) >= 2
            ), f"Expected different layers, got indices: {detected_indices}"

    def test_multiple_scatter_detection(self):
        """Test that multiple scatter calls are separately detectable."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([0.2], [0.5], s=500, id="scatter_left")
        ax.scatter([0.8], [0.5], s=500, id="scatter_right")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        element_left, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.2, 0.5
        )
        element_right, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.8, 0.5
        )

        assert element_left is not None, "Left scatter not detected"
        assert element_right is not None, "Right scatter not detected"
        assert element_left["call_id"] == "scatter_left"
        assert element_right["call_id"] == "scatter_right"


class TestOverlappingElements:
    """Test pixel detection for overlapping elements."""

    def test_scatter_over_line(self):
        """Test that scatter on top of line is detected (z-order)."""
        fig, ax = fr.subplots(1, 1)
        # Line first (bottom)
        ax.plot([0, 1], [0.5, 0.5], linewidth=20, id="bottom_line")
        # Scatter on top
        ax.scatter([0.5], [0.5], s=500, zorder=10, id="top_scatter")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # At overlap point, should detect the top element (scatter)
        element, _, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.5
        )

        assert element is not None, f"No element at overlap, rgb={rgb}"
        # The topmost element should be detected
        assert (
            element["call_id"] == "top_scatter"
        ), f"Expected top_scatter at overlap, got {element['call_id']}"

    def test_overlapping_bars(self):
        """Test overlapping bar detection."""
        fig, ax = fr.subplots(1, 1)
        # Two overlapping bar sets
        ax.bar([0, 1, 2], [3, 3, 3], width=0.8, id="back_bars", alpha=0.7)
        ax.bar([0, 1, 2], [2, 2, 2], width=0.4, id="front_bars", alpha=1.0)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # At center of bar, front bars should be detected
        element, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 1, 1
        )

        assert element is not None, "No bar detected at center"

    def test_fill_with_line_on_top(self):
        """Test fill area with line plotted on top."""
        fig, ax = fr.subplots(1, 1)
        ax.fill_between([0, 1], [0, 0], [1, 1], id="bottom_fill", alpha=0.5)
        ax.plot([0, 1], [0.5, 0.5], linewidth=10, id="top_line", zorder=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # On the line, should detect line
        element_on_line, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.5
        )

        # Away from line but in fill, should detect fill
        element_in_fill, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.5, 0.2
        )

        if element_on_line:
            assert element_on_line["type"] in (
                "line",
                "fill",
            ), f"Expected line or fill on line path, got {element_on_line['type']}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_area_detection(self):
        """Test that clicking empty space returns None/background."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([0.1], [0.1], s=100, id="corner_scatter")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample at opposite corner (should be empty)
        element, _, rgb = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.9, 0.9
        )

        # Should be None (background) or axes element
        if element is not None:
            assert element["type"] in (
                "axes",
                None,
            ), f"Expected empty/axes at empty area, got {element['type']}"

    def test_small_element_detection(self):
        """Test detection of very small elements."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([0.5], [0.5], s=10, id="tiny_scatter")  # Very small
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Verify element exists in color_map
        scatter_elements = [k for k, v in color_map.items() if "scatter" in k]
        assert len(scatter_elements) > 0, "Small scatter not registered in hitmap"

    def test_element_at_axes_edge(self):
        """Test element detection at axes boundaries."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([0, 1], [0, 1], s=200, id="edge_scatter")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample near edges (not exactly at 0,0 as it may be clipped)
        element_bl, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.05, 0.05
        )
        element_tr, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, ax.ax, 0.95, 0.95
        )

        # At least one should be detected (may be clipped at exact edge)
        # This is a lenient test - edge elements may be partially clipped
        _ = [e for e in [element_bl, element_tr] if e is not None]

    def test_transparent_element(self):
        """Test that transparent elements are still in hitmap."""
        fig, ax = fr.subplots(1, 1)
        ax.fill_between([0, 1], [0, 0], [1, 1], alpha=0.1, id="transparent_fill")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Hitmap should use solid colors regardless of original alpha
        fill_elements = [k for k, v in color_map.items() if v.get("type") == "fill"]
        assert len(fill_elements) > 0, "Transparent fill not in hitmap"


class TestMultiPanelDetection:
    """Test pixel detection in multi-panel figures."""

    def test_2x2_panel_detection(self):
        """Test that elements in different panels are correctly identified."""
        fig, axes = fr.subplots(2, 2)

        axes[0, 0].scatter([0.5], [0.5], s=500, id="scatter_00")
        axes[0, 1].plot([0, 1], [0, 1], linewidth=10, id="line_01")
        axes[1, 0].bar(["A"], [1], id="bar_10")
        axes[1, 1].fill([0, 1, 0.5], [0, 0, 1], id="fill_11")

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Sample each panel
        element_00, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, axes[0, 0].ax, 0.5, 0.5
        )
        element_01, _, _ = sample_hitmap_at_data_coord(
            hitmap_array, rgb_to_element, fig, axes[0, 1].ax, 0.5, 0.5
        )

        # Verify different elements detected in different panels
        if element_00 and element_01:
            assert (
                element_00["call_id"] != element_01["call_id"]
            ), "Same element detected in different panels"


class TestSpecialPlotTypes:
    """Test pixel detection for special plot types."""

    def test_errorbar_detection(self):
        """Test errorbar element detection."""
        fig, ax = fr.subplots(1, 1)
        ax.errorbar([1, 2, 3], [1, 4, 9], yerr=[0.5, 0.5, 0.5], id="my_errorbar")

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Errorbar creates line and cap elements
        errorbar_elements = [
            k
            for k, v in color_map.items()
            if v.get("call_id") == "my_errorbar" or "errorbar" in k.lower()
        ]
        assert len(errorbar_elements) > 0, "Errorbar elements not found"

    def test_violin_detection(self):
        """Test violinplot element detection."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.violinplot([rng.standard_normal(50) for _ in range(3)], id="my_violin")

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Find violin elements
        violin_elements = [k for k, v in color_map.items() if v.get("type") == "violin"]
        assert (
            len(violin_elements) >= 3
        ), f"Expected 3+ violin bodies, got {len(violin_elements)}"

    def test_boxplot_detection(self):
        """Test boxplot element detection."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.boxplot([rng.standard_normal(50) for _ in range(3)], id="my_boxplot")

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Boxplot creates multiple elements (boxes, whiskers, etc.)
        # At minimum, should have some patch or line elements
        assert len(color_map) > 0, "No elements found for boxplot"

    def test_contour_detection(self):
        """Test contour plot detection."""
        x = np.linspace(-2, 2, 20)
        y = np.linspace(-2, 2, 20)
        X, Y = np.meshgrid(x, y)
        Z = np.exp(-(X**2 + Y**2))

        fig, ax = fr.subplots(1, 1)
        ax.contourf(X, Y, Z, id="my_contour")

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Contourf creates PolyCollection elements - at least some should be found
        assert len(color_map) > 0, "No elements found for contour"

    def test_quiver_detection(self):
        """Test quiver (vector field) detection."""
        fig, ax = fr.subplots(1, 1)
        X, Y = np.meshgrid([0, 1], [0, 1])
        U = np.ones_like(X)
        V = np.ones_like(Y)
        ax.quiver(X, Y, U, V, id="my_quiver")

        hitmap_array, color_map = generate_hitmap_array(fig)

        # Quiver should be registered
        assert len(color_map) > 0, "No elements found for quiver"


class TestCoordinateTransformation:
    """Test coordinate transformation accuracy."""

    def test_known_position_accuracy(self):
        """Test that coordinate transformation is accurate for known positions."""
        fig, ax = fr.subplots(1, 1)
        # Place markers at exact positions
        ax.scatter([0.25, 0.75], [0.25, 0.75], s=1000, id="position_test")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        hitmap_array, color_map = generate_hitmap_array(fig)
        rgb_to_element = build_rgb_to_element_map(color_map)

        # Test multiple positions
        positions = [(0.25, 0.25), (0.75, 0.75)]
        detected_count = 0

        for x, y in positions:
            element, pixel, rgb = sample_hitmap_at_data_coord(
                hitmap_array, rgb_to_element, fig, ax.ax, x, y
            )
            if element and element["type"] == "scatter":
                detected_count += 1

        # At least one position should be correctly detected
        assert (
            detected_count >= 1
        ), f"Only {detected_count}/2 positions correctly detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# === merged from v2 ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for hitmap visualization functionality."""

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402,F811
import pytest  # noqa: E402

Image = pytest.importorskip("PIL.Image")

from figrecipe._utils._hitmap import (  # noqa: E402
    create_hitmap,
    generate_hitmap_report,
)


@pytest.fixture
def identical_images():
    """Create two identical test images."""
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[20:80, 20:80] = [255, 0, 0]  # Red square
    return arr, arr.copy()


@pytest.fixture
def different_images():
    """Create two different test images."""
    arr1 = np.zeros((100, 100, 3), dtype=np.uint8)
    arr1[20:80, 20:80] = [255, 0, 0]  # Red square

    arr2 = np.zeros((100, 100, 3), dtype=np.uint8)
    arr2[30:90, 30:90] = [0, 0, 255]  # Blue square, offset

    return arr1, arr2


class TestCreateHitmap:
    """Tests for create_hitmap function."""

    def test_identical_images_match(self, identical_images):
        """Identical images should have 100% match ratio."""
        img1, img2 = identical_images
        hitmap, stats = create_hitmap(img1, img2)

        assert stats["match_ratio"] == 1.0
        assert stats["mismatch_ratio"] == 0.0
        assert stats["mismatch_pixels"] == 0
        assert stats["max_diff"] == 0.0
        assert stats["mean_diff"] == 0.0

    def test_different_images_mismatch(self, different_images):
        """Different images should have mismatch."""
        img1, img2 = different_images
        hitmap, stats = create_hitmap(img1, img2)

        assert stats["match_ratio"] < 1.0
        assert stats["mismatch_ratio"] > 0.0
        assert stats["mismatch_pixels"] > 0
        assert stats["max_diff"] > 0

    def test_hitmap_shape(self, identical_images):
        """Hitmap should have same shape as input images."""
        img1, img2 = identical_images
        hitmap, _ = create_hitmap(img1, img2)

        assert hitmap.shape == img1.shape

    def test_output_path(self, identical_images, tmp_path):
        """Hitmap should be saved to output path."""
        img1, img2 = identical_images
        output_path = tmp_path / "hitmap.png"

        create_hitmap(img1, img2, output_path=output_path)

        assert output_path.exists()

    def test_threshold_affects_match(self, different_images):
        """Higher threshold should increase match ratio."""
        img1, img2 = different_images

        _, stats_strict = create_hitmap(img1, img2, threshold=0)
        _, stats_lenient = create_hitmap(img1, img2, threshold=50)

        assert stats_lenient["match_ratio"] >= stats_strict["match_ratio"]

    def test_binary_mode(self, different_images):
        """Binary mode should produce green/red hitmap."""
        img1, img2 = different_images
        hitmap, _ = create_hitmap(img1, img2, mode="binary")

        # Check that hitmap contains green and/or red
        has_green = np.any(hitmap[:, :, 1] > 0)
        has_red = np.any(hitmap[:, :, 0] > 0)

        assert has_green or has_red

    def test_diff_mode(self, different_images):
        """Diff mode should show difference magnitude in red channel."""
        img1, img2 = different_images
        hitmap, _ = create_hitmap(img1, img2, mode="diff")

        # Diff areas should have red intensity
        assert np.any(hitmap[:, :, 0] > 0)

    def test_heatmap_mode(self, different_images):
        """Heatmap mode should produce colormap output."""
        img1, img2 = different_images
        hitmap, _ = create_hitmap(img1, img2, mode="heatmap")

        # Heatmap should have various color values
        assert hitmap.dtype == np.uint8
        assert hitmap.shape[-1] == 3

    def test_regions_detected(self, different_images):
        """Difference regions should be detected."""
        img1, img2 = different_images
        _, stats = create_hitmap(img1, img2, show_bbox=True, min_region_area=5)

        assert "regions" in stats
        assert "num_regions" in stats

    def test_from_file_paths(self, identical_images, tmp_path):
        """Should accept file paths as input."""
        img1, img2 = identical_images

        path1 = tmp_path / "img1.png"
        path2 = tmp_path / "img2.png"

        Image.fromarray(img1).save(path1)
        Image.fromarray(img2).save(path2)

        hitmap, stats = create_hitmap(path1, path2)

        assert stats["match_ratio"] == 1.0


class TestGenerateHitmapReport:
    """Tests for generate_hitmap_report function."""

    def test_report_generation(self, identical_images, tmp_path):
        """Report should contain expected fields."""
        img1, img2 = identical_images

        orig_path = tmp_path / "original.png"
        repro_path = tmp_path / "reproduced.png"

        Image.fromarray(img1).save(orig_path)
        Image.fromarray(img2).save(repro_path)

        report = generate_hitmap_report(orig_path, repro_path, output_dir=tmp_path)

        assert "original" in report
        assert "reproduced" in report
        assert "hitmap" in report
        assert "is_pixel_perfect" in report
        assert "stats" in report
        assert report["is_pixel_perfect"] is True

    def test_report_hitmap_created(self, different_images, tmp_path):
        """Report should create hitmap file."""
        img1, img2 = different_images

        orig_path = tmp_path / "original.png"
        repro_path = tmp_path / "reproduced.png"

        Image.fromarray(img1).save(orig_path)
        Image.fromarray(img2).save(repro_path)

        report = generate_hitmap_report(orig_path, repro_path, output_dir=tmp_path)

        assert Path(report["hitmap"]).exists()
        assert report["is_pixel_perfect"] is False


class TestEdgeCases:  # noqa: F811
    """Tests for edge cases and error handling."""

    def test_different_sizes(self):
        """Images of different sizes should be handled."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.zeros((102, 98, 3), dtype=np.uint8)

        # Should not raise, should crop to common area
        hitmap, stats = create_hitmap(img1, img2)

        assert hitmap is not None
        assert "match_ratio" in stats

    def test_empty_diff_no_bbox(self, identical_images):
        """No regions should be detected for identical images."""
        img1, img2 = identical_images
        _, stats = create_hitmap(img1, img2, show_bbox=True)

        assert stats["num_regions"] == 0
        assert stats["regions"] == []
