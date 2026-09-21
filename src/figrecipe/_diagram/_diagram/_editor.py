#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive editor for Diagram diagrams.

Provides a simple matplotlib-based GUI for dragging boxes to adjust positions.
Saves updated positions back to recipe YAML.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import scitex_logging as slogging
from matplotlib.backend_bases import MouseEvent
from matplotlib.patches import FancyBboxPatch, Rectangle

console = slogging.getConsole(f"{__name__}.console")

if TYPE_CHECKING:
    from ._core import Diagram


class DiagramEditor:
    """Interactive editor for adjusting diagram box positions."""

    def __init__(self, info: "Diagram"):
        """Initialize editor with a Diagram."""
        self.info = info
        self._selected_box: Optional[str] = None
        self._drag_offset: Tuple[float, float] = (0.0, 0.0)
        self._drag_start_pos: Optional[Tuple[float, float]] = None
        self._box_patches: Dict[str, FancyBboxPatch] = {}
        self._fig = None
        self._ax = None
        self._modified = False
        self._drag_ghost: Optional[Rectangle] = None
        self._background = None

    def run(self, save_path: Optional[Path] = None) -> "Diagram":
        """Launch interactive editor."""
        self._fig, self._ax = self.info.render()
        self._fig.canvas.manager.set_window_title(
            "Diagram Editor - Drag boxes to adjust"
        )

        # Add instructions
        self._instruction_text = self._ax.text(
            0.5,
            -0.05,
            "Drag boxes to move | Press 'S' to save | Press 'Q' to quit",
            transform=self._ax.transAxes,
            ha="center",
            va="top",
            fontsize=9,
            color="gray",
        )

        # Connect event handlers
        self._fig.canvas.mpl_connect("button_press_event", self._on_press)
        self._fig.canvas.mpl_connect("button_release_event", self._on_release)
        self._fig.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._fig.canvas.mpl_connect("key_press_event", self._on_key)

        self._save_path = save_path
        plt.show()
        return self.info

    def _find_box_at(self, x: float, y: float) -> Optional[str]:
        """Find which box contains the given coordinates."""
        for box_id, pos in self.info._positions.items():
            if box_id in self.info._containers:
                continue
            x_min = pos.x_mm - pos.width_mm / 2
            x_max = pos.x_mm + pos.width_mm / 2
            y_min = pos.y_mm - pos.height_mm / 2
            y_max = pos.y_mm + pos.height_mm / 2
            if x_min <= x <= x_max and y_min <= y <= y_max:
                return box_id
        return None

    def _on_press(self, event: MouseEvent) -> None:
        """Handle mouse press - select box and create drag ghost."""
        if event.inaxes != self._ax or event.xdata is None:
            return

        box_id = self._find_box_at(event.xdata, event.ydata)
        if box_id:
            self._selected_box = box_id
            pos = self.info._positions[box_id]
            self._drag_offset = (event.xdata - pos.x_mm, event.ydata - pos.y_mm)
            self._drag_start_pos = (pos.x_mm, pos.y_mm)

            # Cache background for blitting
            self._fig.canvas.draw()
            self._background = self._fig.canvas.copy_from_bbox(self._ax.bbox)

            # Create drag ghost rectangle
            self._drag_ghost = Rectangle(
                (pos.x_mm - pos.width_mm / 2, pos.y_mm - pos.height_mm / 2),
                pos.width_mm,
                pos.height_mm,
                fill=False,
                edgecolor="red",
                linewidth=2,
                linestyle="--",
                zorder=100,
            )
            self._ax.add_patch(self._drag_ghost)

    def _on_release(self, event: MouseEvent) -> None:
        """Handle mouse release - apply position and full redraw."""
        if self._selected_box is None:
            return

        # Remove ghost
        if self._drag_ghost:
            self._drag_ghost.remove()
            self._drag_ghost = None

        # Apply final position if mouse is valid
        if event.xdata is not None and event.ydata is not None:
            self._apply_position(event.xdata, event.ydata)

        self._selected_box = None
        self._drag_start_pos = None
        self._background = None

        # Full redraw with new positions
        self._redraw()

    def _on_motion(self, event: MouseEvent) -> None:
        """Handle mouse motion - update drag ghost position."""
        if (
            self._selected_box is None
            or event.xdata is None
            or self._drag_ghost is None
        ):
            return

        pos = self.info._positions[self._selected_box]
        new_x = event.xdata - self._drag_offset[0]
        new_y = event.ydata - self._drag_offset[1]

        # Clamp to bounds
        new_x = max(pos.width_mm / 2, min(self.info.xlim[1] - pos.width_mm / 2, new_x))
        new_y = max(
            pos.height_mm / 2, min(self.info.ylim[1] - pos.height_mm / 2, new_y)
        )

        # Update ghost position (fast, no full redraw)
        self._drag_ghost.set_xy((new_x - pos.width_mm / 2, new_y - pos.height_mm / 2))

        # Use blitting for smooth animation
        if self._background:
            self._fig.canvas.restore_region(self._background)
            self._ax.draw_artist(self._drag_ghost)
            self._fig.canvas.blit(self._ax.bbox)
        else:
            self._fig.canvas.draw_idle()

    def _apply_position(self, mouse_x: float, mouse_y: float) -> None:
        """Apply new position from mouse coordinates."""
        from ._core import PositionSpec

        pos = self.info._positions[self._selected_box]
        new_x = mouse_x - self._drag_offset[0]
        new_y = mouse_y - self._drag_offset[1]

        # Clamp to bounds
        new_x = max(pos.width_mm / 2, min(self.info.xlim[1] - pos.width_mm / 2, new_x))
        new_y = max(
            pos.height_mm / 2, min(self.info.ylim[1] - pos.height_mm / 2, new_y)
        )

        self.info._positions[self._selected_box] = PositionSpec(
            x_mm=new_x, y_mm=new_y, width_mm=pos.width_mm, height_mm=pos.height_mm
        )
        self._modified = True

    def _on_key(self, event) -> None:
        """Handle key press."""
        if event.key == "s":
            self._save()
        elif event.key == "q":
            plt.close(self._fig)

    def _redraw(self) -> None:
        """Redraw the diagram with updated positions."""
        self._ax.clear()
        self.info.render(ax=self._ax)
        status = " [MODIFIED]" if self._modified else ""
        self._ax.text(
            0.5,
            -0.05,
            f"Drag boxes to move | Press 'S' to save | Press 'Q' to quit{status}",
            transform=self._ax.transAxes,
            ha="center",
            va="top",
            fontsize=9,
            color="orange" if self._modified else "gray",
        )
        self._fig.canvas.draw()

    def _save(self) -> None:
        """Save current positions to recipe YAML."""
        if self._save_path:
            import yaml

            # Load existing recipe
            with open(self._save_path) as f:
                recipe = yaml.safe_load(f)

            # Update diagram_data positions
            for ax_key, ax_data in recipe.get("axes", {}).items():
                for call in ax_data.get("calls", []):
                    if call.get("function") in ("diagram", "schematic"):
                        info_data = call.get("kwargs", {}).get(
                            "diagram_data",
                            call.get("kwargs", {}).get("schematic_data", {}),
                        )
                        positions = {}
                        for box_id, pos in self.info._positions.items():
                            positions[box_id] = {
                                "x_mm": round(pos.x_mm, 2),
                                "y_mm": round(pos.y_mm, 2),
                                "width_mm": round(pos.width_mm, 2),
                                "height_mm": round(pos.height_mm, 2),
                            }
                        info_data["positions"] = positions

            # Save updated recipe
            with open(self._save_path, "w") as f:
                yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

            console.info(f"Saved: {self._save_path}")
            self._modified = False
            self._redraw()


