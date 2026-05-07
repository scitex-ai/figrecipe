#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure / axes dimension info helpers.

Migrated from ``scitex.plt.utils._figure_from_axes_mm`` as Phase 3 of
the figrecipe-owns-plt rebalance. Generic — takes plain matplotlib
``(fig, ax)`` and returns a debug dict in mm / inch / px / DPI.

Useful when you're confused about the relationship between mm,
inches, pixels, and DPI. Pairs with ``figrecipe.subplots`` for
verifying that the requested ``axes_width_mm`` actually rendered at
the right pixel count.
"""

from __future__ import annotations

from typing import Any, Dict


def get_dimension_info(fig, ax) -> Dict[str, Any]:
    """Get all dimension info about a figure/axes for debugging.

    Returns a dict with figure size in inch / mm / px, axes size in
    inch / mm / px, axes bounding box in mm and px (origin top-left),
    DPI, and the mm-per-inch conversion factor.

    The function calls ``fig.canvas.draw()`` to finalise layout
    (constrained_layout, tight_layout, label adjustments) so the
    reported axes position is the *actual* one after all adjustments.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    ax : matplotlib.axes.Axes

    Returns
    -------
    dict
        See module docstring for keys.

    Examples
    --------
    >>> import figrecipe as fg
    >>> fig, ax = fg.subplots(axes_width_mm=30, axes_height_mm=21)
    >>> info = get_dimension_info(fig, ax)
    >>> print(f"Axes size: {info['axes_size_mm']} mm")
    >>> print(f"Axes size: {info['axes_size_px']} px at {info['dpi']} DPI")
    """
    from ._units import MM_PER_INCH, inch_to_mm

    fig_width_inch, fig_height_inch = fig.get_size_inches()
    dpi = fig.dpi

    fig_width_mm = inch_to_mm(fig_width_inch)
    fig_height_mm = inch_to_mm(fig_height_inch)
    fig_width_px = int(fig_width_inch * dpi)
    fig_height_px = int(fig_height_inch * dpi)

    # Finalise layout so window_extent is post-adjustment.
    fig.canvas.draw()

    bbox = ax.get_window_extent()
    axes_x0_px = int(round(bbox.x0))
    axes_x1_px = int(round(bbox.x1))
    # Convert display origin (bottom-left) to canvas/web (top-left).
    axes_y0_px = int(round(fig_height_px - bbox.y1))
    axes_y1_px = int(round(fig_height_px - bbox.y0))
    axes_width_px = int(round(bbox.width))
    axes_height_px = int(round(bbox.height))

    axes_width_inch = bbox.width / dpi
    axes_height_inch = bbox.height / dpi
    axes_width_mm = inch_to_mm(axes_width_inch)
    axes_height_mm = inch_to_mm(axes_height_inch)

    axes_x0_mm = (bbox.x0 / dpi) * MM_PER_INCH
    axes_x1_mm = (bbox.x1 / dpi) * MM_PER_INCH
    axes_y0_mm = ((fig_height_px - bbox.y1) / dpi) * MM_PER_INCH
    axes_y1_mm = ((fig_height_px - bbox.y0) / dpi) * MM_PER_INCH

    pos = ax.get_position()

    return {
        "figure_size_inch": (fig_width_inch, fig_height_inch),
        "figure_size_mm": (fig_width_mm, fig_height_mm),
        "figure_size_px": (fig_width_px, fig_height_px),
        "axes_position": (pos.x0, pos.y0, pos.width, pos.height),
        "axes_size_inch": (axes_width_inch, axes_height_inch),
        "axes_size_mm": (axes_width_mm, axes_height_mm),
        "axes_size_px": (axes_width_px, axes_height_px),
        "axes_bbox_px": {
            "x0": axes_x0_px,
            "y0": axes_y0_px,
            "x1": axes_x1_px,
            "y1": axes_y1_px,
            "width": axes_width_px,
            "height": axes_height_px,
        },
        "axes_bbox_mm": {
            "x0": axes_x0_mm,
            "y0": axes_y0_mm,
            "x1": axes_x1_mm,
            "y1": axes_y1_mm,
            "width": axes_width_mm,
            "height": axes_height_mm,
        },
        "dpi": dpi,
        "mm_per_inch": MM_PER_INCH,
    }


def print_dimension_info(fig, ax) -> None:
    """Print ``get_dimension_info`` output in a human-readable format."""
    info = get_dimension_info(fig, ax)

    print("\n" + "=" * 60)
    print("DIMENSION INFORMATION")
    print("=" * 60)

    print("\nFIGURE (total canvas including margins):")
    print(
        f"  Size (mm):    {info['figure_size_mm'][0]:.2f} x {info['figure_size_mm'][1]:.2f}"
    )
    print(
        f"  Size (inch):  {info['figure_size_inch'][0]:.3f} x {info['figure_size_inch'][1]:.3f}"
    )
    print(f"  Size (px):    {info['figure_size_px'][0]} x {info['figure_size_px'][1]}")

    print("\nAXES (actual plot area):")
    print(
        f"  Size (mm):    {info['axes_size_mm'][0]:.2f} x {info['axes_size_mm'][1]:.2f}"
    )
    print(
        f"  Size (inch):  {info['axes_size_inch'][0]:.3f} x {info['axes_size_inch'][1]:.3f}"
    )
    print(f"  Size (px):    {info['axes_size_px'][0]} x {info['axes_size_px'][1]}")
    print(
        f"  Position:     left={info['axes_position'][0]:.3f}, bottom={info['axes_position'][1]:.3f}"
    )

    print("\nSETTINGS:")
    print(f"  DPI:          {info['dpi']}")
    print(f"  Conversion:   1 inch = {info['mm_per_inch']} mm")
    print(
        f"  At {info['dpi']} DPI: 1 mm = {info['dpi'] / 25.4:.2f} px, 1 inch = {info['dpi']} px"
    )

    print("\nFOR PUBLICATION:")
    print(
        f"  Save with: fig.savefig('file.tiff', dpi={info['dpi']}, bbox_inches='tight')"
    )
    print(
        f"  Final axes size: ~{info['axes_size_mm'][0]:.1f} x {info['axes_size_mm'][1]:.1f} mm"
    )
    print("=" * 60 + "\n")


__all__ = ["get_dimension_info", "print_dimension_info"]
