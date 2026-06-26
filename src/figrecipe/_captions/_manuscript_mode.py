#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manuscript mode: keep captions canonical, suppress the on-canvas copy.

In a manuscript build the figure caption is typeset by LaTeX (from the emitted
``<stem>.tex`` sidecar), so baking the caption onto the PNG would double-render
it (pixels + ``\\caption``). Manuscript mode makes ``add_figure_caption`` /
compose record the caption in the recipe (``metadata.caption`` /
``figure.panel_captions``) and emit the ``.tex`` sidecar, but NOT draw the
caption onto the canvas (and not record it as a replayed ``figure_texts``
entry). The drawn copy and the ``.tex`` are derived views; the YAML stays the
single source of truth.

Toggle via :func:`set_manuscript_mode`, the :func:`manuscript_mode` context
manager, or the ``FIGRECIPE_MANUSCRIPT_MODE`` environment variable.
"""

import os
from contextlib import contextmanager

__all__ = ["set_manuscript_mode", "is_manuscript_mode", "manuscript_mode"]

_MANUSCRIPT_MODE = False

_TRUTHY = {"1", "true", "yes", "on"}


def set_manuscript_mode(on: bool = True) -> None:
    """Enable/disable manuscript mode process-wide."""
    global _MANUSCRIPT_MODE
    _MANUSCRIPT_MODE = bool(on)


def is_manuscript_mode() -> bool:
    """True when manuscript mode is active (explicit flag OR env var)."""
    if _MANUSCRIPT_MODE:
        return True
    return os.environ.get("FIGRECIPE_MANUSCRIPT_MODE", "").strip().lower() in _TRUTHY


@contextmanager
def manuscript_mode(on: bool = True):
    """Context manager that sets manuscript mode for the enclosed block."""
    global _MANUSCRIPT_MODE
    prev = _MANUSCRIPT_MODE
    _MANUSCRIPT_MODE = bool(on)
    try:
        yield
    finally:
        _MANUSCRIPT_MODE = prev
