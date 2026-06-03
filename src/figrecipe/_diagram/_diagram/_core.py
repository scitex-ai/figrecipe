#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagram builder for rich scientific diagrams."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from ._color import Color, normalize_color  # noqa: F401
from ._constants import (
    ANCHOR_POINTS,
    NODE_CLASSES,
    VERIFICATION_STATES,
    normalize_anchor,
)  # noqa: F401
from ._specs import (  # noqa: F401
    Anchor,
    ArrowSpec,
    BoxSpec,
    IconSpec,
    PositionSpec,
    _resolve_emphasis,
)

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class Diagram:
    """Builder for rich box-and-arrow diagrams with mm-based coordinates."""

    def __init__(
        self,
        title: Optional[str] = None,
        width_mm: float = 170.0,
        height_mm: Optional[float] = 120.0,
        padding_mm: float = 10.0,
        gap_mm: Optional[float] = None,
    ):
        if width_mm > 185.0:
            logger.warning(
                f"Diagram width {width_mm}mm exceeds 185mm (double-column max)."
            )
        self.title = title
        self.width_mm = width_mm
        self._padding_mm = padding_mm
        self._gap_mm = gap_mm
        self._flow_items: List[str] = []
        if gap_mm is not None:
            height_mm = None  # force auto-height in flex mode
        self._auto_height = height_mm is None
        self.height_mm = height_mm if height_mm is not None else 0
        self.figsize = (width_mm / 25.4, self.height_mm / 25.4)
        self.xlim = (0, width_mm)
        self.ylim = (0, self.height_mm)
        self._boxes: Dict[str, BoxSpec] = {}
        self._containers: Dict[str, Dict] = {}
        self._arrows: List[ArrowSpec] = []
        self._icons: Dict[str, IconSpec] = {}
        self._positions: Dict[str, PositionSpec] = {}
        self._render_info: Dict[str, Dict[str, Any]] = {}

    def add_box(
        self,
        id: str,
        title: str,
        subtitle: Optional[str] = None,
        content: Optional[List] = None,
        emphasis: str = "normal",
        shape: str = "rounded",
        x_mm: Optional[float] = None,
        y_mm: Optional[float] = None,
        width_mm: Optional[float] = None,
        height_mm: Optional[float] = None,
        fill_color: Color = None,
        border_color: Color = None,
        title_color: Color = None,
        padding_mm: float = 5.0,
        margin_mm: float = 0.0,
        node_class: Optional[str] = None,
        state: Optional[str] = None,
        language: Optional[str] = None,
        bullet: Optional[str] = None,
    ) -> "Diagram":
        """Add a rich text box. See BoxSpec for node_class/state/language/bullet."""
        fill_color = normalize_color(fill_color)
        border_color = normalize_color(border_color)
        title_color = normalize_color(title_color)
        if node_class and shape == "rounded" and node_class in NODE_CLASSES:
            shape = NODE_CLASSES[node_class]
        if state and state in VERIFICATION_STATES:
            s_fill, s_border = VERIFICATION_STATES[state]
            fill_color = fill_color or s_fill
            border_color = border_color or s_border
        fill_color, border_color, title_color = _resolve_emphasis(
            emphasis,
            fill_color,
            border_color,
            title_color,
        )
        box = BoxSpec(
            id=id,
            title=title,
            subtitle=subtitle,
            content=content or [],
            emphasis=emphasis,
            shape=shape,
            fill_color=fill_color,
            border_color=border_color,
            title_color=title_color,
            padding_mm=padding_mm,
            margin_mm=margin_mm,
            node_class=node_class,
            state=state,
            language=language,
            bullet=bullet,
        )
        self._boxes[id] = box
        if self._gap_mm is not None and x_mm is None and y_mm is None:
            if height_mm is None:
                height_mm = self._auto_box_height(box)
            from ._flex import auto_box_width

            w = width_mm if width_mm is not None else auto_box_width(box)
            self._positions[id] = PositionSpec(0, 0, w, height_mm)
            self._flow_items.append(id)
            return self
        if height_mm is None and None not in (x_mm, y_mm, width_mm):
            height_mm = self._auto_box_height(box)
        if None not in (x_mm, y_mm, width_mm, height_mm):
            self._positions[id] = PositionSpec(x_mm, y_mm, width_mm, height_mm)
        return self

    def add_container(
        self,
        id: str,
        title: Optional[str] = None,
        children: Optional[List[str]] = None,
        emphasis: str = "muted",
        x_mm: Optional[float] = None,
        y_mm: Optional[float] = None,
        width_mm: Optional[float] = None,
        height_mm: Optional[float] = None,
        fill_color: Color = None,
        border_color: Color = None,
        title_loc: str = "upper center",
        direction: str = "row",
        container_gap_mm: float = 8.0,
        container_padding_mm: float = 8.0,
        equalize_heights: bool = True,
        equalize_widths: bool = True,
    ) -> "Diagram":
        """Add a container. equalize_heights/widths: match children in row/column."""
        fill_color = normalize_color(fill_color)
        border_color = normalize_color(border_color)
        fill_color, border_color, _ = _resolve_emphasis(
            emphasis, fill_color, border_color
        )
        self._containers[id] = {
            "title": title,
            "children": children or [],
            "emphasis": emphasis,
            "fill_color": fill_color,
            "border_color": border_color,
            "title_loc": title_loc,
            "direction": direction,
            "gap_mm": container_gap_mm,
            "padding_mm": container_padding_mm,
            "equalize_heights": equalize_heights,
            "equalize_widths": equalize_widths,
        }
        if self._gap_mm is not None and x_mm is None and y_mm is None:
            self._positions[id] = PositionSpec(0, 0, width_mm or 0, height_mm or 0)
            self._flow_items.append(id)
            return self
        if None not in (x_mm, y_mm, width_mm, height_mm):
            self._positions[id] = PositionSpec(x_mm, y_mm, width_mm, height_mm)
        return self

    def add_arrow(
        self,
        source: str,
        target: str,
        source_anchor: Anchor = "auto",
        target_anchor: Anchor = "auto",
        source_dx: float = 0.0,
        source_dy: float = 0.0,
        target_dx: float = 0.0,
        target_dy: float = 0.0,
        label: Optional[str] = None,
        style: str = "solid",
        color: Color = None,
        curve: float = 0.0,
        linewidth_mm: float = 0.5,
        label_offset_mm: Optional[Tuple[float, float]] = None,
        margin_mm: Optional[float] = None,
    ) -> "Diagram":
        """Add an arrow connecting two boxes."""
        color = normalize_color(color)
        auto_id = f"arrow:{source}->{target}"
        self._arrows.append(
            ArrowSpec(
                id=auto_id,
                source=source,
                target=target,
                source_anchor=source_anchor,
                target_anchor=target_anchor,
                source_dx=source_dx,
                source_dy=source_dy,
                target_dx=target_dx,
                target_dy=target_dy,
                label=label,
                style=style,
                color=color,
                curve=curve,
                linewidth_mm=linewidth_mm,
                label_offset_mm=label_offset_mm,
                margin_mm=margin_mm,
            )
        )
        return self

    def add_icon(
        self,
        id: str,
        source: str,
        x_mm: float,
        y_mm: float,
        width_mm: float = 8.0,
        height_mm: float = 8.0,
        color: Optional[str] = None,
        opacity: float = 1.0,
    ) -> "Diagram":
        """Add an icon (SVG/PNG or built-in: warning/check/cross/info/lock)."""
        self._icons[id] = IconSpec(id=id, source=source, color=color, opacity=opacity)
        self._positions[id] = PositionSpec(x_mm, y_mm, width_mm, height_mm)
        return self

    def validate_containers(self) -> None:
        """Check every container fully encloses its declared children."""
        from ._validate import validate_containers

        validate_containers(self)

    def validate_no_overlap(self) -> None:
        """Check that no two boxes overlap each other."""
        from ._validate import validate_no_overlap

        validate_no_overlap(self)

    def auto_layout(
        self,
        layout: str = "lr",
        margin_mm: float = 15.0,
        box_size_mm: Optional[Tuple[float, float]] = None,
        gap_mm: float = 10.0,
        avoid_overlap: bool = True,
        justify: str = "space-between",
        align_items: str = "center",
    ) -> "Diagram":
        """Automatically position boxes. See _layout for details."""
        from ._layout import auto_layout

        auto_layout(
            self,
            layout=layout,
            margin_mm=margin_mm,
            box_size_mm=box_size_mm,
            gap_mm=gap_mm,
            avoid_overlap=avoid_overlap,
            justify=justify,
            align_items=align_items,
        )
        return self

    def _auto_box_height(self, box: BoxSpec) -> float:
        """Compute box height from content when height_mm is not specified."""
        pad = box.padding_mm
        if box.shape == "codeblock":
            title_bar = 6.0
            n_lines = len(box.content)
            return title_bar + n_lines * 3.5 + 2 * pad
        h = 6.0  # title
        if box.subtitle:
            h += 5.0
        h += len(box.content) * 5.0
        h += 2 * pad
        return max(h, 18.0)

    def _finalize_canvas_size(self) -> None:
        """Compute canvas height from element positions when height_mm=None."""
        from ._flex import resolve_flex_layout

        resolve_flex_layout(self)
        if not self._auto_height:
            return
        if not self._positions:
            self.height_mm = 120.0
            self.ylim = (0, 120.0)
            self.figsize = (self.width_mm / 25.4, 120.0 / 25.4)
            return
        max_top = max(p.y_mm + p.height_mm / 2 for p in self._positions.values())
        min_bottom = min(p.y_mm - p.height_mm / 2 for p in self._positions.values())
        title_space = 12.0 if self.title else 0.0
        margin = 8.0
        self.height_mm = max_top - min_bottom + title_space + 2 * margin
        self.ylim = (min_bottom - margin, max_top + title_space + margin)
        self.figsize = (self.width_mm / 25.4, self.height_mm / 25.4)

    def _get_anchor(self, pos: PositionSpec, anchor: str) -> Tuple[float, float]:
        """Get absolute position of an anchor point on the visual box edge."""
        anchor = normalize_anchor(anchor)
        rx, ry = ANCHOR_POINTS[anchor]
        x = pos.x_mm - pos.width_mm / 2 + rx * pos.width_mm
        y = pos.y_mm - pos.height_mm / 2 + ry * pos.height_mm
        return x, y

    def _auto_anchor(self, src: PositionSpec, tgt: PositionSpec) -> Tuple[str, str]:
        """Determine best anchor points automatically."""
        dx, dy = tgt.x_mm - src.x_mm, tgt.y_mm - src.y_mm
        if abs(dx) > abs(dy):
            return ("right", "left") if dx > 0 else ("left", "right")
        return ("top", "bottom") if dy > 0 else ("bottom", "top")

    def render(
        self,
        ax: Optional[Axes] = None,
        auto_fix: bool = False,
        auto_curve: bool = True,
    ) -> Tuple["Figure", Axes]:
        """Render. auto_fix=True resolves violations; auto_curve=False skips R7."""
        import matplotlib.pyplot as plt

        from . import _render as _sr
        from . import _validate as _sv

        self._finalize_canvas_size()
        if auto_fix:
            from ._autofix import auto_fix as _af

            _af(self, auto_curve=auto_curve)

        w_mm = self.xlim[1] - self.xlim[0]
        h_mm = self.ylim[1] - self.ylim[0]
        figsize = (w_mm / 25.4, h_mm / 25.4)
        owns_fig = ax is None
        if owns_fig:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.figure

        _sr.draw_all_elements(self, ax)

        if auto_fix:
            from ._autofix import fix_post_render

            for _ in range(3):
                if fix_post_render(self, fig, ax) == 0:
                    break
                _sr.draw_all_elements(self, ax)

        if owns_fig:
            fig._figrecipe_diagram_failed = False
            fig._figrecipe_validation_errors = []
            try:
                _sv.validate_all(self, fig=fig, ax=ax)
            except ValueError as e:
                fig._figrecipe_diagram_failed = True
                fig._figrecipe_validation_errors = str(e).split("\n")
                logger.warning(str(e))
            fig._figrecipe_diagram = self

        # GH #139: record this render as a single high-level "diagram" call so
        # the recipe's reproducer can replay it via replay_diagram_native_call
        # (already wired to function="diagram" in _reproducer/_core.py via
        # _replay_diagram.py). Without this hook, users who call
        # `Diagram.render(ax)` directly on a figrecipe-recording axes get a
        # recipe with NO record of the diagram render, so
        # `fr.save(fig, validate=True)` round-trips into a blank panel and
        # fails the MSE check (figrecipe-concept violation per #139). The
        # `ax.diagram(...)` wrapper path already records via
        # _wrappers/_axes_diagram::_record_diagram_call; this mirrors that
        # for the direct-render path so the two entry points stay in sync.
        if (
            ax is not None
            and getattr(ax, "_recorder", None) is not None
            and getattr(ax, "_position", None) is not None
        ):
            try:
                from .._wrappers._axes_diagram import _record_diagram_call

                _record_diagram_call(ax._recorder, ax._position, None, self)
            except Exception as _e:  # noqa: BLE001 - defensive: never break render
                logger.warning(f"Failed to record diagram for recipe replay: {_e}")

        # Auto-crop SVG on any savefig call (stx.io.save, direct, etc.)
        # Pixel-analysis approach: renders temp PNG → find_content_area → adjust viewBox
        _original_savefig = fig.savefig
        fig._figrecipe_original_savefig = _original_savefig  # exposed for crop_svg

        def _savefig_with_svg_crop(fname, **kwargs):
            result = _original_savefig(fname, **kwargs)
            from pathlib import Path as _Path

            _p = _Path(str(fname))
            if _p.suffix.lower() == ".svg" and _p.exists():
                from figrecipe._utils._crop import crop_svg

                crop_svg(_p, fig, margin_mm=2.0)
            return result

        fig.savefig = _savefig_with_svg_crop

        return fig, ax

    def save(
        self,
        path: Union[str, Path],
        dpi: int = 200,
        save_recipe: bool = True,
        save_hitmap: bool = False,
        save_debug: bool = True,
        watermark: bool = False,
    ) -> Path:
        """Render, crop, and save. watermark=True adds 'Plotted by scitex.ai'."""
        from ._io import render_to_file as _rtf

        return _rtf(
            self,
            path,
            dpi=dpi,
            save_recipe=save_recipe,
            save_hitmap=save_hitmap,
            save_debug=save_debug,
            watermark=watermark,
        )

    # Backwards compatibility alias
    render_to_file = save

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagram to dictionary for serialization."""
        from ._io import diagram_to_dict

        return diagram_to_dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagram":
        """Create Diagram from dictionary (recipe reproduction)."""
        from ._io import diagram_from_dict

        return diagram_from_dict(data)


__all__ = [
    "ArrowSpec",
    "BoxSpec",
    "Color",
    "Diagram",
    "IconSpec",
    "NODE_CLASSES",
    "PositionSpec",
    "VERIFICATION_STATES",
]
