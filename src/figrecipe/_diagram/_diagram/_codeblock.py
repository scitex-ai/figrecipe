#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Syntax-highlighted code rendering for codeblock diagram shapes.

Parses Emacs theme .el files for accurate colors. Supports any language
via pygments lexers and any Emacs theme via .el file parsing.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ._core import BoxSpec, PositionSpec

# Pygments token type → Emacs font-lock face name
_TOKEN_TO_FACE: Dict = {}

# Cache: theme_path → {face_name: {color, bold, italic}}
_THEME_CACHE: Dict[str, Dict] = {}


def _init_token_map():
    """Build mapping from pygments token types to Emacs font-lock face names."""
    if _TOKEN_TO_FACE:
        return
    try:
        from pygments.token import (
            Comment,
            Keyword,
            Name,
            Number,
            Operator,
            Punctuation,
            String,
        )

        _TOKEN_TO_FACE[Keyword] = "font-lock-keyword-face"
        _TOKEN_TO_FACE[Keyword.Namespace] = "font-lock-keyword-face"
        _TOKEN_TO_FACE[Keyword.Constant] = "font-lock-constant-face"
        _TOKEN_TO_FACE[Name.Function] = "font-lock-function-name-face"
        _TOKEN_TO_FACE[Name.Class] = "font-lock-type-face"
        _TOKEN_TO_FACE[Name.Builtin] = "font-lock-builtin-face"
        _TOKEN_TO_FACE[Name.Decorator] = "font-lock-function-name-face"
        _TOKEN_TO_FACE[Name.Variable] = "font-lock-variable-name-face"
        _TOKEN_TO_FACE[Name.Exception] = "font-lock-type-face"
        _TOKEN_TO_FACE[String] = "font-lock-string-face"
        _TOKEN_TO_FACE[String.Doc] = "font-lock-doc-face"
        _TOKEN_TO_FACE[Comment] = "font-lock-comment-face"
        _TOKEN_TO_FACE[Comment.Single] = "font-lock-comment-face"
        _TOKEN_TO_FACE[Comment.Multiline] = "font-lock-comment-face"
        _TOKEN_TO_FACE[Number] = "font-lock-constant-face"
        _TOKEN_TO_FACE[Number.Integer] = "font-lock-constant-face"
        _TOKEN_TO_FACE[Number.Float] = "font-lock-constant-face"
        _TOKEN_TO_FACE[Operator] = None  # default fg
        _TOKEN_TO_FACE[Punctuation] = None  # default fg
    except ImportError:
        pass


def parse_emacs_theme(el_path: str) -> Dict[str, Dict]:
    """Parse an Emacs theme .el file, returning font-lock face styles.

    Returns dict like::

        {"font-lock-keyword-face": {"color": "#F0DFAF", "bold": True, "italic": False},
         "font-lock-string-face":  {"color": "#CC9393", "bold": False, "italic": False},
         "_bg": "#3F3F3F", "_fg": "#DCDCCC"}
    """
    el_path = str(el_path)
    if el_path in _THEME_CACHE:
        return _THEME_CACHE[el_path]

    text = Path(el_path).read_text()

    # Step 1: Extract color palette (("name" . "#HEX") pairs)
    palette = {}
    for m in re.finditer(r'\("([^"]+)"\s*\.\s*"(#[0-9A-Fa-f]{6})"\)', text):
        palette[m.group(1)] = m.group(2)

    # Step 2: Extract font-lock face definitions
    # Pattern: `(font-lock-*-face ((t (:foreground ,var-name ...))))
    faces = {}
    face_re = re.compile(r"`\((font-lock-\S+-face)\s+\(\(t\s+\(([^)]+)\)\)\)\)")
    for m in face_re.finditer(text):
        face_name = m.group(1)
        props = m.group(2)
        color = None
        bold = "bold" in props
        italic = "italic" in props
        # :foreground ,zenburn-yellow
        fg_match = re.search(r":foreground\s+,(\S+)", props)
        if fg_match:
            var_name = fg_match.group(1)
            color = palette.get(var_name)
        faces[face_name] = {"color": color, "bold": bold, "italic": italic}

    # Store bg/fg/bg_dark from palette
    # Try theme-specific names first, then generic -bg/-fg suffix patterns
    bg_candidates = [k for k in palette if k.endswith("-bg")]
    fg_candidates = [k for k in palette if k.endswith("-fg")]
    bg_dark_candidates = [k for k in palette if k.endswith("-bg-1")]
    faces["_bg"] = (
        palette.get(bg_candidates[0], "#3F3F3F") if bg_candidates else "#3F3F3F"
    )
    faces["_fg"] = (
        palette.get(fg_candidates[0], "#DCDCCC") if fg_candidates else "#DCDCCC"
    )
    faces["_bg_dark"] = (
        palette.get(bg_dark_candidates[0], faces["_bg"])
        if bg_dark_candidates
        else faces["_bg"]
    )

    _THEME_CACHE[el_path] = faces
    return faces


