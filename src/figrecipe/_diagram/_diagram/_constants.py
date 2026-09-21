#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Constants for diagram diagram rendering."""
import scitex_logging as slogging

# 9 canonical anchors (relative to box: 0-1 range)
ANCHOR_POINTS = {
    "center": (0.5, 0.5),
    "top": (0.5, 1.0),
    "bottom": (0.5, 0.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "top-left": (0.0, 1.0),
    "top-right": (1.0, 1.0),
    "bottom-left": (0.0, 0.0),
    "bottom-right": (1.0, 0.0),
}

# Token synonyms for programmatic normalization
_SYNONYMS = {"upper": "top", "lower": "bottom", "center": "center", "middle": "center"}
_VERTICAL = {"top", "bottom"}
_HORIZONTAL = {"left", "right"}


def normalize_anchor(raw: str) -> str:
    """Normalize any anchor string to one of the 9 canonical forms.

    Accepts any order, separator (- _ space), and synonyms (upper/lower/middle).
    E.g. "left-top", "upper_right", "lower left" all resolve correctly.
    """
    if raw == "auto":
        return raw
    tokens = [t for t in raw.lower().replace("-", " ").replace("_", " ").split() if t]
    tokens = [_SYNONYMS.get(t, t) for t in tokens]
    if len(tokens) == 1:
        if tokens[0] in ANCHOR_POINTS:
            return tokens[0]
    elif len(tokens) == 2:
        v = [t for t in tokens if t in _VERTICAL]
        h = [t for t in tokens if t in _HORIZONTAL]
        if v and h:
            return f"{v[0]}-{h[0]}"

    slogging.getLogger(__name__).warning(
        "Unknown anchor '%s'. Available: %s. Falling back to 'center'.",
        raw,
        ", ".join(sorted(ANCHOR_POINTS)),
    )
    return "center"


# Semantic node classes → default shape
NODE_CLASSES = {
    "source": "rounded",
    "input": "cylinder",
    "processing": "rounded",
    "output": "cylinder",
    "claim": "document",
    "code": "codeblock",
}

# Verification states → default (fill_color, border_color)
VERIFICATION_STATES = {
    "verified": ("#90EE90", "#228B22"),
    "tampered": ("#FFB6C1", "#DC143C"),
    "invalidated": ("#FFD580", "#E67E00"),
    "ignored": ("#D3D3D3", "#808080"),
}


__all__ = ["ANCHOR_POINTS", "NODE_CLASSES", "VERIFICATION_STATES", "normalize_anchor"]
