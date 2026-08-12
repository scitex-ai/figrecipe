#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Warn when a caller's kwarg overrides a SCITEX_STYLE default.

Agent-written plotting code drifts off-theme silently: ``ax.set_title("...",
fontsize=14)`` quietly wins over ``SCITEX_STYLE.fonts.title_pt = 8`` and nothing
says so. This module makes that drift visible, reporting what the default is,
what it was overridden with, and **the caller's** file/line/function - never a
figrecipe-internal frame.

Silencing it:

- ``no_warn_style=True`` on the individual call, or
- ``FIGRECIPE_NO_WARN_STYLE=1`` in the environment, for a whole script.

Nothing here changes the value that reaches matplotlib: the override still
applies. The warning is feedback, not enforcement.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

#: Opt-out kwarg consumed by :func:`warn_style_overrides` (never forwarded to
#: matplotlib, which would raise on an unexpected keyword).
NO_WARN_KWARG = "no_warn_style"

#: Whole-script opt-out.
NO_WARN_ENV = "FIGRECIPE_NO_WARN_STYLE"

#: ``method name -> {caller kwarg: SCITEX_STYLE dotted path}``.
#:
#: Only the ``fonts`` group is tracked for now (the issue's initial set). Several
#: matplotlib aliases map to the same style key: ``size`` is an accepted synonym
#: of ``fontsize`` on text-bearing setters, and ``labelsize`` is the tick
#: equivalent.
TRACKED_KWARGS: Dict[str, Dict[str, str]] = {
    "set_title": {"fontsize": "fonts.title_pt", "size": "fonts.title_pt"},
    "set_xlabel": {"fontsize": "fonts.axis_label_pt", "size": "fonts.axis_label_pt"},
    "set_ylabel": {"fontsize": "fonts.axis_label_pt", "size": "fonts.axis_label_pt"},
    "suptitle": {"fontsize": "fonts.suptitle_pt", "size": "fonts.suptitle_pt"},
    "legend": {"fontsize": "fonts.legend_pt"},
    "text": {"fontsize": "fonts.annotation_pt", "size": "fonts.annotation_pt"},
    "annotate": {"fontsize": "fonts.annotation_pt", "size": "fonts.annotation_pt"},
    "tick_params": {"labelsize": "fonts.tick_label_pt"},
}

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent


class StyleOverrideWarning(UserWarning):
    """A caller kwarg overrode a SCITEX_STYLE default.

    A dedicated subclass so it can be filtered on its own
    (``warnings.simplefilter("ignore", StyleOverrideWarning)``) without
    suppressing every other ``UserWarning`` figrecipe emits.
    """


def _style_default(dotted_path: str) -> Any:
    """The SCITEX_STYLE value at ``dotted_path``, or None if unavailable.

    Goes through ``resolve_style_value`` rather than reading the YAML directly, so
    an env-var or user-set override counts as *the default* here - the point is to
    flag divergence from the style actually in force.
    """
    from ..presets._scitex_style import resolve_style_value

    return resolve_style_value(dotted_path, type=float)


def _is_internal(filename: str) -> bool:
    """True for figrecipe's own frames and for import machinery.

    Pseudo-filenames like ``<stdin>`` and ``<string>`` are treated as *external*:
    a REPL or ``-c`` caller has no real file, but reporting ``<stdin>:3`` still
    localises the override better than giving up. ``<frozen ...>`` frames are the
    import bootstrap and are never the interesting caller.
    """
    if not filename:
        return True
    if filename.startswith("<"):
        return filename.startswith("<frozen")
    try:
        return Path(filename).resolve().is_relative_to(_PACKAGE_ROOT)
    except (OSError, ValueError):  # unresolvable path: treat as external
        return False


def _caller_site() -> Optional[Tuple[str, int, str]]:
    """The nearest frame outside figrecipe, as ``(file, line, function)``.

    ``warnings.warn(stacklevel=N)`` cannot be used for this: N differs per entry
    point (a direct ``ax.set_title`` is a different depth from a call routed
    through a wrapper factory), so the frame is located by walking out instead.
    """
    depth = 1
    while True:
        try:
            frame = sys._getframe(depth)
        except ValueError:  # walked off the top of the stack
            return None
        filename = frame.f_code.co_filename
        if not _is_internal(filename):
            return filename, frame.f_lineno, frame.f_code.co_name
        depth += 1


def _comparable(value: Any) -> Optional[float]:
    """``value`` as a float, or None when it is not numerically comparable.

    Matplotlib accepts named sizes (``"large"``, ``"x-small"``) as well as
    points. Those are not compared: mapping a name onto points needs matplotlib's
    own font-scaling table, and guessing would produce false warnings.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def format_override_warning(
    key: str,
    dotted_path: str,
    default: Any,
    override: Any,
    site: Optional[Tuple[str, int, str]],
) -> str:
    """The warning text. Kept separate so tests can assert on it directly."""
    where = "unknown call site"
    if site is not None:
        filename, lineno, function = site
        where = f"{filename}:{lineno}  in {function}()"
    return (
        "figrecipe: SCITEX_STYLE default overridden\n"
        f"  what:     {key} = {default}        (SCITEX_STYLE.{dotted_path})\n"
        f"  override: {key} = {override}\n"
        f"  at:       {where}\n"
        "\n"
        f"If intentional (off-theme): pass `{NO_WARN_KWARG}=True` to silence locally,\n"
        f"or set SCITEX_STYLE.{dotted_path} globally to re-theme."
    )


def warn_style_overrides(method_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Warn for each tracked kwarg in ``kwargs`` that diverges from SCITEX_STYLE.

    Returns ``kwargs`` with the :data:`NO_WARN_KWARG` control key removed, so the
    result is safe to forward to matplotlib. The tracked values themselves are
    left untouched - the override still takes effect.
    """
    silenced = bool(kwargs.pop(NO_WARN_KWARG, False))
    tracked = TRACKED_KWARGS.get(method_name)
    if tracked is None or silenced or os.environ.get(NO_WARN_ENV, "") not in ("", "0"):
        return kwargs

    site = None
    for key, dotted_path in tracked.items():
        if key not in kwargs:
            continue
        override = _comparable(kwargs[key])
        default = _comparable(_style_default(dotted_path))
        if override is None or default is None or override == default:
            continue
        if site is None:  # resolved lazily: only pay for it when warning
            site = _caller_site()
        warnings.warn(
            format_override_warning(key, dotted_path, default, override, site),
            StyleOverrideWarning,
            stacklevel=2,
        )
    return kwargs
