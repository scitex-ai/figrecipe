#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Caption content validation — figrecipe's own (independent) rules.

figrecipe owns figure captions canonically (``metadata.caption`` /
``figure.panel_captions`` in the recipe YAML, plus the caption-only ``<stem>.tex``
it emits). These checks fail LOUD on caption text that is known to break
downstream LaTeX, so the problem is caught at figure-build/save time rather than
at manuscript-compile time.

This rule is INTENTIONALLY independent of scitex-writer's equivalent
manuscript-side rule — each tool owns and enforces its own copy.

Rule FR-CAP-001 — no ``\footnote`` in captions:
    ``\footnote`` (and the ``\footnotemark``/``\footnotetext`` family) inside a
    figure caption breaks LaTeX in spanning floats (``figure*``): the ``\caption``
    argument is read in a context where ``\footnote`` triggers
    ``\caption@ydblarg`` "Argument ... has an extra }" and a runaway
    ``\@xfootnote``. Inline the footnote text into the caption instead.
"""

from typing import Optional

__all__ = ["FootnoteInCaptionError", "check_caption_latex_safe"]

# The LaTeX command (with backslash). Matching this substring also catches
# \footnotemark / \footnotetext, which are equally unwelcome in a caption.
_FOOTNOTE_TOKEN = "\\footnote"


class FootnoteInCaptionError(ValueError):
    """Raised when a figure caption contains a ``\\footnote`` command."""


def check_caption_latex_safe(text: Optional[str], where: str) -> None:
    r"""Raise :class:`FootnoteInCaptionError` if *text* contains ``\footnote``.

    Parameters
    ----------
    text : str or None
        Caption text to check. ``None``/empty is allowed (no-op).
    where : str
        Human description of the caption's origin, surfaced in the error so the
        caller knows exactly which caption/panel (and file) is offending —
        e.g. ``"the figure caption"`` or ``"the panel B caption of fig01.yaml"``.
    """
    if not text:
        return
    if _FOOTNOTE_TOKEN in str(text):
        raise FootnoteInCaptionError(
            f"figrecipe [FR-CAP-001]: \\footnote is not allowed in {where}. "
            r"\footnote inside a figure caption breaks LaTeX in spanning floats "
            r"(figure*): it triggers \caption@ydblarg 'extra }' and a runaway "
            r"\@xfootnote. Inline the footnote text into the caption instead."
        )