# Built-in code palette, so a codeblock renders THE SAME EVERYWHERE.
#
# `_find_default_theme` below looks for zenburn-theme.el inside the AUTHOR'S
# Emacs installation, so a diagram's appearance depended on whether the machine
# doing the rendering happened to have Emacs and that theme:
#
#   developer box with Emacs   -> theme found, code coloured
#   CI / container / anyone    -> no theme, faces == {}, every token drawn in
#   else's laptop                 the default foreground: present but invisible
#
# Measured 2026-08-16: `_find_default_theme()` returns None in the agent
# container, and the concept diagram generated there was illegible — which is
# what the operator reported (「ターミナル？の文字見えるようにして欲しい」).
# Nothing errored. An absent theme just silently produced a worse picture, and a
# rendered artefact must not depend on ambient machine state like that.
#
# DELIBERATELY A LIGHT-BACKGROUND PALETTE. The codeblock panel is drawn LIGHT, so
# the token colours have to be dark. Zenburn — what the search finds — is a DARK
# theme: its pale yellows and dusty roses are chosen to sit on #3F3F3F, and on
# the light panel they are washed out. Matching the palette to the panel that is
# actually drawn is the fix; repainting the panel to suit the palette is not.
#
# No `_bg` / `_bg_dark` keys, on purpose: including them would repaint the panel,
# and the panel is not what needs changing. Omitting them leaves the existing
# fill alone, since `faces.get("_bg", fill)` then falls through to `fill`.
#
# A discovered .el still wins, so anyone who themes their Emacs keeps that.
_BUILTIN_LIGHT_FACES: Dict[str, Dict] = {
    "font-lock-keyword-face": {"color": "#a626a4", "bold": True, "italic": False},
    "font-lock-string-face": {"color": "#50a14f", "bold": False, "italic": False},
    "font-lock-comment-face": {"color": "#8a8f98", "bold": False, "italic": True},
    "font-lock-function-name-face": {"color": "#4078f2", "bold": False, "italic": False},
    "font-lock-variable-name-face": {"color": "#986801", "bold": False, "italic": False},
    "font-lock-constant-face": {"color": "#986801", "bold": False, "italic": False},
    "font-lock-type-face": {"color": "#0184bc", "bold": False, "italic": False},
    "font-lock-builtin-face": {"color": "#c18401", "bold": False, "italic": False},
    "_fg": "#1a2a40",  # SciTeX navy for unstyled tokens
}


def resolve_theme_faces() -> Dict[str, Dict]:
    """Return the code-block face palette, never empty.

    Prefers a zenburn-theme.el discovered on this machine so a user who themes
    their Emacs sees the same colours in their diagrams; falls back to the
    inlined palette so everyone else gets a legible code block instead of
    unstyled text.
    """
    theme_path = _find_default_theme()
    if theme_path:
        faces = parse_emacs_theme(theme_path)
        if faces:
            return faces
    return _BUILTIN_LIGHT_FACES


def _find_default_theme() -> Optional[str]:
    """Find zenburn-theme.el in common Emacs locations."""
    home = Path.home()
    for pattern in [
        home / ".emacs.d" / "elpa" / "zenburn-theme-*" / "zenburn-theme.el",
        home / ".dotfiles" / "**" / "zenburn-theme.el",
        home / ".dotfiles_public" / "**" / "zenburn-theme.el",
    ]:
        matches = sorted(Path("/").glob(str(pattern).lstrip("/")))
        if matches:
            return str(matches[-1])
    return None


def _tokenize_code(code: str, language: str) -> Optional[List[Tuple]]:
    """Tokenize code using pygments for any language."""
    try:
        from pygments.lexers import get_lexer_by_name

        lexer = get_lexer_by_name(language, stripall=False)
        return list(lexer.get_tokens(code))
    except Exception:
        return None


