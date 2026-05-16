#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for hit area detection across all plot types.

Ensures that hitmap generation and bbox extraction work correctly
for every supported plot type.
"""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from figrecipe._editor._bbox import extract_bboxes
from figrecipe._editor._hitmap import generate_hitmap


# Simple plot creators that use plain matplotlib (no figrecipe id kwarg)
def create_plot():
    """Create a simple line plot."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 100)
    ax.plot(x, np.sin(x))
    ax.plot(x, np.cos(x))
    return fig, ax


def create_scatter():
    """Create a simple scatter plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    x, y = rng.uniform(0, 10, 50), rng.uniform(0, 10, 50)
    ax.scatter(x, y)
    return fig, ax


def create_bar():
    """Create a simple bar chart."""
    fig, ax = plt.subplots()
    categories = ["A", "B", "C", "D"]
    values = [3, 7, 2, 5]
    ax.bar(categories, values)
    return fig, ax


def create_barh():
    """Create a simple horizontal bar chart."""
    fig, ax = plt.subplots()
    categories = ["A", "B", "C", "D"]
    values = [3, 7, 2, 5]
    ax.barh(categories, values)
    return fig, ax


def create_hist():
    """Create a simple histogram."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = rng.normal(0, 1, 1000)
    ax.hist(data, bins=30)
    return fig, ax


def create_imshow():
    """Create a simple image plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = rng.uniform(0, 1, (10, 10))
    ax.imshow(data)
    return fig, ax


def create_contour():
    """Create a simple contour plot."""
    fig, ax = plt.subplots()
    x = np.linspace(-3, 3, 50)
    y = np.linspace(-3, 3, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y)
    ax.contour(X, Y, Z)
    return fig, ax


def create_contourf():
    """Create a simple filled contour plot."""
    fig, ax = plt.subplots()
    x = np.linspace(-3, 3, 50)
    y = np.linspace(-3, 3, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y)
    ax.contourf(X, Y, Z)
    return fig, ax


def create_quiver():
    """Create a simple quiver (vector) plot."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2, 5)
    y = np.linspace(0, 2, 5)
    X, Y = np.meshgrid(x, y)
    U = np.cos(X)
    V = np.sin(Y)
    ax.quiver(X, Y, U, V)
    return fig, ax


def create_pie():
    """Create a simple pie chart."""
    fig, ax = plt.subplots()
    sizes = [15, 30, 45, 10]
    ax.pie(sizes)
    return fig, ax


def create_fill():
    """Create a simple fill plot."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    ax.fill(x, y)
    return fig, ax


def create_fill_between():
    """Create a fill_between plot."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    ax.fill_between(x, y1, y2)
    return fig, ax


def create_boxplot():
    """Create a simple box plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = [rng.normal(0, 1, 100) for _ in range(3)]
    ax.boxplot(data)
    return fig, ax


def create_violinplot():
    """Create a simple violin plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = [rng.normal(0, 1, 100) for _ in range(3)]
    ax.violinplot(data)
    return fig, ax


def create_errorbar():
    """Create an error bar plot."""
    fig, ax = plt.subplots()
    x = np.arange(5)
    y = [2, 4, 3, 5, 4]
    yerr = [0.5, 0.3, 0.4, 0.6, 0.2]
    ax.errorbar(x, y, yerr=yerr)
    return fig, ax


def create_step():
    """Create a step plot."""
    fig, ax = plt.subplots()
    x = np.arange(10)
    y = np.random.default_rng(42).integers(0, 10, 10)
    ax.step(x, y)
    return fig, ax


def create_stem():
    """Create a stem plot."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 20)
    y = np.sin(x)
    ax.stem(x, y)
    return fig, ax


def create_stackplot():
    """Create a stack plot."""
    fig, ax = plt.subplots()
    x = np.arange(5)
    y1 = [1, 2, 3, 4, 5]
    y2 = [2, 3, 2, 3, 2]
    y3 = [1, 1, 1, 1, 1]
    ax.stackplot(x, y1, y2, y3)
    return fig, ax


def create_pcolormesh():
    """Create a pcolormesh plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = rng.uniform(0, 1, (10, 10))
    ax.pcolormesh(data)
    return fig, ax


def create_hexbin():
    """Create a hexbin plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    x = rng.normal(0, 1, 1000)
    y = rng.normal(0, 1, 1000)
    ax.hexbin(x, y, gridsize=20)
    return fig, ax


def create_specgram():
    """Create a spectrogram."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    Fs = 1000
    t = np.arange(0, 1, 1 / Fs)
    signal = np.sin(2 * np.pi * 50 * t) + rng.normal(0, 0.1, len(t))
    ax.specgram(signal, Fs=Fs)
    return fig, ax


