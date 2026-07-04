#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic label declutter for ``scatter_labels(declutter=True)``.

The solver (``_solver``) is pure geometry: it runs ONCE at record time and
returns resolved label positions. The caller emits those positions as ordinary
recorded ``text``/``annotate`` calls, so replay is byte-identical with no solver
in the replay path (see the figrecipe-scatter-labels-declutter design).
"""

from ._solver import solve_label_positions

__all__ = ["solve_label_positions"]

# EOF
