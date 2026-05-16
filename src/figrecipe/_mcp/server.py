#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP server for figrecipe - declarative matplotlib figure creation.

This module provides MCP tools for creating, reproducing, and managing
matplotlib figures through the figrecipe library.

Usage:
    fastmcp run figrecipe._mcp.server:mcp
    # or
    figrecipe mcp start
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastmcp import FastMCP

from .._branding import get_mcp_instructions, get_mcp_server_name
from ._diagram_tools import register_diagram_tools
from ._resources import register_resources

mcp = FastMCP(
    name=get_mcp_server_name(),
    instructions=get_mcp_instructions(),
)


@mcp.tool
def plt_plot(
    spec: Dict[str, Any],
    output_path: str,
    dpi: int = 300,
    save_recipe: bool = True,
) -> Dict[str, Any]:
    """Create a publication-ready matplotlib figure from a single declarative spec dict — one call covers subplots, plots (line/scatter/bar/hist/box/violin/heatmap/errorbar/etc.), axis labels/limits, legend, title, stat annotations, and style. Drop-in replacement for hand-writing `fig, ax = plt.subplots(); ax.plot(...); ax.set_xlabel(...); ax.legend(); fig.savefig(...)` sequences. Use whenever the user asks to "make a plot / figure", "plot this data", "create a bar/scatter/line chart", "draw a histogram/boxplot/violin/heatmap", "save the figure as PNG/PDF/SVG", or describes a figure declaratively. Also writes a YAML recipe so the figure can be reproduced later with `plt_reproduce`.

    See figrecipe._api._plot module docstring for full spec format.

    Parameters
    ----------
    spec : dict
        Declarative specification. Key sections: figure, plots, stat_annotations,
        xlabel, ylabel, title, legend, xlim, ylim.
    output_path : str
        Path to save the output figure.
    dpi : int
        DPI for raster output (default: 300).
    save_recipe : bool
        If True, also save as figrecipe YAML recipe.

    Returns
    -------
    dict
        Result with 'image_path' and 'recipe_path'.

    Raises
    ------
    ValueError
        If no plots are specified or data is missing.
    """
    from .._api._plot import create_figure_from_spec

    # Validate spec has plots with data
    plots = spec.get("plots", [])
    axes_specs = spec.get("axes") or spec.get("subplots", [])
    if not plots and not axes_specs:
        raise ValueError("No plots specified in spec. Add 'plots' or 'axes' section.")
    for i, p in enumerate(plots):
        if not (p.get("x") or p.get("y") or p.get("data") or p.get("z")):
            raise ValueError(f"Plot {i} has no data (x, y, data, or z required)")

    result = create_figure_from_spec(
        spec=spec,
        output_path=output_path,
        dpi=dpi,
        save_recipe=save_recipe,
        show=False,
    )

    return {
        "image_path": str(result["image_path"]) if result["image_path"] else None,
        "recipe_path": str(result["recipe_path"])
        if result.get("recipe_path")
        else None,
        "success": True,
    }


@mcp.tool
def plt_reproduce(
    recipe_path: str,
    output_path: Optional[str] = None,
    format: str = "png",
    dpi: int = 300,
) -> Dict[str, Any]:
    """Regenerate a figure bit-for-bit from its saved YAML recipe — the core reproducibility contract of figrecipe. Use whenever the user asks to "reproduce this figure", "regenerate the plot from the recipe", "re-render the YAML", "recreate the figure at higher DPI", "export the recipe to PDF/SVG", or wants to reuse an existing plot spec. Takes a `.yaml` recipe saved by `plt_plot` / `fr.save(fig, ...)` and produces the image again — no original data arrays needed because the recipe embeds them.

    Parameters
    ----------
    recipe_path : str
        Path to the .yaml recipe file.

    output_path : str, optional
        Output path for the reproduced figure.
        Defaults to recipe_path with .reproduced.{format} suffix.

    format : str
        Output format: png, pdf, or svg.

    dpi : int
        DPI for raster output.

    Returns
    -------
    dict
        Result with 'output_path' and 'success'.
    """
    import matplotlib.pyplot as plt

    import figrecipe as fr

    recipe_path = Path(recipe_path)

    if output_path is None:
        output_path = recipe_path.with_suffix(f".reproduced.{format}")
    else:
        output_path = Path(output_path)

    fig, axes = fr.reproduce(recipe_path)
    fig.savefig(output_path, dpi=dpi, format=format)

    try:
        plt.close(fig)
    except TypeError:
        plt.close("all")

    return {
        "output_path": str(output_path),
        "success": True,
    }