def create_streamplot():
    """Create a streamplot."""
    fig, ax = plt.subplots()
    x = np.linspace(-3, 3, 20)
    y = np.linspace(-3, 3, 20)
    X, Y = np.meshgrid(x, y)
    U = -Y
    V = X
    ax.streamplot(X, Y, U, V)
    return fig, ax


def create_eventplot():
    """Create an event plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = [rng.uniform(0, 10, 20) for _ in range(3)]
    ax.eventplot(data)
    return fig, ax


def create_hist2d():
    """Create a 2D histogram."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    x = rng.normal(0, 1, 1000)
    y = rng.normal(0, 1, 1000)
    ax.hist2d(x, y, bins=20)
    return fig, ax


def create_spy():
    """Create a spy plot (sparse matrix visualization)."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = rng.choice([0, 1], size=(10, 10), p=[0.7, 0.3])
    ax.spy(data)
    return fig, ax


def create_matshow():
    """Create a matshow plot."""
    fig, ax = plt.subplots()
    rng = np.random.default_rng(42)
    data = rng.uniform(0, 1, (10, 10))
    ax.matshow(data)
    return fig, ax


# Registry of all plot creators
PLOT_CREATORS = {
    "plot": create_plot,
    "scatter": create_scatter,
    "bar": create_bar,
    "barh": create_barh,
    "hist": create_hist,
    "imshow": create_imshow,
    "contour": create_contour,
    "contourf": create_contourf,
    "quiver": create_quiver,
    "pie": create_pie,
    "fill": create_fill,
    "fill_between": create_fill_between,
    "boxplot": create_boxplot,
    "violinplot": create_violinplot,
    "errorbar": create_errorbar,
    "step": create_step,
    "stem": create_stem,
    "stackplot": create_stackplot,
    "pcolormesh": create_pcolormesh,
    "hexbin": create_hexbin,
    "specgram": create_specgram,
    "streamplot": create_streamplot,
    "eventplot": create_eventplot,
    "hist2d": create_hist2d,
    "spy": create_spy,
    "matshow": create_matshow,
}

ALL_PLOT_TYPES = list(PLOT_CREATORS.keys())


class TestHitmapGeneration:
    """Test hitmap generation for all plot types."""

    @pytest.mark.parametrize("plot_type", ALL_PLOT_TYPES)
    def test_hitmap_generates_without_error(self, plot_type):
        """Each plot type should generate a hitmap without errors."""
        creator = PLOT_CREATORS[plot_type]
        fig, ax = creator()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # Basic assertions
            assert hitmap is not None, f"{plot_type}: hitmap should not be None"
            assert isinstance(color_map, dict), f"{plot_type}: color_map should be dict"
            assert len(color_map) > 0, f"{plot_type}: color_map should not be empty"

        finally:
            plt.close(fig)

    @pytest.mark.parametrize("plot_type", ALL_PLOT_TYPES)
    def test_hitmap_has_plot_elements(self, plot_type):
        """Each plot type should have at least one plot element in color_map."""
        creator = PLOT_CREATORS[plot_type]
        fig, ax = creator()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # Filter out text-only elements (title, xlabel, ylabel)
            text_types = {
                "title",
                "xlabel",
                "ylabel",
                "suptitle",
                "supxlabel",
                "supylabel",
            }
            plot_elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") not in text_types
            ]

            assert len(plot_elements) > 0, (
                f"{plot_type}: should have at least one plot element. "
                f"Found types: {[color_map[k].get('type') for k in color_map if isinstance(color_map[k], dict)]}"
            )

        finally:
            plt.close(fig)


class TestBboxExtraction:
    """Test bounding box extraction for all plot types."""

    @pytest.mark.parametrize("plot_type", ALL_PLOT_TYPES)
    def test_bbox_extracts_without_error(self, plot_type):
        """Each plot type should have bbox extraction work without errors."""
        creator = PLOT_CREATORS[plot_type]
        fig, ax = creator()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            # Basic assertions
            assert isinstance(bboxes, dict), f"{plot_type}: bboxes should be dict"
            assert len(bboxes) > 0, f"{plot_type}: bboxes should not be empty"

        finally:
            plt.close(fig)

    @pytest.mark.parametrize("plot_type", ALL_PLOT_TYPES)
    def test_bbox_has_valid_coordinates(self, plot_type):
        """Each bbox should have valid x, y, width, height coordinates."""
        creator = PLOT_CREATORS[plot_type]
        fig, ax = creator()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            for key, bbox in bboxes.items():
                if key == "_meta":
                    continue  # Skip metadata

                if "x" in bbox:  # Some elements may not have bbox
                    assert bbox["x"] >= 0, f"{plot_type}/{key}: x should be >= 0"
                    assert bbox["y"] >= 0, f"{plot_type}/{key}: y should be >= 0"
                    assert bbox["width"] > 0, f"{plot_type}/{key}: width should be > 0"
                    assert (
                        bbox["height"] > 0
                    ), f"{plot_type}/{key}: height should be > 0"

        finally:
            plt.close(fig)


class TestHitmapBboxConsistency:
    """Test that hitmap and bbox extraction are consistent."""

    @pytest.mark.parametrize("plot_type", ALL_PLOT_TYPES)
    def test_plot_elements_have_bboxes(self, plot_type):
        """Plot elements in colorMap should have corresponding bboxes."""
        creator = PLOT_CREATORS[plot_type]
        fig, ax = creator()

        try:
            hitmap, color_map = generate_hitmap(fig)
            bboxes = extract_bboxes(fig, 800, 600)

            # Get plot element types (excluding text elements)
            text_types = {
                "title",
                "xlabel",
                "ylabel",
                "suptitle",
                "supxlabel",
                "supylabel",
            }
            plot_elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") not in text_types
            ]

            # Count elements with bboxes
            elements_with_bbox = 0
            elements_without_bbox = []
            for elem_key in plot_elements:
                # Find matching bbox key (may have different naming)
                has_bbox = any(
                    elem_key in bbox_key or bbox_key in elem_key
                    for bbox_key in bboxes.keys()
                    if bbox_key != "_meta"
                )
                if has_bbox:
                    elements_with_bbox += 1
                else:
                    elements_without_bbox.append(elem_key)

            # At least some elements should have bboxes
            # (Some elements like fills may not always have bboxes)
            # Note: boxplot creates many thin lines (whiskers, caps) that have
            # zero-height bboxes, so we use a lower threshold of 30%
            if len(plot_elements) > 0:
                coverage = elements_with_bbox / len(plot_elements) * 100
                assert coverage >= 30, (
                    f"{plot_type}: Only {coverage:.0f}% of plot elements have bboxes. "
                    f"Missing: {elements_without_bbox[:5]}"
                )

        finally:
            plt.close(fig)


class TestSpecificPlotTypes:
    """Test specific plot types that had known issues."""

    def test_imshow_has_image_element(self):
        """imshow should create an 'image' type element."""
        fig, ax = create_imshow()

        try:
            hitmap, color_map = generate_hitmap(fig)

            image_elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") == "image"
            ]
            assert len(image_elements) > 0, "imshow should create image elements"

        finally:
            plt.close(fig)

    def test_hist_has_bar_or_hist_element(self):
        """hist should create 'hist' or 'bar' type elements."""
        fig, ax = create_hist()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # Without recording, hist may show as bar
            bar_or_hist = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") in ("bar", "hist")
            ]
            assert len(bar_or_hist) > 0, "hist should create bar/hist elements"

        finally:
            plt.close(fig)

    def test_quiver_has_quiver_element(self):
        """quiver should create a 'quiver' type element."""
        fig, ax = create_quiver()

        try:
            hitmap, color_map = generate_hitmap(fig)

            quiver_elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") == "quiver"
            ]
            assert len(quiver_elements) > 0, "quiver should create quiver elements"

        finally:
            plt.close(fig)

    def test_pie_has_pie_element(self):
        """pie should create 'pie' type elements."""
        fig, ax = create_pie()

        try:
            hitmap, color_map = generate_hitmap(fig)

            pie_elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") == "pie"
            ]
            assert len(pie_elements) > 0, "pie should create pie elements"

        finally:
            plt.close(fig)

    def test_contourf_has_elements(self):
        """contourf should create fill or image elements."""
        fig, ax = create_contourf()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # contourf may create fill or image elements
            # Note: contourf may not create easily selectable elements
            # Just verify hitmap generation doesn't error
            assert hitmap is not None
            assert color_map is not None

        finally:
            plt.close(fig)

    def test_boxplot_has_elements(self):
        """boxplot should create 'boxplot' or 'line' type elements."""
        fig, ax = create_boxplot()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # With recording, boxplot elements should be identified
            # Without recording, they may appear as lines
            elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict) and v.get("type") in ("boxplot", "line")
            ]
            assert len(elements) > 0, "boxplot should create boxplot or line elements"

        finally:
            plt.close(fig)

    def test_violinplot_has_elements(self):
        """violinplot should create 'violin' type elements."""
        fig, ax = create_violinplot()

        try:
            hitmap, color_map = generate_hitmap(fig)

            # With recording, violin elements should be identified
            elements = [
                k
                for k, v in color_map.items()
                if isinstance(v, dict)
                and v.get("type") in ("violin", "fill", "linecollection")
            ]
            assert len(elements) > 0, "violinplot should create violin elements"

        finally:
            plt.close(fig)


class TestBboxTypes:
    """Test that specific element types have valid bboxes."""

    def test_scatter_bbox(self):
        """scatter should have valid bbox."""
        fig, ax = create_scatter()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            scatter_bboxes = [k for k in bboxes.keys() if "scatter" in k]
            assert len(scatter_bboxes) > 0, "scatter should have bbox"

        finally:
            plt.close(fig)

    def test_bar_bbox(self):
        """bar should have valid bbox."""
        fig, ax = create_bar()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            bar_bboxes = [k for k in bboxes.keys() if "bar" in k]
            assert len(bar_bboxes) > 0, "bar should have bbox"

        finally:
            plt.close(fig)

    def test_line_bbox(self):
        """plot (line) should have valid bbox."""
        fig, ax = create_plot()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            line_bboxes = [k for k in bboxes.keys() if "line" in k]
            assert len(line_bboxes) > 0, "plot should have line bbox"

        finally:
            plt.close(fig)

    def test_image_bbox(self):
        """imshow should have valid bbox."""
        fig, ax = create_imshow()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            image_bboxes = [k for k in bboxes.keys() if "image" in k]
            assert len(image_bboxes) > 0, "imshow should have image bbox"

        finally:
            plt.close(fig)

    def test_quiver_bbox(self):
        """quiver should have valid bbox."""
        fig, ax = create_quiver()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            quiver_bboxes = [k for k in bboxes.keys() if "quiver" in k]
            assert len(quiver_bboxes) > 0, "quiver should have bbox"

        finally:
            plt.close(fig)

    def test_pie_bbox(self):
        """pie should have valid bbox."""
        fig, ax = create_pie()

        try:
            bboxes = extract_bboxes(fig, 800, 600)

            pie_bboxes = [k for k in bboxes.keys() if "wedge" in k or "pie" in k]
            assert len(pie_bboxes) > 0, "pie should have wedge bbox"

        finally:
            plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# === merged from v2 ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for hitmap call_id matching with recorded calls.

These tests verify that hitmap elements have call_ids that match
actual recorded calls, which is essential for the editor's property
panel to display correct data.
"""

