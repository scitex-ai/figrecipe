#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-14 (ywatanabe)"
# File: /home/ywatanabe/proj/figrecipe/tests/test_autofix.py

"""Tests for auto_fix layout violation resolution."""

import warnings

import matplotlib

matplotlib.use("Agg")


import figrecipe as fr
from figrecipe._diagram._diagram._autofix import auto_fix
from figrecipe._diagram._diagram._fix_layout import (
    _collect_canvas_violations,
    _collect_container_violations,
    _collect_overlap_violations,
)


class TestAutoFixNoViolations:
    """auto_fix with a well-formed diagram produces no warnings."""

    def test_no_violations_no_warnings(self):
        """Normal diagram with well-spaced boxes renders cleanly."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=130, y_mm=50, width_mm=40, height_mm=25)
        s.add_arrow("a", "b")

        fig, ax = s.render(auto_fix=True)
        assert fig._figrecipe_diagram_failed is False

    def test_no_violations_returns_zero(self):
        """auto_fix() returns 0 when there are no violations."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=130, y_mm=50, width_mm=40, height_mm=25)
        s._finalize_canvas_size()
        count = auto_fix(s)
        assert count == 0


class TestFixOverlaps:
    """R2: Overlapping boxes are pushed apart by auto_fix."""

    def test_overlapping_boxes_resolved(self):
        """Two boxes at the same position no longer overlap after auto_fix."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s._finalize_canvas_size()

        # Confirm violation exists before fix
        violations_before = _collect_overlap_violations(s)
        assert len(violations_before) > 0

        fig, ax = s.render(auto_fix=True)

        violations_after = _collect_overlap_violations(s)
        assert len(violations_after) == 0

    def test_partially_overlapping_boxes_resolved(self):
        """Partially overlapping boxes are separated after auto_fix."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=55, y_mm=50, width_mm=40, height_mm=25)
        s._finalize_canvas_size()

        fig, ax = s.render(auto_fix=True)

        violations_after = _collect_overlap_violations(s)
        assert len(violations_after) == 0


class TestFixContainerEnclosure:
    """R1: Containers are expanded to enclose children by auto_fix."""

    def test_child_outside_container_fixed(self):
        """Child positioned outside container is enclosed after auto_fix."""
        s = fr.Diagram(width_mm=300, height_mm=200)
        s.add_container(
            "c",
            title="Container",
            children=["a"],
            x_mm=80,
            y_mm=80,
            width_mm=40,
            height_mm=50,
        )
        s.add_box("a", title="A", x_mm=150, y_mm=80, width_mm=30, height_mm=20)
        s._finalize_canvas_size()

        # Confirm violation exists before fix
        violations_before = _collect_container_violations(s)
        assert len(violations_before) > 0

        fig, ax = s.render(auto_fix=True)

        violations_after = _collect_container_violations(s)
        assert len(violations_after) == 0


class TestFixCanvasBounds:
    """R9: Canvas xlim/ylim expanded to contain out-of-bounds elements."""

    def test_box_beyond_canvas_fixed(self):
        """Box at x_mm=200 on a 170mm canvas triggers canvas expansion."""
        s = fr.Diagram(width_mm=170, height_mm=100)
        s.add_box("far", title="Far", x_mm=200, y_mm=50, width_mm=40, height_mm=25)
        s._finalize_canvas_size()

        # Confirm violation exists before fix
        violations_before = _collect_canvas_violations(s)
        assert len(violations_before) > 0

        fig, ax = s.render(auto_fix=True)

        violations_after = _collect_canvas_violations(s)
        assert len(violations_after) == 0

        # Canvas should have expanded to contain the box
        assert s.xlim[1] >= 220  # box center=200 + half_width=20

    def test_box_below_canvas_fixed(self):
        """Box at negative y position triggers ylim expansion."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("low", title="Low", x_mm=90, y_mm=-20, width_mm=40, height_mm=25)
        s._finalize_canvas_size()

        violations_before = _collect_canvas_violations(s)
        assert len(violations_before) > 0

        fig, ax = s.render(auto_fix=True)

        violations_after = _collect_canvas_violations(s)
        assert len(violations_after) == 0

        assert s.ylim[0] <= -32.5  # box center=-20 - half_height=12.5


class TestAutoFixReturnCount:
    """auto_fix returns a non-zero integer when violations are fixed."""

    def test_returns_nonzero_on_violations(self):
        """auto_fix returns positive count when fixes are applied."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s._finalize_canvas_size()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            count = auto_fix(s)

        assert isinstance(count, int)
        assert count > 0


