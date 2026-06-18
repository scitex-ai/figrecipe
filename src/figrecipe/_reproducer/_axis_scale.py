#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation for replayed axis-scale (set_xscale / set_yscale) values.

``set_xscale`` / ``set_yscale`` are recorded as generic decorations (NeuroVista
Ask 2) so a ``log`` / ``symlog`` / ``logit`` axis reproduces as such instead of
silently falling back to ``linear``. matplotlib only knows a fixed set of scale
names; an unknown one would raise deep inside the generic replay and surface as a
vague "Failed to replay set_yscale" warning. We check the name up front and warn
loudly (no silent fallback) so an unsupported / custom scale is recognised during
reproduction.
"""

import warnings
from typing import Any, List

# Built-in matplotlib scale names. ``function`` / ``functionlog`` need a callable
# pair that can't be serialized into a recipe, so they are intentionally absent
# here -- a recipe should never carry them, and if one does we warn rather than
# crash.
_SUPPORTED_SCALES = {"linear", "log", "symlog", "logit", "asinh"}


def warn_if_unsupported_scale(method_name: str, args: List[Any]) -> None:
    """Warn if a recorded axis scale is not a recognised matplotlib scale.

    Parameters
    ----------
    method_name : str
        The replayed method (``set_xscale`` or ``set_yscale``).
    args : list
        Positional args as reconstructed for the call; ``args[0]`` is the scale.

    Notes
    -----
    This only warns -- it does not alter the call. matplotlib still receives the
    recorded scale and raises its own error for a truly invalid name, which the
    caller's try/except converts into a replay warning. The point is to make an
    unsupported scale visible instead of degrading silently to ``linear``.
    """
    if method_name not in ("set_xscale", "set_yscale"):
        return
    if not args:
        return
    scale = args[0]
    if isinstance(scale, str) and scale not in _SUPPORTED_SCALES:
        warnings.warn(
            f"{method_name} recorded an unsupported axis scale {scale!r}; "
            f"supported scales are {sorted(_SUPPORTED_SCALES)}. The axis may "
            "reproduce as linear if matplotlib cannot apply it.",
            stacklevel=2,
        )


__all__ = ["warn_if_unsupported_scale"]

# EOF