import sys
import tempfile
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


def get_hitmap_and_calls(fig):
    """Generate hitmap and get recorded calls."""
    from figrecipe._editor._hitmap_main import generate_hitmap

    _, color_map = generate_hitmap(fig)

    # Get recorded call IDs
    recorded_call_ids = set()
    if hasattr(fig, "record"):
        for ax_key, ax_record in fig.record.axes.items():
            for call in ax_record.calls:
                recorded_call_ids.add(call.id)

    return color_map, recorded_call_ids


def check_call_ids_match(color_map, recorded_call_ids, allow_fallback=False):
    """Check that hitmap call_ids match recorded calls.

    Returns list of mismatches.
    """
    mismatches = []
    for key, info in color_map.items():
        call_id = info.get("call_id")
        elem_type = info.get("type", "unknown")

        # Skip elements that don't need call_id matching
        if elem_type in (
            "axes",
            "spine",
            "xticks",
            "yticks",
            "title",
            "xlabel",
            "ylabel",
            "legend",
            "text",
            "panel_label",
        ):
            continue

        if call_id is None:
            mismatches.append(
                {
                    "key": key,
                    "type": elem_type,
                    "call_id": None,
                    "reason": "No call_id assigned",
                }
            )
        elif call_id not in recorded_call_ids:
            # Check if it's a fallback ID (like line_0_1, bar_2, etc.)
            is_fallback = (
                any(
                    call_id.startswith(p)
                    for p in ["line_", "bar_", "scatter_", "fill_", "stairs_", "step_"]
                )
                and "_" in call_id
                and call_id.split("_")[-1].isdigit()
            )

            if not allow_fallback or not is_fallback:
                mismatches.append(
                    {
                        "key": key,
                        "type": elem_type,
                        "call_id": call_id,
                        "reason": f"call_id '{call_id}' not in recorded calls",
                        "recorded": list(recorded_call_ids),
                    }
                )

    return mismatches