def _get_token_style(faces: Dict, token_type) -> Tuple[str, bool, bool]:
    """Map pygments token → (color, bold, italic) using parsed theme."""
    _init_token_map()
    fg = faces.get("_fg", "#DCDCCC")
    # Walk up token hierarchy
    t = token_type
    while t:
        if t in _TOKEN_TO_FACE:
            face_name = _TOKEN_TO_FACE[t]
            if face_name is None:
                return (fg, False, False)
            face = faces.get(face_name, {})
            return (
                face.get("color") or fg,
                face.get("bold", False),
                face.get("italic", False),
            )
        t = t.parent
    return (fg, False, False)


def _measure_char_width_mm(ax, fontsize, fontfamily="monospace") -> float:
    """Measure actual monospace character width in data (mm) coordinates.

    Uses two-point measurement to eliminate bbox padding bias:
    width = (bbox(60 chars) - bbox(20 chars)) / 40.
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    widths = []
    for n in (20, 60):
        t = ax.text(0, 0, "M" * n, fontsize=fontsize, fontfamily=fontfamily, alpha=0)
        bbox = t.get_window_extent(renderer)
        p0, p1 = inv.transform((bbox.x0, 0)), inv.transform((bbox.x1, 0))
        widths.append(p1[0] - p0[0])
        t.remove()

    return (widths[1] - widths[0]) / 40


def render_codeblock_text(
    ax: "Axes",
    pos: "PositionSpec",
    box: "BoxSpec",
    fill: str,
    title_color: str,
    colors: Dict,
) -> None:
    """Render syntax-highlighted code inside a codeblock box.

    Parses Emacs zenburn-theme.el for colors. Supports any pygments language.
    Falls back to plain monospace when pygments is unavailable.
    """
    bar_h = min(pos.height_mm * 0.18, 4.5)
    code_top = pos.y_mm + pos.height_mm / 2 - bar_h - box.padding_mm
    left_x = pos.x_mm - pos.width_mm / 2 + box.padding_mm
    code_fontsize = 7
    line_gap = 4.0

    # Title in the title bar
    ax.text(
        pos.x_mm,
        pos.y_mm + pos.height_mm / 2 - bar_h / 2,
        box.title,
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color="white",
        fontfamily="monospace",
        zorder=8,
    )

    # Tokenize
    code_text = "\n".join(str(line) for line in box.content)
    tokens = _tokenize_code(code_text, box.language)
    if tokens is None:
        _render_plain(ax, pos, box, fill, left_x, code_top, code_fontsize, line_gap)
        return

    # Code theme: a discovered Emacs theme, else the inlined palette. Never the
    # empty dict this used to fall back to — with no faces every token was drawn
    # in the default foreground on a panel that (for the same reason) stayed
    # light, so the code was there but effectively invisible.
    faces = resolve_theme_faces()

    # Measure char width
    char_width_mm = _measure_char_width_mm(ax, code_fontsize)

    # Render token by token
    cur_line = 0
    cur_col = 0
    for tok_type, tok_value in tokens:
        color, bold, italic = _get_token_style(faces, tok_type)
        for j, part in enumerate(tok_value.split("\n")):
            if j > 0:
                cur_line += 1
                cur_col = 0
            if not part:
                continue
            t = ax.text(
                left_x + cur_col * char_width_mm,
                code_top - cur_line * line_gap,
                part,
                ha="left",
                va="top",
                fontsize=code_fontsize,
                fontfamily="monospace",
                fontweight="bold" if bold else "normal",
                fontstyle="italic" if italic else "normal",
                color=color,
                zorder=7,
            )
            t.set_label("__codeblock_internal__")
            cur_col += len(part)


def _render_plain(ax, pos, box, fill, left_x, code_top, fontsize, line_gap):
    """Fallback: plain monospace rendering without highlighting."""
    _bg = dict(facecolor=fill, edgecolor="none", pad=0.3, alpha=0.85)
    for i, line in enumerate(box.content):
        t = ax.text(
            left_x,
            code_top - i * line_gap,
            str(line),
            ha="left",
            va="top",
            fontsize=fontsize,
            fontfamily="monospace",
            color="#DCDCCC",
            zorder=7,
            bbox=_bg,
        )
        t.set_label("__codeblock_internal__")


# EOF
