#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loosely-coupled scitex-clew provenance recording for figrecipe I/O.

figrecipe records the recipe + data files it writes/reads with scitex-clew
WHEN clew is installed and a ``@stx.session`` is active, so figures and
compositions become nodes in the Clew provenance DAG: a composed figure's
recipe -> its source panel recipes/data -> ... -> raw data. This is what keeps
the provenance chain connected through composition.

Loosely coupled, leaf-respecting (scitex-clew depends on nothing; producers opt
in): clew is reached via scitex-dev's ``try_import_optional`` -- if clew (or
scitex-dev) is absent, or no session is active, every call is a no-op.
Recording is best-effort *observability*; a failure here is logged at debug and
never breaks figrecipe's real save/load (which stays fail-loud on data errors).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

_logger = logging.getLogger(__name__)


def _active_tracker():
    """Return scitex-clew's active-session tracker, or None (no-op safe)."""
    try:
        from scitex_dev import try_import_optional

        clew = try_import_optional("scitex_clew")
        if clew is None:
            return None
        return clew.get_tracker()
    except Exception as exc:  # optional path: clew/scitex-dev unavailable
        _logger.debug("figrecipe: scitex-clew unavailable (%s)", exc)
        return None


def record_output(path: Union[str, Path]) -> None:
    """Record ``path`` as a clew output of the active session (best-effort)."""
    tracker = _active_tracker()
    if tracker is None:
        return
    try:
        tracker.record_output(str(path))
    except Exception as exc:  # never break the real save
        _logger.debug("figrecipe: clew record_output(%s) failed: %s", path, exc)


def record_input(path: Union[str, Path]) -> None:
    """Record ``path`` as a clew input of the active session (best-effort).

    clew auto-links the session(s) that produced ``path`` as parents, which is
    what connects a composed figure to its source panels.
    """
    tracker = _active_tracker()
    if tracker is None:
        return
    try:
        tracker.record_input(str(path))
    except Exception as exc:  # never break the real load
        _logger.debug("figrecipe: clew record_input(%s) failed: %s", path, exc)


__all__ = ["record_input", "record_output"]

# EOF