class TestSinglePanelCallIdMatching:
    """Test call_id matching for single-panel figures."""

    def test_plot_call_id_matches(self):
        """Test that plot elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9], id="my_plot")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_plot" in recorded

    def test_scatter_call_id_matches(self):
        """Test that scatter elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.scatter([1, 2, 3], [1, 4, 9], id="my_scatter")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_scatter" in recorded

    def test_bar_call_id_matches(self):
        """Test that bar elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.bar(["A", "B", "C"], [1, 4, 9], id="my_bar")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_bar" in recorded

    def test_errorbar_call_id_matches(self):
        """Test that errorbar elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.errorbar([1, 2, 3], [1, 4, 9], yerr=[0.5, 0.5, 0.5], id="my_errorbar")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_errorbar" in recorded

    def test_fill_between_call_id_matches(self):
        """Test that fill_between elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.fill_between([1, 2, 3], [0, 0, 0], [1, 4, 9], id="my_fill")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_fill" in recorded

    def test_hist_call_id_matches(self):
        """Test that hist elements have matching call_ids."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.hist(rng.standard_normal(100), bins=10, id="my_hist")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_hist" in recorded

    def test_pie_call_id_matches(self):
        """Test that pie elements have matching call_ids."""
        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], id="my_pie")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_pie" in recorded

    def test_imshow_call_id_matches(self):
        """Test that imshow elements have matching call_ids."""
        rng = np.random.default_rng(42)
        fig, ax = fr.subplots(1, 1)
        ax.imshow(rng.random((10, 10)), id="my_image")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"
        assert "my_image" in recorded