@mcp.tool
def plt_compose(
    sources: List[str],
    output_path: str,
    layout: str = "horizontal",
    gap_mm: float = 5.0,
    dpi: int = 300,
    panel_labels: bool = True,
    label_style: str = "uppercase",
    caption: Optional[str] = None,
    create_symlinks: bool = True,
    canvas_size_mm: Optional[Tuple[float, float]] = None,
    save_recipe: bool = True,
) -> Dict[str, Any]:
    """Combine multiple figures or panels into a single publication-figure with automatic A/B/C/D labels, precise mm-based placement, and an editable recipe. Drop-in replacement for manual `matplotlib.gridspec.GridSpec`, `subplot2grid`, Inkscape / Illustrator panel-assembly, and ImageMagick `montage`. Use whenever the user asks to "combine these figures", "make a multi-panel figure", "panels A, B, C side by side", "lay out subfigures", "arrange panels at exact mm positions", "add panel labels", or is assembling a final manuscript figure from individual plots.

    Supports two modes:
    1. Grid-based layout (list sources): automatic arrangement with layout parameter
    2. Free-form positioning (dict sources): precise mm-based positioning

    All layouts are internally converted to mm-based positioning, enabling:
    - Precise control over panel placement
    - Recipe-based editing and re-composition
    - Future adjustments without re-solving layout

    Parameters
    ----------
    sources : list of str or dict
        Either:
        - List of paths to source images or recipe files (grid-based layout)
        - Dict mapping source paths to positioning specs with 'xy_mm' and 'size_mm':
          {"panel_a.yaml": {"xy_mm": [0, 0], "size_mm": [80, 50]}, ...}
    output_path : str
        Path to save the composed figure.
    layout : str
        Layout mode for list sources: 'horizontal', 'vertical', or 'grid'.
        Ignored when using dict sources with mm positioning.
    gap_mm : float
        Gap between panels in millimeters (for grid-based layout only).
    dpi : int
        DPI for output.
    panel_labels : bool
        If True, add panel labels (A, B, C, D) automatically.
    label_style : str
        Style: 'uppercase' (A,B,C), 'lowercase' (a,b,c), 'numeric' (1,2,3).
    caption : str, optional
        Figure caption to add below.
    create_symlinks : bool
        If True (default), create symlinks to source files for traceability.
    canvas_size_mm : tuple of (float, float), optional
        Canvas size as (width_mm, height_mm) for free-form positioning.
        Required when sources is a dict with mm positioning.
    save_recipe : bool
        If True (default), save a .compose.yaml recipe file for future editing.

    Returns
    -------
    dict
        Result with 'output_path', 'success', 'layout_spec', 'recipe_path',
        and 'sources_dir' (if symlinks created).

    Examples
    --------
    Grid-based layout:

    >>> compose(
    ...     sources=["panel_a.png", "panel_b.png"],
    ...     output_path="figure.png",
    ...     layout="horizontal",
    ... )

    Free-form mm-based positioning:

    >>> compose(
    ...     canvas_size_mm=[180, 120],
    ...     sources={
    ...         "panel_a.yaml": {"xy_mm": [0, 0], "size_mm": [80, 50]},
    ...         "panel_b.yaml": {"xy_mm": [90, 0], "size_mm": [80, 50]},
    ...     },
    ...     output_path="figure.png",
    ... )
    """
    from pathlib import Path

    import matplotlib.pyplot as plt

    from .. import compose as fr_compose
    from .. import save as fr_save
    from .._composition._layout_solver import solve_layout_to_mm

    # Convert list sources to mm-based dict
    if isinstance(sources, list):
        sources_mm = solve_layout_to_mm(sources, layout, gap_mm)
    else:
        sources_mm = {
            p: {"xy_mm": tuple(s["xy_mm"]), "size_mm": tuple(s["size_mm"])}
            for p, s in sources.items()
        }

    # Create composed figure using unified matplotlib-based API
    fig, axes = fr_compose(
        sources=sources_mm,
        canvas_size_mm=tuple(canvas_size_mm) if canvas_size_mm else None,
        dpi=dpi,
        panel_labels=panel_labels,
        label_style=label_style,
    )

    # Save output with recipe
    output_path = Path(output_path)
    fr_save(fig, output_path, verbose=False, validate=False)

    result = {
        "output_path": str(output_path),
        "success": True,
        "layout_spec": {
            "canvas_size_mm": list(fig.record.canvas_size_mm)
            if hasattr(fig.record, "canvas_size_mm")
            else None,
            "panels": {
                p: {"xy_mm": list(s["xy_mm"]), "size_mm": list(s["size_mm"])}
                for p, s in sources_mm.items()
            },
        },
        "recipe_path": str(output_path.with_suffix(".yaml")),
    }

    plt.close(fig._fig if hasattr(fig, "_fig") else fig)
    return result


