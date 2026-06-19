#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Overlap audit hook used by ``save_figure``.

Extracted to keep ``_save.py`` focused on the I/O pipeline; the audit
itself lives in :mod:`figrecipe._overlap`.
"""

from __future__ import annotations

import os
import warnings
from typing import Optional


def _env_disabled() -> bool:
    val = os.environ.get("FIGRECIPE_OVERLAP_DISABLE", "")
    return val.lower() in {"1", "true", "yes", "on"}


def run_overlap_audit_for_save(fig, overlap_policy: Optional[str]) -> None:
    """Pre-save overlap audit.

    Resolution order:

    1. Explicit ``overlap_policy`` kwarg → temporarily set on the
       figure for the duration of this call.
    2. Otherwise: figure-level attribute (set by ``fr.compose``).
    3. Otherwise: detector defaults
       (shape=strict, color=warn, legend=warn).

    Set ``FIGRECIPE_OVERLAP_DISABLE=1`` in the environment to disable
    the audit (used by the test suite and CI when explicitly opted out).
    """
    if _env_disabled():
        return

    from .._overlap._core import run_overlap_audit
    from .._overlap._policy import set_figure_policy

    prior = None
    if overlap_policy is not None:
        mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
        prior = getattr(mpl_fig, "_figrecipe_overlap_policy", None)
        set_figure_policy(fig, overlap_policy)

    try:
        run_overlap_audit(fig)
    except Exception as exc:
        # Re-raise OverlapError (strict-policy failure); other exceptions
        # (e.g. malformed figure objects in tests) downgrade to warning
        # so we never break a save on a detector bug.
        from .._overlap._errors import OverlapError

        if isinstance(exc, OverlapError):
            raise
        warnings.warn(
            f"figrecipe overlap audit skipped due to detector error: {exc!r}",
            UserWarning,
            stacklevel=2,
        )
    finally:
        if overlap_policy is not None:
            mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
            mpl_fig._figrecipe_overlap_policy = prior


__all__ = ["run_overlap_audit_for_save"]