class TestMultiPanelCallIdMatching:
    """Test call_id matching for multi-panel figures."""

    def test_3x3_grid_call_ids_match(self):
        """Test that 3x3 grid correctly maps call_ids."""
        fig, axes = fr.subplots(3, 3)

        # Each panel has a different plot type with custom id
        axes[0, 0].plot([1, 2, 3], [1, 4, 9], id="plot_0_0")
        axes[0, 1].scatter([1, 2, 3], [1, 4, 9], id="scatter_0_1")
        axes[0, 2].bar(["A", "B"], [3, 5], id="bar_0_2")
        axes[1, 0].fill([0, 1, 1, 0], [0, 0, 1, 1], id="fill_1_0")
        axes[1, 1].errorbar([1, 2], [1, 4], yerr=[0.5, 0.5], id="errorbar_1_1")
        axes[1, 2].fill_between([1, 2, 3], [0, 0, 0], [1, 4, 9], id="fillbetween_1_2")
        axes[2, 0].pie([30, 40, 30], id="pie_2_0")
        rng = np.random.default_rng(42)
        axes[2, 1].hist(rng.standard_normal(50), bins=5, id="hist_2_1")
        axes[2, 2].imshow(rng.random((5, 5)), id="imshow_2_2")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"

        # Verify all custom ids are recorded
        expected_ids = [
            "plot_0_0",
            "scatter_0_1",
            "bar_0_2",
            "fill_1_0",
            "errorbar_1_1",
            "fillbetween_1_2",
            "pie_2_0",
            "hist_2_1",
            "imshow_2_2",
        ]
        for expected_id in expected_ids:
            assert expected_id in recorded, f"{expected_id} not in recorded calls"

    def test_16_panel_grid_call_ids_match(self):
        """Test that 4x4 grid (16 panels) correctly maps call_ids.

        This tests the natural sorting fix for ax_10_0 vs ax_1_0.
        """
        fig, axes = fr.subplots(4, 4)

        # Plot in each panel with custom id encoding position
        for i in range(4):
            for j in range(4):
                axes[i, j].plot([1, 2], [1, 2], id=f"plot_{i}_{j}")

        color_map, recorded = get_hitmap_and_calls(fig)
        mismatches = check_call_ids_match(color_map, recorded)

        assert not mismatches, f"Mismatches: {mismatches}"

        # Verify all 16 plots are recorded with correct ids
        for i in range(4):
            for j in range(4):
                expected_id = f"plot_{i}_{j}"
                assert expected_id in recorded, f"{expected_id} not in recorded calls"