@mcp.tool
def plt_info(recipe_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Inspect a figrecipe `.yaml` recipe — returns figure dimensions, call counts, plot types used, and (verbose) full call log. Use when the user asks to "inspect this recipe", "what's inside this YAML?", "summarize this figure", "what plots does this recipe contain?", or is auditing a saved figure before reproducing or modifying it.

    Parameters
    ----------
    recipe_path : str
        Path to the .yaml recipe file.

    verbose : bool
        If True, include detailed call information.

    Returns
    -------
    dict
        Recipe information including figure dimensions, call counts, etc.
    """
    import figrecipe as fr

    recipe_info = fr.info(recipe_path)
    return recipe_info


@mcp.tool
def plt_validate(
    recipe_path: str,
    mse_threshold: float = 100.0,
) -> Dict[str, Any]:
    """Verify a recipe regenerates a pixel-close copy of the original figure (MSE-based). Use when the user asks to "validate this recipe", "check the recipe still works", "verify reproducibility", "does this YAML still make the same figure?", or is auditing recipe health before trusting it for a paper. Returns `valid`, `mse`, and a diagnostic message.

    Parameters
    ----------
    recipe_path : str
        Path to the .yaml recipe file.

    mse_threshold : float
        Maximum acceptable mean squared error (default: 100).

    Returns
    -------
    dict
        Validation result with 'passed', 'mse', and details.
    """
    import figrecipe as fr

    result = fr.validate(recipe_path, mse_threshold=mse_threshold)

    return {
        "valid": result.valid,
        "mse": result.mse,
        "message": result.message,
        "recipe_path": str(recipe_path),
    }


@mcp.tool
def plt_crop(
    input_path: str,
    output_path: Optional[str] = None,
    margin_mm: float = 1.0,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Trim whitespace borders from a figure image with per-side mm-precision margins. Drop-in replacement for `PIL.Image.crop` + manual bbox detection, ImageMagick `-trim`, `pdfcrop`, and matplotlib's `bbox_inches='tight'` (with more control). Use whenever the user asks to "crop whitespace", "trim the figure", "remove margins", "tighten the bounding box", "crop to content", or "cut blank space around the plot". Works on PNG/JPEG/PDF.

    Parameters
    ----------
    input_path : str
        Path to the input image.

    output_path : str, optional
        Path for cropped output. Defaults to input with .cropped suffix.

    margin_mm : float
        Margin to keep around content in millimeters.

    overwrite : bool
        If True, overwrite the input file.

    Returns
    -------
    dict
        Result with 'output_path' and 'success'.
    """
    import figrecipe as fr

    result_path = fr.crop(
        input_path,
        output_path=output_path,
        margin_mm=margin_mm,
        overwrite=overwrite,
    )

    return {
        "output_path": str(result_path),
        "success": True,
    }


@mcp.tool
def plt_extract_data(recipe_path: str) -> Dict[str, Dict[str, Any]]:
    """Pull the raw x/y/z arrays back out of a figrecipe YAML — gives you the underlying data that produced each line, scatter, bar, etc. Use whenever the user asks to "get the data out of this figure", "recover the plotted values", "export to CSV", "reuse the data for another plot", or is data-mining an old figure where source CSVs were lost. Returns a dict keyed by call_id with arrays as JSON-serializable lists.

    Parameters
    ----------
    recipe_path : str
        Path to the .yaml recipe file.

    Returns
    -------
    dict
        Nested dict: {call_id: {'x': list, 'y': list, ...}}
    """
    import figrecipe as fr

    data = fr.extract_data(recipe_path)

    # Convert numpy arrays to lists for JSON serialization
    result = {}
    for call_id, call_data in data.items():
        result[call_id] = {}
        for key, value in call_data.items():
            if hasattr(value, "tolist"):
                result[call_id][key] = value.tolist()
            else:
                result[call_id][key] = value

    return result


@mcp.tool
def plt_list_styles() -> Dict[str, Any]:
    """List the named figure style presets that ship with figrecipe — currently `SCITEX` (publication defaults) and `MATPLOTLIB` (stock rcParams). Use whenever the user asks "what styles are available?", "what style presets does figrecipe ship?", "list the themes", or before choosing a style name to pass to `plt_plot`.

    Returns
    -------
    dict
        Dictionary with 'presets' list of available style names.
    """
    import figrecipe as fr

    presets = fr.list_presets()

    return {
        "presets": presets,
        "count": len(presets),
    }


@mcp.tool
def plt_get_plot_types() -> Dict[str, Any]:
    """Enumerate every plot type figrecipe's declarative spec understands — line/plot/step/fill/fill_between/errorbar, scatter, bar/barh, hist/hist2d/boxplot/violinplot, imshow/matshow/heatmap/pcolormesh, contour/contourf, pie/stem/eventplot/hexbin. Use when the user asks "what plot types are supported?", "can figrecipe do a heatmap / violin / hexbin?", "list all plot kinds", or before writing a declarative spec.

    Returns
    -------
    dict
        Dictionary with 'plot_types' and their descriptions.
    """
    from .._api._plot import PLOT_TYPES

    return {
        "plot_types": list(PLOT_TYPES.keys()),
        "mapping": PLOT_TYPES,
        "categories": {
            "line_curve": ["line", "plot", "step", "fill", "fill_between", "errorbar"],
            "scatter_points": ["scatter"],
            "bar_categorical": ["bar", "barh"],
            "distribution": [
                "hist",
                "hist2d",
                "boxplot",
                "box",
                "violinplot",
                "violin",
            ],
            "image_matrix": ["imshow", "matshow", "heatmap", "pcolormesh"],
            "contour": ["contour", "contourf"],
            "special": ["pie", "stem", "eventplot", "hexbin"],
        },
    }


# Resource for spec schema documentation
@mcp.resource("figrecipe://spec-schema")
def get_spec_schema() -> str:
    """Get the declarative plot specification schema from API module."""
    from .._api import _plot

    # Return the module docstring as single source of truth
    schema = _plot.__doc__ or ""

    # Append supported plot types
    from .._api._plot import PLOT_TYPES

    schema += "\n\nSupported Plot Types\n"
    schema += "--------------------\n"
    schema += ", ".join(sorted(PLOT_TYPES.keys()))

    return schema


# §5 audit-mcp-tools — every package's MCP server MUST expose
# skills_list + skills_get so agents can discover skill pages.
@mcp.tool
async def skills_list() -> Dict[str, Any]:
    """List available skill pages for figrecipe."""
    from scitex_dev.skills import list_skills

    return list_skills(package="figrecipe")


@mcp.tool
async def skills_get(name: Optional[str] = None) -> Dict[str, Any]:
    """Get a figrecipe skill page by name (or list when name is None)."""
    from scitex_dev.skills import get_skill

    return get_skill(package="figrecipe", name=name)


# Register additional documentation resources
register_resources(mcp)

# Register diagram tools
register_diagram_tools(mcp)

# Register explicit per-method plot tools (plt_line, plt_scatter, plt_bar, …)
from ._plot_tools import register_plot_tools  # noqa: E402

register_plot_tools(mcp)

# Register §6 Python-API parity wrappers (subplots, save, reproduce, …).
from ._api_parity_tools import register_api_parity_tools  # noqa: E402

register_api_parity_tools(mcp)


if __name__ == "__main__":
    mcp.run()