def edit_diagram(
    source: "Diagram | Path | str",
    save_path: Optional[Path] = None,
) -> "Diagram":
    """Launch interactive editor for a diagram.

    Parameters
    ----------
    source : Diagram or Path or str
        Either a Diagram object or path to recipe YAML.
    save_path : Path, optional
        Where to save updated recipe. If source is a Path, defaults to same file.

    Returns
    -------
    Diagram
        The modified diagram.

    Examples
    --------
    >>> import figrecipe as fr
    >>> diagram = fr.Diagram()
    >>> diagram.add_box("a", title="A")
    >>> diagram.add_box("b", title="B")
    >>> diagram.auto_layout("lr")
    >>> fr.edit_diagram(diagram)  # Opens interactive editor
    """

    if isinstance(source, (str, Path)):
        source = Path(source)
        save_path = save_path or source

        # Load from recipe
        import yaml

        with open(source) as f:
            recipe = yaml.safe_load(f)

        # Find diagram data in recipe
        for ax_data in recipe.get("axes", {}).values():
            for call in ax_data.get("calls", []):
                if call.get("function") in ("diagram", "schematic"):
                    info_data = call.get("kwargs", {}).get(
                        "diagram_data", call.get("kwargs", {}).get("schematic_data", {})
                    )
                    info = Diagram.from_dict(info_data)
                    break
            else:
                continue
            break
        else:
            raise ValueError("No diagram found in recipe")
    else:
        info = source

    editor = DiagramEditor(info)
    return editor.run(save_path=save_path)


__all__ = ["DiagramEditor", "edit_diagram"]