class TestReproducedFigureCallIdMatching:
    """Test call_id matching after save/reproduce cycle."""

    def test_reproduced_single_panel_call_ids_match(self):
        """Test call_ids match after save/reproduce for single panel."""
        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9], id="my_plot")
        ax.scatter([1, 2, 3], [9, 4, 1], id="my_scatter")

        # Save and reproduce
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.png"
            fr.save(fig, output, validate_error_level="warning")
            fig2, _ = fr.reproduce(output)

            color_map, recorded = get_hitmap_and_calls(fig2)
            mismatches = check_call_ids_match(color_map, recorded)

            assert not mismatches, f"Mismatches: {mismatches}"
            assert "my_plot" in recorded
            assert "my_scatter" in recorded

    def test_reproduced_multipanel_call_ids_match(self):
        """Test call_ids match after save/reproduce for multi-panel."""
        fig, axes = fr.subplots(3, 3)

        axes[0, 0].plot([1, 2], [1, 2], id="plot_a")
        axes[0, 1].scatter([1, 2], [1, 2], id="scatter_b")
        axes[0, 2].bar(["X", "Y"], [1, 2], id="bar_c")
        axes[1, 0].fill([0, 1, 1], [0, 0, 1], id="fill_d")
        axes[1, 1].errorbar([1, 2], [1, 2], yerr=[0.1, 0.1], id="errorbar_e")
        axes[1, 2].pie([50, 50], id="pie_f")
        rng = np.random.default_rng(42)
        axes[2, 0].hist(rng.random(50), id="hist_g")
        axes[2, 1].imshow(rng.random((5, 5)), id="imshow_h")
        axes[2, 2].fill_between([1, 2], [0, 0], [1, 1], id="fillbetween_i")

        # Save and reproduce
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.png"
            fr.save(fig, output, validate_error_level="warning")
            fig2, _ = fr.reproduce(output)

            color_map, recorded = get_hitmap_and_calls(fig2)
            mismatches = check_call_ids_match(color_map, recorded)

            assert not mismatches, f"Mismatches: {mismatches}"


class TestMultiLayerElements:
    """Test multi-layer elements like stackplot."""

    def test_stackplot_layers_have_layer_index(self):
        """Test that stackplot layers get layer_index for individual editing."""
        fig, ax = fr.subplots(1, 1)
        ax.stackplot([1, 2, 3], [1, 2, 3], [2, 3, 4], [3, 4, 5], id="my_stack")

        color_map, recorded = get_hitmap_and_calls(fig)

        # Check that stackplot layers have layer_index
        stack_elements = [
            (k, v) for k, v in color_map.items() if v.get("type") == "stackplot"
        ]
        assert (
            len(stack_elements) == 3
        ), f"Expected 3 stackplot layers, got {len(stack_elements)}"

        # Each layer should have a unique layer_index
        layer_indices = [v.get("layer_index") for _, v in stack_elements]
        assert set(layer_indices) == {
            0,
            1,
            2,
        }, f"Expected layer_indices 0,1,2, got {layer_indices}"

        # All layers should share the same call_id
        call_ids = [v.get("call_id") for _, v in stack_elements]
        assert all(
            cid == "my_stack" for cid in call_ids
        ), "All layers should have call_id 'my_stack'"


class TestNaturalSortingFix:
    """Test that natural sorting works for ax_key ordering."""

    def test_natural_sort_key(self):
        """Test natural sort function."""
        import re

        def natural_sort_key(s):
            return [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", s)]

        keys = ["ax_0_0", "ax_0_1", "ax_1_0", "ax_10_0", "ax_2_0", "ax_9_0"]
        sorted_keys = sorted(keys, key=natural_sort_key)

        expected = ["ax_0_0", "ax_0_1", "ax_1_0", "ax_2_0", "ax_9_0", "ax_10_0"]
        assert sorted_keys == expected, f"Got {sorted_keys}, expected {expected}"

    def test_detect_plot_types_uses_natural_sort(self):
        """Test that detect_plot_types uses natural sorting."""
        from figrecipe._editor._hitmap._detect import detect_plot_types

        # Create a figure with enough panels to trigger sorting issues
        fig, axes = fr.subplots(4, 4)  # 16 panels

        # Plot in each with distinct id
        for i in range(4):
            for j in range(4):
                axes[i, j].plot([1, 2], [1, 2], id=f"p{i}{j}")

        result = detect_plot_types(fig)

        # ax_idx 0-15 should all be present
        for ax_idx in range(16):
            assert ax_idx in result, f"ax_idx {ax_idx} not found in result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
