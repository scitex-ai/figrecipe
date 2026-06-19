#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Overlap-policy resolution.

Three knobs cascade, in priority order:

1. Per-element flag set via ``allow_overlap="warn"`` (or ``"off"``)
   recorded on the artist by the figrecipe wrappers.
2. Per-axes ``overlap_policy`` attribute on the matplotlib Axes
   (``_figrecipe_overlap_policy``).
3. Per-figure ``overlap_policy`` attribute on the Figure
   (``_figrecipe_overlap_policy``).
4. Global default — ``'strict'`` for shape, ``'warn'`` for color,
   ``'warn'`` for legend.

A policy is one of three strings:

* ``'strict'`` — raise :class:`figrecipe.OverlapError`
* ``'warn'``   — emit a UserWarning, attach to the FigureRecord
* ``'off'``    — do not detect (reluctantly allowed escape hatch — the
  DEFAULT remains ``'strict'``; ``'off'`` exists only for legacy
  notebooks that the operator can audit later)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

PolicyLevel = Literal["strict", "warn", "off"]
DetectorKind = Literal["shape", "color", "legend"]


@dataclass(frozen=True)
class OverlapPolicy:
    """Effective policy for one detector kind on one axes."""

    shape: PolicyLevel = "strict"
    color: PolicyLevel = "warn"
    legend: PolicyLevel = "warn"

    def for_kind(self, kind: DetectorKind) -> PolicyLevel:
        return getattr(self, kind)


_VALID = {"strict", "warn", "off"}


def _coerce(value, fallback: PolicyLevel) -> PolicyLevel:
    if value is None:
        return fallback
    if isinstance(value, str) and value.lower() in _VALID:
        return value.lower()  # type: ignore[return-value]
    return fallback


def resolve_policy(
    fig=None,
    ax=None,
    artist=None,
    *,
    fig_default: Optional[PolicyLevel] = None,
    kind: DetectorKind = "shape",
) -> PolicyLevel:
    """Resolve effective policy by walking artist → axes → figure → default."""
    # Per-artist opt-in (typical KDE / density use case).
    if artist is not None:
        artist_pol = getattr(artist, "_figrecipe_allow_overlap", None)
        if artist_pol is not None:
            return _coerce(artist_pol, fallback="warn")

    # Per-axes override.
    if ax is not None:
        ax_pol_obj = getattr(ax, "_figrecipe_overlap_policy", None)
        if isinstance(ax_pol_obj, OverlapPolicy):
            return ax_pol_obj.for_kind(kind)
        if isinstance(ax_pol_obj, str):
            return _coerce(ax_pol_obj, fallback=_default_for_kind(kind))

    # Per-figure override.
    if fig is not None:
        mpl_fig = getattr(fig, "_fig", fig)
        fig_pol_obj = getattr(mpl_fig, "_figrecipe_overlap_policy", None)
        if isinstance(fig_pol_obj, OverlapPolicy):
            return fig_pol_obj.for_kind(kind)
        if isinstance(fig_pol_obj, str):
            return _coerce(fig_pol_obj, fallback=_default_for_kind(kind))

    if fig_default is not None:
        return fig_default

    return _default_for_kind(kind)


def _default_for_kind(kind: DetectorKind) -> PolicyLevel:
    if kind == "shape":
        return "strict"
    return "warn"


def set_figure_policy(fig, policy) -> None:
    """Attach a policy to a figure (used by ``fr.compose(overlap_policy=...)``)."""
    mpl_fig = getattr(fig, "_fig", fig)
    if isinstance(policy, str):
        s = _coerce(policy, fallback="strict")
        mpl_fig._figrecipe_overlap_policy = OverlapPolicy(shape=s, color=s, legend=s)
    elif isinstance(policy, OverlapPolicy):
        mpl_fig._figrecipe_overlap_policy = policy
    elif isinstance(policy, dict):
        mpl_fig._figrecipe_overlap_policy = OverlapPolicy(
            shape=_coerce(policy.get("shape"), fallback="strict"),
            color=_coerce(policy.get("color"), fallback="warn"),
            legend=_coerce(policy.get("legend"), fallback="warn"),
        )
    elif policy is None:
        mpl_fig._figrecipe_overlap_policy = None


def set_axes_policy(ax, policy) -> None:
    """Attach a policy to a single Axes."""
    if isinstance(policy, str):
        s = _coerce(policy, fallback="strict")
        ax._figrecipe_overlap_policy = OverlapPolicy(shape=s, color=s, legend=s)
    elif isinstance(policy, (OverlapPolicy, type(None))):
        ax._figrecipe_overlap_policy = policy
    elif isinstance(policy, dict):
        ax._figrecipe_overlap_policy = OverlapPolicy(
            shape=_coerce(policy.get("shape"), fallback="strict"),
            color=_coerce(policy.get("color"), fallback="warn"),
            legend=_coerce(policy.get("legend"), fallback="warn"),
        )


__all__ = [
    "OverlapPolicy",
    "PolicyLevel",
    "DetectorKind",
    "resolve_policy",
    "set_figure_policy",
    "set_axes_policy",
]