class TestDefaultNoFix:
    """auto_fix=False (default) does not resolve violations."""

    def test_overlapping_boxes_warn_without_autofix(self):
        """Overlapping boxes set _figrecipe_diagram_failed with default auto_fix."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=50, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=50, y_mm=50, width_mm=40, height_mm=25)

        fig, ax = s.render()
        assert fig._figrecipe_diagram_failed is True

    def test_child_outside_container_warns_without_autofix(self):
        """Child outside container marks diagram as failed with default auto_fix=False."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_container(
            "c",
            title="Container",
            children=["a"],
            x_mm=50,
            y_mm=50,
            width_mm=40,
            height_mm=30,
        )
        s.add_box("a", title="A", x_mm=100, y_mm=50, width_mm=40, height_mm=25)

        fig, ax = s.render()
        assert fig._figrecipe_diagram_failed is True

    def test_canvas_bounds_violation_warns_without_autofix(self):
        """Element beyond canvas bounds marks diagram as failed with default auto_fix=False."""
        s = fr.Diagram(width_mm=170, height_mm=100)
        s.add_box("far", title="Far", x_mm=200, y_mm=50, width_mm=40, height_mm=25)

        fig, ax = s.render()
        assert fig._figrecipe_diagram_failed is True


class TestFixPostRender:
    """Phase 2: Post-render auto-fix for text collisions and arrow occlusion."""

    def test_arrow_label_occlusion_fixed(self):
        """R7: Arrow label sitting on arrow path is offset by auto_fix."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=40, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=130, y_mm=50, width_mm=40, height_mm=25)
        s.add_arrow("a", "b", label="Label")

        # Without auto_fix, the label occludes the arrow (R7 violation)
        fig, ax = s.render()
        assert fig._figrecipe_diagram_failed is True

    def test_arrow_label_occlusion_autofix_succeeds(self):
        """R7: auto_fix offsets the label so arrow visibility passes."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=40, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=130, y_mm=50, width_mm=40, height_mm=25)
        s.add_arrow("a", "b", label="Label")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fig, ax = s.render(auto_fix=True)

        # Label should have been offset
        arrow = s._arrows[0]
        assert arrow.label_offset_mm is not None
        assert arrow.label_offset_mm != (0, 0)

    def test_nandeyanen_diagram_autofix(self):
        """Real-world test: Nandeyanen diagram renders with auto_fix."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("yusuke", title="Yusuke", x_mm=40, y_mm=50, width_mm=40, height_mm=25)
        s.add_box(
            "nandeyanen",
            title="Nandeyanen",
            x_mm=130,
            y_mm=50,
            width_mm=50,
            height_mm=25,
        )
        s.add_arrow("yusuke", "nandeyanen", label="Why?!")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fig, ax = s.render(auto_fix=True)

        # Should succeed without exception
        assert fig is not None

    def test_no_label_no_fix_needed(self):
        """Arrows without labels don't trigger post-render fixes."""
        s = fr.Diagram(width_mm=180, height_mm=100)
        s.add_box("a", title="A", x_mm=40, y_mm=50, width_mm=40, height_mm=25)
        s.add_box("b", title="B", x_mm=130, y_mm=50, width_mm=40, height_mm=25)
        s.add_arrow("a", "b")

        fig, ax = s.render(auto_fix=True)
        assert fig._figrecipe_diagram_failed is False


# EOF
