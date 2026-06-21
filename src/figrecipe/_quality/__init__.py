#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe._quality — runtime validators, linter plugin, axis alignment + overlap checks.

Topical grouping of figrecipe's quality-gate modules. These siblings used
to live as flat `_<module>.py` files at the package root; they were grouped
here because they share a single responsibility (figure-shape correctness
checks fired at save-time, lint-time, or runtime), and because flat-file
count at the package root was tripping the `scitex-dev ecosystem audit-all`
project-structure rule (PS series, "16 flat .py files, threshold 15").

Members
-------
- ``_validator``                 ValidationResult + save-time validators
- ``_axis_range_alignment``      runtime check (peer-grouped axes with shared
                                   axis labels must share their numeric range)
- ``_axis_alignment_checker``    AxisAlignmentChecker — the AST-side STX-FIG001
                                   linter-plugin worker
- ``_linter_plugin``             pytest/flake8 plugin entry-point that loads
                                   AxisAlignmentChecker
- ``_overlap``                   save-time layout-conflict (overlap) detector:
                                   enumerate components, consult one policy
                                   table per pair, warn on forbidden overlaps

All modules remain underscore-prefixed (private surface); the public figrecipe
API (figrecipe.fr.*) is unaffected by the move.
"""

from ._overlap import (
    Conflict,
    detect_layout_conflicts,
    run_overlap_check,
)

__all__ = [
    "Conflict",
    "detect_layout_conflicts",
    "run_overlap_check",
]

# EOF
