#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""What figrecipe answers to when a script uses it AS ``plt``.

scitex-session can inject figrecipe in place of ``matplotlib.pyplot``. figrecipe
answers to ``subplots``, which is exactly the call that convinces a script it
holds pyplot — and then the next pyplot call used to die with a bare
``AttributeError: module 'figrecipe' has no attribute 'rcParams'``, pointing the
author at nothing. The author reasonably concludes their script is wrong; in
fact the substitution is incomplete.

This module turns that dead end into a signpost. It does NOT make figrecipe a
drop-in pyplot: a blind passthrough would be a REGRESSION, because the calls
authors reach for first are the ones that defeat figrecipe's guarantees —

  * ``figure()`` / ``gca()`` / ``savefig()`` create or write RAW matplotlib
    artifacts the recorder never sees, so the figure silently stops being
    reproducible. That is the raw-matplotlib-bypass anti-pattern figrecipe's
    own linter flags.
  * mutating ``rcParams`` globally fights the style system, which exists to stop
    exactly that (the hardcoded-font problem).

So each known pyplot name either names its figrecipe equivalent or says plainly
that it is deliberately not proxied and why. Only names that cannot create an
unrecorded artifact are passed through.

Whether figrecipe should become a TRUE drop-in is a larger decision and is not
taken here — it must not be reached by accreting passthroughs one
AttributeError at a time.
"""

from typing import Any, Callable, Optional

#: Passed straight through to pyplot. Display/lifecycle only — these cannot
#: create or write an artifact, so proxying them costs no reproducibility.
#: ``close`` is also already special-cased by figrecipe (_patch_pyplot_close).
_PROXIED = frozenset({"close", "show"})

#: Names with a direct figrecipe counterpart. Value completes the sentence
#: "use ...".
_EQUIVALENTS = {
    "figure": (
        "use `fig, ax = figrecipe.subplots(...)`, which returns a figure already "
        "wrapped for recording. `plt.figure()` is not proxied because a raw "
        "matplotlib figure is invisible to the recorder, so it would save with no "
        "recipe behind it"
    ),
    "subplot": "use `figrecipe.subplots(nrows, ncols)` and index the returned axes",
    "savefig": (
        "use `figrecipe.save(fig, path)` — or `fig.savefig(path)` on the figure "
        "`subplots()` returned. Module-level `plt.savefig()` is not proxied "
        "because it writes pixels for whatever figure pyplot considers current, "
        "with no recipe, which is the one thing figrecipe exists to prevent"
    ),
    "rcParams": (
        "use `figrecipe.load_style(...)` / `figrecipe.apply_style(...)`, or pass "
        "`style={...}` to `figrecipe.subplots(...)`. Global rcParams mutation is "
        "not proxied because it fights the style system and leaks settings into "
        "every later figure in the process"
    ),
    "rc": (
        "use `figrecipe.load_style(...)` or `figrecipe.subplots(style={...})` — "
        "see `rcParams` above for why global rc mutation is not proxied"
    ),
    "gca": (
        "use the `ax` that `figrecipe.subplots()` returned. figrecipe is "
        "explicit-axes and keeps no current-axes state, so there is nothing for "
        "`gca()` to return"
    ),
    "gcf": (
        "use the `fig` that `figrecipe.subplots()` returned. figrecipe keeps no "
        "current-figure state"
    ),
    "tight_layout": (
        "size the layout up front with `figrecipe.subplots(axes_width_mm=..., "
        "margin_left_mm=..., space_w_mm=...)`, or pass "
        "`constrained_layout=True`. figrecipe lays out in millimetres so the "
        "saved figure matches the recipe"
    ),
    "subplots_adjust": (
        "use the millimetre layout arguments of `figrecipe.subplots(...)` "
        "(`margin_*_mm`, `space_*_mm`)"
    ),
}

#: pyplot state-machine functions whose axes counterpart is ``ax.set_<name>``.
_AX_SETTERS = frozenset(
    {"xlabel", "ylabel", "title", "xlim", "ylim", "xticks", "yticks", "xscale", "yscale"}
)

#: pyplot state-machine functions whose axes counterpart has the SAME name.
_AX_DIRECT = frozenset(
    {
        "annotate", "axhline", "axhspan", "axvline", "axvspan", "bar", "barh",
        "boxplot", "contour", "contourf", "errorbar", "fill_between",
        "fill_betweenx", "grid", "hist", "hist2d", "imshow", "legend", "loglog",
        "pcolormesh", "pie", "plot", "scatter", "semilogx", "semilogy", "step",
        "stem", "text", "violinplot",
    }
)


def _axes_hint(name: str) -> str:
    """Guidance for a pyplot state-machine call, naming the axes method."""
    if name in _AX_SETTERS:
        method = f"ax.set_{name}(...)"
        extra = (
            " — or `ax.set_xyt(xlabel, ylabel, title)` to set all three at once"
            if name in ("xlabel", "ylabel", "title")
            else ""
        )
    else:
        method = f"ax.{name}(...)"
        extra = ""
    return (
        f"figrecipe has no pyplot state machine, so there is no implicit current "
        f"axes to act on. Take the axes from `fig, ax = figrecipe.subplots()` and "
        f"call `{method}`, which IS recorded{extra}"
    )


def pyplot_proxy(name: str) -> Optional[Callable[..., Any]]:
    """Return pyplot's ``name`` if figrecipe deliberately proxies it, else None."""
    if name not in _PROXIED:
        return None
    import matplotlib.pyplot as plt

    return getattr(plt, name, None)


def pyplot_guidance(name: str) -> Optional[str]:
    """Return actionable guidance for a pyplot name, or None if unrelated.

    None means "this is not a pyplot name either" — a genuine unknown attribute,
    which the caller should report as the plain AttributeError it is.
    """
    if name in _EQUIVALENTS:
        return _EQUIVALENTS[name]
    if name in _AX_SETTERS or name in _AX_DIRECT:
        return _axes_hint(name)

    # Any other pyplot name: say so rather than leaving the author guessing
    # whether they typo'd. Imported lazily and only on the failure path.
    try:
        import matplotlib.pyplot as plt
    except Exception:  # pragma: no cover - matplotlib is a hard dependency
        return None
    if hasattr(plt, name):
        return (
            f"`matplotlib.pyplot.{name}` exists, but figrecipe is NOT a drop-in "
            f"pyplot replacement — it deliberately exposes only the surface it "
            f"can record and style. If this script was handed figrecipe as "
            f"`plt`, either use the figrecipe equivalent or import pyplot "
            f"explicitly for this call, accepting that whatever it draws will "
            f"not be in the recipe"
        )
    return None


__all__ = [
    "pyplot_guidance",
    "pyplot_proxy",
]
