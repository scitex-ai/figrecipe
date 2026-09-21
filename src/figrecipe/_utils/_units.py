#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit conversion utilities for figrecipe.

Provides conversions between millimeters, inches, and points for precise
figure layout control.

Constants:
    - 1 inch = 25.4 mm
    - 1 inch = 72 points (PostScript points)
    - 1 mm = 72/25.4 points
"""
import scitex_logging as slogging

__all__ = [
    "mm_to_inch",
    "inch_to_mm",
    "mm_to_pt",
    "pt_to_mm",
    "mm_to_scatter_size",
    "normalize_color",
]

from typing import List, Tuple, Union

console = slogging.getConsole(f"{__name__}.console")

# Conversion constants
MM_PER_INCH = 25.4
PT_PER_INCH = 72.0


def mm_to_inch(mm: float) -> float:
    """Convert millimeters to inches.

    Parameters
    ----------
    mm : float
        Value in millimeters

    Returns
    -------
    float
        Value in inches

    Examples
    --------
    >>> mm_to_inch(25.4)
    1.0
    >>> mm_to_inch(40)  # Nature figure width
    1.5748031496062993
    """
    return mm / MM_PER_INCH


def inch_to_mm(inch: float) -> float:
    """Convert inches to millimeters.

    Parameters
    ----------
    inch : float
        Value in inches

    Returns
    -------
    float
        Value in millimeters

    Examples
    --------
    >>> inch_to_mm(1.0)
    25.4
    """
    return inch * MM_PER_INCH


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to points (PostScript points).

    Parameters
    ----------
    mm : float
        Value in millimeters

    Returns
    -------
    float
        Value in points (1 pt = 1/72 inch)

    Examples
    --------
    >>> mm_to_pt(0.2)  # Typical line thickness
    0.5669291338582677
    >>> mm_to_pt(0.8)  # Typical tick length
    2.267716535433071
    """
    return mm * PT_PER_INCH / MM_PER_INCH


def pt_to_mm(pt: float) -> float:
    """Convert points to millimeters.

    Parameters
    ----------
    pt : float
        Value in points

    Returns
    -------
    float
        Value in millimeters

    Examples
    --------
    >>> pt_to_mm(1.0)
    0.3527777777777778
    """
    return pt * MM_PER_INCH / PT_PER_INCH


def mm_to_scatter_size(diameter_mm: float) -> float:
    """Convert mm diameter to matplotlib scatter 's' parameter.

    matplotlib's scatter() uses 's' as marker AREA in points².
    This function converts a desired diameter in mm to the correct
    's' value for circular markers.

    Parameters
    ----------
    diameter_mm : float
        Desired marker diameter in millimeters

    Returns
    -------
    float
        Value for scatter's 's' parameter (area in points²)

    Examples
    --------
    >>> import figrecipe as fr
    >>> # 0.8mm diameter markers (matches tick length)
    >>> s = fr.mm_to_scatter_size(0.8)
    >>> ax.scatter(x, y, s=s)

    >>> # Use style's marker size
    >>> style = fr.load_style()
    >>> s = fr.mm_to_scatter_size(style.markers.size_mm)
    >>> ax.scatter(x, y, s=s)

    Notes
    -----
    For a circle: area = π * r² = π * (d/2)²
    where d is diameter in points.
    """
    import math

    diameter_pt = mm_to_pt(diameter_mm)
    return math.pi * (diameter_pt / 2) ** 2


def normalize_color(
    color: Union[List[int], Tuple[int, ...], str],
) -> Union[Tuple[float, ...], str]:
    """Normalize color to matplotlib-compatible format.

    Converts RGB [0-255] values to normalized [0-1] tuples.
    Hex strings and named colors are passed through unchanged.

    Parameters
    ----------
    color : list, tuple, or str
        Color in various formats:
        - RGB list/tuple [0-255]: [0, 128, 192] -> (0.0, 0.5, 0.75)
        - Hex string: "#0080C0" -> "#0080C0"
        - Named color: "blue" -> "blue"

    Returns
    -------
    tuple or str
        Matplotlib-compatible color specification

    Examples
    --------
    >>> normalize_color([0, 128, 192])
    (0.0, 0.5019607843137255, 0.7529411764705882)
    >>> normalize_color("#0080C0")
    '#0080C0'
    >>> normalize_color("blue")
    'blue'
    """
    if isinstance(color, str):
        return color
    if isinstance(color, (list, tuple)):
        # Check if already normalized (values <= 1)
        if all(c <= 1.0 for c in color):
            return tuple(color)
        # Normalize 0-255 to 0-1
        return tuple(c / 255.0 for c in color)
    return color


if __name__ == "__main__":
    # Test conversions
    console.info("Unit conversion tests:")
    console.info(f"  25.4 mm = {mm_to_inch(25.4):.4f} inch")
    console.info(f"  1 inch = {inch_to_mm(1.0):.1f} mm")
    console.info(f"  0.2 mm = {mm_to_pt(0.2):.4f} pt")
    console.info(f"  1 pt = {pt_to_mm(1.0):.4f} mm")
    console.info("\nColor normalization:")
    console.info(f"  [0, 128, 192] -> {normalize_color([0, 128, 192])}")
    console.info(f"  '#0080C0' -> {normalize_color('#0080C0')}")
