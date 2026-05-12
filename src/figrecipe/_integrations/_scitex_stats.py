#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration with scitex.stats for statistical results."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Check if scitex.stats is available
from scitex_dev import try_import_optional

scitex_stats = try_import_optional("scitex_stats", extra="scitex", pkg="figrecipe")
SCITEX_STATS_AVAILABLE = scitex_stats is not None


def from_scitex_stats(
    stats_result: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Convert scitex.stats result(s) to figrecipe stats format.

    Parameters
    ----------
    stats_result : dict or list of dict
        Statistical result(s) from scitex.stats. Supports:
        - Single comparison dict
        - List of comparison dicts
        - scitex.stats flat format: {name, method, p_value, effect_size, ci95}
        - scitex.stats nested format: {method: {name}, results: {p_value}}

    Returns
    -------
    dict
        Figrecipe-compatible stats dict with 'comparisons' list.

    Examples
    --------
    >>> from scitex import stats
    >>> result = stats.ttest_ind(x, y)
    >>> fr_stats = from_scitex_stats(result)
    >>> fig.set_stats(fr_stats)

    >>> # Or for multiple comparisons
    >>> results = [stats.ttest_ind(a, b), stats.ttest_ind(a, c)]
    >>> fr_stats = from_scitex_stats(results)
    """
    # Normalize to list
    if isinstance(stats_result, dict):
        results = [stats_result]
    else:
        results = list(stats_result)

    comparisons = []
    for result in results:
        comp = _convert_single_result(result)
        if comp:
            comparisons.append(comp)

    return {"comparisons": comparisons}


def _convert_single_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single scitex.stats result to figrecipe format."""
    # Handle flat format (legacy or from load_statsz)
    if "p_value" in result and "results" not in result:
        return _convert_flat_format(result)

    # Handle nested format (from test functions)
    if "results" in result:
        return _convert_nested_format(result)

    # Handle already-converted format
    if "comparisons" in result:
        # Already in figrecipe format, return first comparison
        comps = result.get("comparisons", [])
        return comps[0] if comps else {}

    return {}


def _convert_flat_format(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert flat scitex.stats format."""
    p_value = result.get("p_value")
    stars = result.get("formatted") or result.get("stars")
    if not stars and p_value is not None:
        stars = _p_to_stars(p_value)

    comp = {
        "name": result.get("name", "comparison"),
        "p_value": p_value,
        "stars": stars,
        "method": result.get("method", ""),
    }

    # Handle effect size
    es = result.get("effect_size")
    if es is not None:
        ci = result.get("ci95", [])
        if isinstance(es, (int, float)):
            comp["effect_size"] = {
                "name": "d",
                "value": float(es),
            }
            if len(ci) >= 2:
                comp["effect_size"]["ci_lower"] = ci[0]
                comp["effect_size"]["ci_upper"] = ci[1]
        elif isinstance(es, dict):
            comp["effect_size"] = es

    return comp


def _convert_nested_format(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert nested scitex.stats format."""
    method_data = result.get("method", {})
    results_data = result.get("results", {})

    method_name = (
        method_data.get("name", "")
        if isinstance(method_data, dict)
        else str(method_data)
    )
    p_value = results_data.get("p_value")
    stars = _p_to_stars(p_value) if p_value is not None else ""

    comp = {
        "name": result.get("name", "comparison"),
        "p_value": p_value,
        "stars": stars,
        "method": method_name,
    }

    # Handle effect size from results
    es_data = results_data.get("effect_size")
    if es_data:
        if isinstance(es_data, dict):
            comp["effect_size"] = es_data
        else:
            comp["effect_size"] = {"name": "d", "value": float(es_data)}

    return comp


def _p_to_stars(p_value: float, ns_symbol: bool = True) -> str:
    """Convert p-value to significance stars."""
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    return "ns" if ns_symbol else ""


def load_stats_bundle(path: Union[str, Path]) -> Dict[str, Any]:
    """Load stats from a scitex.stats bundle file.

    Parameters
    ----------
    path : str or Path
        Path to .statsz or .zip bundle file.

    Returns
    -------
    dict
        Figrecipe-compatible stats dict.

    Raises
    ------
    ImportError
        If scitex.stats is not installed.
    """
    if not SCITEX_STATS_AVAILABLE:
        raise ImportError(
            "scitex.stats is required for bundle loading. "
            "Install with: pip install scitex[stats]"
        )

    data = scitex_stats.load_statsz(path)
    comparisons = data.get("comparisons", [])

    # Convert each comparison
    return from_scitex_stats(comparisons)


def annotate_from_stats(
    ax,
    stats: Dict[str, Any],
    positions: Optional[Dict[str, float]] = None,
    style: str = "stars",
    **kwargs,
) -> List[Any]:
    """Add stat annotations to axes from stats dict.

    Parameters
    ----------
    ax : RecordingAxes
        The axes to annotate.
    stats : dict
        Stats dict with 'comparisons' list. Each comparison should have:
        - name: "Group A vs Group B" (parsed for group names)
        - p_value: float
        - Optional: groups: ["Group A", "Group B"]
    positions : dict, optional
        Mapping of group names to x positions. If None, uses 0, 1, 2, ...
    style : str
        Annotation style: "stars", "p_value", "both".
    **kwargs
        Additional arguments passed to add_stat_annotation().

    Returns
    -------
    list
        List of artist objects created.

    Examples
    --------
    >>> stats = from_scitex_stats(result)
    >>> annotate_from_stats(ax, stats, positions={"Control": 0, "Treatment": 1})
    """
    comparisons = stats.get("comparisons", [])
    if not comparisons:
        return []

    artists = []
    y_offset = 0

    for comp in comparisons:
        # Get positions for this comparison
        x1, x2 = _get_comparison_positions(comp, positions)
        if x1 is None or x2 is None:
            continue

        # Calculate y position (stack annotations)
        y = kwargs.pop("y", None)
        if y is None:
            # Auto-calculate based on data
            ylim = ax.get_ylim() if hasattr(ax, "get_ylim") else (0, 1)
            y = ylim[1] + (ylim[1] - ylim[0]) * 0.05 * (1 + y_offset)
            y_offset += 1

        # Add annotation
        result = ax.add_stat_annotation(
            x1,
            x2,
            p_value=comp.get("p_value"),
            text=comp.get("stars") if style == "stars" else None,
            y=y,
            style=style,
            id=comp.get("name", "").replace(" ", "_"),
            **kwargs,
        )
        artists.extend(result if isinstance(result, list) else [result])

    return artists


def _get_comparison_positions(
    comp: Dict[str, Any],
    positions: Optional[Dict[str, float]],
) -> tuple:
    """Extract x positions for a comparison."""
    # Try explicit groups
    groups = comp.get("groups", [])
    if len(groups) >= 2 and positions:
        x1 = positions.get(groups[0])
        x2 = positions.get(groups[1])
        if x1 is not None and x2 is not None:
            return x1, x2

    # Try parsing from name (e.g., "Control vs Treatment")
    name = comp.get("name", "")
    if " vs " in name:
        parts = name.split(" vs ")
        if len(parts) >= 2 and positions:
            x1 = positions.get(parts[0].strip())
            x2 = positions.get(parts[1].strip())
            if x1 is not None and x2 is not None:
                return x1, x2

    # Try x1, x2 directly in comparison
    if "x1" in comp and "x2" in comp:
        return comp["x1"], comp["x2"]

    # Default to sequential positions
    if positions is None:
        return 0, 1

    return None, None


__all__ = [
    "SCITEX_STATS_AVAILABLE",
    "from_scitex_stats",
    "load_stats_bundle",
    "annotate_from_stats",
]
