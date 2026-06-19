#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Native matplotlib diagram renderer using FancyBboxPatch and FancyArrowPatch."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._arrows import compute_connection_points, create_edge_arrow
from ._layout import compute_layout
from ._shapes import create_node_patch, estimate_node_bounds
from ._styles_native import resolve_font_config

if TYPE_CHECKING:
    from ._schema import DiagramSpec


class DiagramRenderer:
    """Native matplotlib renderer for diagrams.

    Renders diagrams using matplotlib patches without external dependencies
    like Mermaid or Graphviz.

    Examples
    --------
    >>> from figrecipe import Diagram
    >>> d = Diagram(type="workflow")
    >>> d.add_node("a", "Start")
    >>> d.add_node("b", "End", emphasis="primary")
    >>> d.add_edge("a", "b")
    >>> renderer = DiagramRenderer(d.spec)
    >>> fig, ax = renderer.render()
    >>> plt.show()
    """

    def __init__(
        self,
        spec: "DiagramSpec",
        layout: str = "layered",
        direction: Optional[str] = None,
    ):
        """Initialize the renderer.

        Parameters
        ----------
        spec : DiagramSpec
            The diagram specification.
        layout : str
            Layout algorithm: layered, grid, spring, kamada_kawai
        direction : str, optional
            Layout direction: LR, TB, RL, BT.
            If None, inferred from spec.paper.reading_direction.
        """
        self.spec = spec
        self.layout = layout

        if direction is None:
            rd = spec.paper.reading_direction
            direction = "LR" if rd == "left_to_right" else "TB"
        self.direction = direction

        # Computed state
        self._positions: Dict[str, Tuple[float, float]] = {}
        self._node_sizes: Dict[str, Tuple[float, float]] = {}

    def compute_positions(self) -> Dict[str, Tuple[float, float]]:
        """Compute node positions using the layout algorithm.

        Returns
        -------
        dict
            Mapping from node_id to (x, y) position.
        """
        self._positions = compute_layout(
            self.spec,
            algorithm=self.layout,
            direction=self.direction,
        )

        # Compute node sizes for edge connections
        for node in self.spec.nodes:
            w, h = estimate_node_bounds(node.label, node.shape)
            self._node_sizes[node.id] = (w, h)

        return self._positions

    def render(
        self,
        ax: Optional[Axes] = None,
        width_mm: float = 200.0,
        height_mm: float = 150.0,
        dpi: int = 150,
    ) -> Tuple[Figure, Axes]:
        """Render the diagram to matplotlib axes.

        Parameters
        ----------
        ax : Axes, optional
            Existing axes to render on. If None, creates new figure.
        width_mm : float
            Figure width in millimeters (default: 200.0).
        height_mm : float
            Figure height in millimeters (default: 150.0).
        dpi : int
            Figure DPI.

        Returns
        -------
        tuple
            (Figure, Axes) containing the rendered diagram.
        """
        if ax is None:
            figsize = (width_mm / 25.4, height_mm / 25.4)
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        else:
            fig = ax.figure

        # Compute positions if not already done
        if not self._positions:
            self.compute_positions()

        # Render edges first (lower z-order)
        self._render_edges(ax)

        # Render nodes
        self._render_nodes(ax)

        # Add title if specified
        if self.spec.title:
            ax.set_title(
                self.spec.title,
                fontsize=resolve_font_config()["title_size"],
                fontweight="bold",
            )

        # Clean up axes - don't use equal aspect which distorts patches
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        return fig, ax

    def _render_nodes(self, ax: Axes) -> None:
        """Render all nodes as FancyBboxPatch."""
        for node in self.spec.nodes:
            pos = self._positions.get(node.id)
            if pos is None:
                continue

            x, y = pos
            patch, text_kwargs = create_node_patch(
                x,
                y,
                node.label,
                shape=node.shape,
                emphasis=node.emphasis,
            )

            ax.add_patch(patch)
            ax.text(**text_kwargs)

    def _render_edges(self, ax: Axes) -> None:
        """Render all edges as FancyArrowPatch."""
        # Track edge pairs for bidirectional handling
        edge_pairs = {}
        for edge in self.spec.edges:
            key = tuple(sorted([edge.source, edge.target]))
            if key not in edge_pairs:
                edge_pairs[key] = []
            edge_pairs[key].append(edge)

        for edge in self.spec.edges:
            source_pos = self._positions.get(edge.source)
            target_pos = self._positions.get(edge.target)

            if source_pos is None or target_pos is None:
                continue

            source_size = self._node_sizes.get(edge.source, (0.1, 0.05))
            target_size = self._node_sizes.get(edge.target, (0.1, 0.05))

            # Compute connection points on node boundaries
            start, end = compute_connection_points(
                source_pos,
                source_size,
                target_pos,
                target_size,
                self.direction,
            )

            # Check if bidirectional
            key = tuple(sorted([edge.source, edge.target]))
            is_bidirectional = len(edge_pairs[key]) > 1
            index = edge_pairs[key].index(edge)

            # Adjust for bidirectional edges
            if is_bidirectional:
                connectionstyle = f"arc3,rad={0.15 if index == 0 else -0.15}"
            else:
                connectionstyle = "arc3,rad=0.0"

            arrow, label_kwargs = create_edge_arrow(
                start,
                end,
                style=edge.style,
                label=edge.label,
                arrow_type=edge.arrow,
                connectionstyle=connectionstyle,
            )

            ax.add_patch(arrow)
            if label_kwargs:
                ax.text(**label_kwargs)

    def render_to_file(
        self,
        path: Union[str, Path],
        format: Optional[str] = None,
        dpi: int = 300,
        transparent: bool = False,
        save_recipe: bool = True,
        **kwargs,
    ) -> Path:
        """Render diagram directly to file.

        Parameters
        ----------
        path : str or Path
            Output file path.
        format : str, optional
            Output format (inferred from extension if not specified).
        dpi : int
            Output DPI.
        transparent : bool
            Whether to use transparent background.
        save_recipe : bool
            If True (default), save a YAML recipe alongside the image.
        **kwargs
            Additional arguments passed to fig.savefig().

        Returns
        -------
        Path
            Path to the saved file.
        """
        path = Path(path)
        if format is None:
            format = path.suffix.lstrip(".") or "png"

        fig, ax = self.render()

        fig.savefig(
            path,
            format=format,
            dpi=dpi,
            transparent=transparent,
            bbox_inches="tight",
            **kwargs,
        )
        if save_recipe:
            _save_graph_recipe(self, path.with_suffix(".yaml"), dpi=dpi)
        plt.close(fig)

        return path

    # Intuitive alias
    save = render_to_file

    def to_dict(self) -> Dict[str, Any]:
        """Serialize renderer state for recipe recording.

        Returns
        -------
        dict
            Serializable dictionary with diagram data and positions.
        """
        # Ensure positions are computed
        if not self._positions:
            self.compute_positions()

        return {
            "type": self.spec.type.value,
            "title": self.spec.title,
            "layout": self.layout,
            "direction": self.direction,
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "shape": n.shape,
                    "emphasis": n.emphasis,
                }
                for n in self.spec.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "style": e.style,
                    "arrow": e.arrow,
                }
                for e in self.spec.edges
            ],
            "positions": {k: list(v) for k, v in self._positions.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagramRenderer":
        """Reconstruct renderer from serialized data.

        Parameters
        ----------
        data : dict
            Dictionary from to_dict().

        Returns
        -------
        DiagramRenderer
            Reconstructed renderer with pre-computed positions.
        """
        from ._schema import DiagramSpec, DiagramType, EdgeSpec, NodeSpec

        # Rebuild spec
        spec = DiagramSpec(
            type=DiagramType(data.get("type", "workflow")),
            title=data.get("title", ""),
        )

        for n in data.get("nodes", []):
            spec.nodes.append(
                NodeSpec(
                    id=n["id"],
                    label=n["label"],
                    shape=n.get("shape", "box"),
                    emphasis=n.get("emphasis", "normal"),
                )
            )

        for e in data.get("edges", []):
            spec.edges.append(
                EdgeSpec(
                    source=e["source"],
                    target=e["target"],
                    label=e.get("label"),
                    style=e.get("style", "solid"),
                    arrow=e.get("arrow", "normal"),
                )
            )

        renderer = cls(
            spec,
            layout=data.get("layout", "layered"),
            direction=data.get("direction", "LR"),
        )

        # Restore positions
        positions = data.get("positions", {})
        renderer._positions = {k: tuple(v) for k, v in positions.items()}

        # Compute sizes
        for node in spec.nodes:
            w, h = estimate_node_bounds(node.label, node.shape)
            renderer._node_sizes[node.id] = (w, h)

        return renderer


def render_diagram_native(
    spec: "DiagramSpec",
    path: Optional[Union[str, Path]] = None,
    layout: str = "layered",
    direction: Optional[str] = None,
    dpi: int = 300,
    **kwargs,
) -> Union[Tuple[Figure, Axes], Path]:
    """Convenience function to render a diagram.

    Parameters
    ----------
    spec : DiagramSpec
        The diagram specification.
    path : str or Path, optional
        If provided, saves to file and returns path.
        If None, returns (fig, ax).
    layout : str
        Layout algorithm.
    direction : str, optional
        Layout direction.
    dpi : int
        Output DPI for file.
    **kwargs
        Additional arguments for file saving.

    Returns
    -------
    tuple or Path
        (Figure, Axes) if path is None, else Path to saved file.
    """
    renderer = DiagramRenderer(spec, layout=layout, direction=direction)

    if path is not None:
        return renderer.render_to_file(path, dpi=dpi, **kwargs)

    return renderer.render()


def _save_graph_recipe(renderer: DiagramRenderer, path: Path, dpi: int = 300):
    """Save a standalone YAML recipe for a graph diagram."""
    import datetime

    import yaml

    recipe = {
        "figrecipe": "1.0",
        "type": "graph_diagram",
        "created": datetime.datetime.now().isoformat(),
        "dpi": dpi,
        "diagram": renderer.to_dict(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)


__all__ = [
    "DiagramRenderer",
    "render_diagram_native",
]
