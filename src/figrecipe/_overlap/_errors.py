#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exceptions for overlap detection."""

from __future__ import annotations

from typing import List, Optional


class OverlapError(ValueError):
    """Raised when figrecipe detects overlap with ``policy='strict'``.

    Parameters
    ----------
    message : str
        Human-readable description naming the colliding elements and
        panel.
    elements : list of str, optional
        IDs of the colliding elements (e.g. ``['plot_000', 'plot_001']``).
    axes_key : str, optional
        The figrecipe axes key (e.g. ``ax_0_0``) where the collision was
        detected.
    kind : str, optional
        ``'shape'``, ``'color'``, or ``'legend'`` — which detector fired.
    """

    def __init__(
        self,
        message: str,
        elements: Optional[List[str]] = None,
        axes_key: Optional[str] = None,
        kind: Optional[str] = None,
    ):
        super().__init__(message)
        self.elements = list(elements) if elements else []
        self.axes_key = axes_key
        self.kind = kind


__all__ = ["OverlapError"]
