#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scientific caption system for publication-ready figures.

This module provides a comprehensive caption system supporting:
- Figure-level captions with automatic numbering
- Panel-level captions (A, B, C, etc.)
- Cross-references
- Multiple formatting styles (scientific, nature, ieee, apa)
- Export to TXT, TeX, and Markdown formats

Usage
-----
>>> import figrecipe as fr
>>> fig, ax = fr.subplots()
>>> ax.plot([1, 2, 3], [1, 4, 9])
>>> fr.add_figure_caption(fig, "Example plot showing quadratic growth.")

For multiple panels:
>>> fig, axes = fr.subplots(1, 2)
>>> axes[0].plot([1, 2, 3], [1, 4, 9])
>>> axes[1].bar([1, 2, 3], [1, 2, 3])
>>> fr.add_panel_captions(fig, axes, ["Line plot", "Bar plot"])
"""

from ._caption import ScientificCaption, caption_manager
from ._convenience import (
    add_figure_caption,
    add_panel_captions,
    create_figure_list,
    cross_ref,
    export_captions,
    quick_caption,
    save_caption_multiple_formats,
)
from ._formats import (
    create_latex_figure_list,
    create_markdown_figure_list,
    create_text_figure_list,
    escape_latex,
    format_caption_for_md,
    format_caption_for_tex,
    format_caption_for_txt,
)
from ._validate import FootnoteInCaptionError, check_caption_latex_safe

__all__ = [
    # Validation (FR-CAP-001)
    "FootnoteInCaptionError",
    "check_caption_latex_safe",
    # Core class
    "ScientificCaption",
    "caption_manager",
    # Convenience functions
    "add_figure_caption",
    "add_panel_captions",
    "export_captions",
    "cross_ref",
    "create_figure_list",
    "quick_caption",
    "save_caption_multiple_formats",
    # Format utilities
    "format_caption_for_txt",
    "format_caption_for_tex",
    "format_caption_for_md",
    "escape_latex",
    "create_text_figure_list",
    "create_latex_figure_list",
    "create_markdown_figure_list",
]
