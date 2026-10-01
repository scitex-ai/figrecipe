#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an editable recipe from a neutral statistics plot spec.

The spec (``schema: scitex-stats.plot-spec``, version 1) is plain JSON: raw
data, precomputed summaries (box stats, mean ± CI, regression band) and
annotation text. Any producer can emit it; figrecipe does not import the
producer. Every element is drawn through ``RecordingAxes`` so the figure saves
as a normal recipe, and significance brackets use figrecipe's native
``add_stat_annotation`` so they stay editable and replay from the YAML.
"""

from __future__ import annotations

__all__ = [
    "STATS_PLOT_SPEC_SCHEMA",
    "STATS_PLOT_SPEC_VERSIONS",
    "from_stats_plot_spec",
    "validate_stats_plot_spec",
]

import warnings
from typing import Any, Dict, List, Tuple

STATS_PLOT_SPEC_SCHEMA = "scitex-stats.plot-spec"
STATS_PLOT_SPEC_VERSIONS = (1,)

_OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]


def validate_stats_plot_spec(spec: Any) -> Dict[str, Any]:
    """Return ``spec`` if it is a supported stats plot spec, else raise ``ValueError``."""
    if not isinstance(spec, dict) or spec.get("schema") != STATS_PLOT_SPEC_SCHEMA:
        raise ValueError(f"not a {STATS_PLOT_SPEC_SCHEMA} document")
    if spec.get("version") not in STATS_PLOT_SPEC_VERSIONS:
        raise ValueError(
            f"unsupported {STATS_PLOT_SPEC_SCHEMA} version {spec.get('version')!r}; "
            f"supported: {STATS_PLOT_SPEC_VERSIONS}"
        )
    kind = spec.get("kind")
    needs = {"groups": "groups", "paired": "groups", "one_sample": "groups", "correlation": "xy", "contingency": "table"}
    if kind not in needs or not spec.get(needs[kind]):
        raise ValueError(f"spec kind {kind!r} is missing its data block")
    return spec


def _light(color: str, amount: float = 0.72) -> str:
    from matplotlib.colors import to_hex, to_rgb

    r, g, b = to_rgb(color)
    return to_hex((r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount))


def _bracket_geometry(groups: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    ys = [v for g in groups for v in g["values"]]
    lo, hi = (min(ys), max(ys)) if ys else (0.0, 1.0)
    span = (hi - lo) or 1.0
    return hi + 0.08 * span, 0.11 * span, 0.025 * span


def _draw_groups(ax, spec: Dict[str, Any], palette: List[str]) -> None:
    groups = spec["groups"]
    types = {layer["type"]: layer for layer in spec.get("layers", [])}
    center = types.get("center", {}).get("estimator", "mean_ci")
    for g in groups:
        x, color, name = g["position"], palette[g["position"] % len(palette)], g["name"]
        if "box" in types and g["values"]:
            ax.boxplot(
                list(g["values"]), positions=[x], widths=0.5, showfliers=False,
                color=_light(color), medianprops={"color": color}, id=f"box_{x}",
            )
    if "paired_lines" in types and len(groups) >= 2:
        for k in range(min(len(g["values"]) for g in groups)):
            ax.plot(
                [g["position"] + g["jitter"][k] for g in groups], [g["values"][k] for g in groups],
                color="#999999", linewidth=0.5, alpha=0.7, zorder=2, id=f"pair_{k}",
            )
    if "points" in types:
        for g in groups:
            x, color = g["position"], palette[g["position"] % len(palette)]
            ax.scatter(
                [x + j for j in g["jitter"]], list(g["values"]), s=9, color=color,
                edgecolors="white", linewidths=0.3, alpha=0.9, zorder=3, id=f"points_{x}",
            )
    if center == "mean_ci":
        for g in groups:
            s = g.get("summary", {})
            if s.get("ci_lower") is None:
                continue
            ax.errorbar(
                [g["position"] + 0.33], [s["mean"]],
                yerr=[[s["mean"] - s["ci_lower"]], [s["ci_upper"] - s["mean"]]],
                fmt="o", color="black", markersize=3, capsize=1.8, elinewidth=0.6, capthick=0.6,
                zorder=4, id=f"mean_ci_{g['position']}",
            )
    for layer in spec.get("layers", []):
        if layer["type"] == "reference_line":
            ax.plot([-0.6, len(groups) - 0.4], [layer["value"]] * 2, color="#666666",
                    linestyle="--", linewidth=0.6, id="reference")
    ann = spec.get("annotations", {})
    ax.set_xticks([g["position"] for g in groups])
    ax.set_xticklabels([g["name"] + ("\n" + g.get("n_text", "") if ann.get("n_labels") else "") for g in groups])
    ax.set_xlim(-0.6, len(groups) - 0.4)
    brackets = ann.get("brackets", [])
    base, step, tick = _bracket_geometry(groups)
    ys = [v for g in groups for v in g["values"]] or [0.0, 1.0]
    span = (max(ys) - min(ys)) or 1.0
    top = max([base + b["tier"] * step + 0.75 * step for b in brackets], default=max(ys) + 0.08 * span)
    bottom = min(ys) - 0.08 * span
    ax.set_ylim(bottom, top)
    for b in brackets:
        ax.add_stat_annotation(
            groups[b["group1"]]["position"], groups[b["group2"]]["position"],
            p_value=b.get("p_value"), text=b["text"], y=base + b["tier"] * step,
            style="stars" if ann.get("show_stars") else "p_value",
            bracket_height=tick / (top - bottom), fontsize=spec["style"].get("font_size_pt", 7),
            fontweight="normal",
        )


def _draw_correlation(ax, spec: Dict[str, Any], palette: List[str]) -> None:
    xy, color = spec["xy"], palette[0]
    for layer in spec.get("layers", []):
        if layer["type"] == "regression":
            ax.fill_between(layer["x"], layer["lower"], layer["upper"], color=_light(color, 0.7),
                            linewidth=0, zorder=1, id="regression_ci")
            ax.plot(layer["x"], layer["y"], color=color, linewidth=1.0, zorder=2, id="regression")
    ax.scatter(list(xy["x"]), list(xy["y"]), s=10, color=color, edgecolors="white", linewidths=0.3,
               zorder=3, id="points")


def _draw_contingency(ax, spec: Dict[str, Any], palette: List[str]) -> None:
    table = spec["table"]
    layer = (spec.get("layers") or [{}])[0]
    k = len(table["rows"])
    width = layer.get("bar_width", 0.8 / max(k, 1))
    for i, (row, counts) in enumerate(zip(table["rows"], table["counts"])):
        offset = (i - (k - 1) / 2) * width
        ax.bar([j + offset for j in range(len(counts))], list(counts), width=width * 0.92,
               color=palette[i % len(palette)], label=row, id=f"bars_{i}")
    ax.set_xticks(list(range(len(table["columns"]))))
    ax.set_xticklabels(table["columns"])
    ax.legend(frameon=False, loc="upper right")


def from_stats_plot_spec(spec: Dict[str, Any]):
    """Create a recorded figure from a ``scitex-stats.plot-spec`` document.

    Parameters
    ----------
    spec : dict
        Stats plot spec (schema ``scitex-stats.plot-spec``, version 1).

    Returns
    -------
    (RecordingFigure, RecordingAxes)
        Save with :func:`figrecipe.save` to get the PNG plus editable YAML.

    Examples
    --------
    >>> fig, ax = figrecipe.from_stats_plot_spec(spec)
    >>> figrecipe.save(fig, "ttest.png")
    """
    import figrecipe as fr

    validate_stats_plot_spec(spec)
    style = spec.get("style", {})
    palette = list(style.get("palette") or _OKABE_ITO)
    width, height = float(style.get("width_mm", 85)), float(style.get("height_mm", 68))
    with warnings.catch_warnings():
        # Only the overall figure size matters here; constrained layout places the axes.
        warnings.filterwarnings("ignore", message=".*mm layout was computed.*")
        fig, ax = fr.subplots(axes_width_mm=max(width - 20.0, 20.0), axes_height_mm=max(height - 24.0, 20.0))
    kind = spec["kind"]
    if kind in ("groups", "paired", "one_sample"):
        _draw_groups(ax, spec, palette)
    elif kind == "correlation":
        _draw_correlation(ax, spec, palette)
    else:
        _draw_contingency(ax, spec, palette)
    ann = spec.get("annotations", {})
    title = "\n".join(t for t in (ann.get("statistic"), ann.get("effect_size")) if t)
    if title:
        ax.set_title(title, loc="left", fontsize=style.get("font_size_pt", 7))
    axes = spec.get("axes", {})
    if axes.get("x", {}).get("label"):
        ax.set_xlabel(axes["x"]["label"])
    if axes.get("y", {}).get("label"):
        ax.set_ylabel(axes["y"]["label"])
    return fig, ax


# EOF
