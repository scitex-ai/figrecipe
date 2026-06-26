#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caption format utilities for multiple output formats."""

__all__ = [
    "format_caption_for_txt",
    "format_caption_for_tex",
    "format_caption_only_tex",
    "format_caption_for_md",
    "escape_latex",
    "create_text_figure_list",
    "create_latex_figure_list",
    "create_markdown_figure_list",
]

import textwrap
from pathlib import Path
from typing import Any, Dict, Optional


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters.

    Parameters
    ----------
    text : str
        Text to escape.

    Returns
    -------
    str
        Text with LaTeX special characters escaped.
    """
    # Backslash must be escaped first to avoid double-escaping
    result = text.replace("\\", r"\textbackslash{}")

    # Then escape other special characters
    escapes = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("^", r"\textasciicircum{}"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
    ]
    for char, escape in escapes:
        result = result.replace(char, escape)
    return result


def format_caption_for_txt(
    caption: str, figure_label: str, style: str, wrap_width: int
) -> str:
    """Format caption for plain text file.

    Parameters
    ----------
    caption : str
        The caption text.
    figure_label : str
        Figure label (e.g., "Figure 1").
    style : str
        Caption style: "scientific", "nature", "ieee", "apa".
    wrap_width : int
        Text wrapping width.

    Returns
    -------
    str
        Formatted plain text caption.
    """
    wrapped_text = textwrap.fill(caption, width=wrap_width)
    styles = {
        "scientific": f"{figure_label}. {wrapped_text}",
        "nature": f"{figure_label} | {wrapped_text}",
        "ieee": f"{figure_label}. {wrapped_text}",
        "apa": f"{figure_label}\n{wrapped_text}",
    }
    return styles.get(style, f"{figure_label}. {wrapped_text}")


def format_caption_for_tex(
    caption: str, figure_label: str, style: str, wrap_width: int
) -> str:
    """Format caption for LaTeX file.

    Parameters
    ----------
    caption : str
        The caption text.
    figure_label : str
        Figure label (e.g., "Figure 1").
    style : str
        Caption style: "scientific", "nature", "ieee", "apa".
    wrap_width : int
        Text wrapping width.

    Returns
    -------
    str
        Formatted LaTeX caption with figure environment.
    """
    tex_caption = escape_latex(caption)
    wrapped_text = textwrap.fill(tex_caption, width=wrap_width)
    label_slug = figure_label.lower().replace(" ", "_")

    if style == "scientific":
        return f"""% {figure_label} caption
\\begin{{figure}}[htbp]
    \\centering
    % \\includegraphics{{figure_filename}}
    \\caption{{\\textbf{{{figure_label}.}} {wrapped_text}}}
    \\label{{fig:{label_slug}}}
\\end{{figure}}

% For use in manuscript:
% \\textbf{{{figure_label}.}} {wrapped_text}
"""
    elif style == "nature":
        return f"""% {figure_label} caption (Nature style)
\\begin{{figure}}[htbp]
    \\centering
    % \\includegraphics{{figure_filename}}
    \\caption{{\\textbf{{{figure_label} |}} {wrapped_text}}}
    \\label{{fig:{label_slug}}}
\\end{{figure}}
"""
    else:
        return f"""% {figure_label} caption
\\begin{{figure}}[htbp]
    \\centering
    % \\includegraphics{{figure_filename}}
    \\caption{{{figure_label}. {wrapped_text}}}
    \\label{{fig:{label_slug}}}
\\end{{figure}}
"""


def format_caption_only_tex(
    caption: str,
    label_slug: Optional[str] = None,
) -> str:
    r"""Format a caption as a bare ``\caption{...}`` (+ optional ``\label``).

    Unlike :func:`format_caption_for_tex`, this emits NO ``\begin{figure}``
    wrapper, so the fragment can be ``\input`` directly inside a manuscript's
    own float (e.g. scitex-writer's ``\begin{figure*}``) without nesting two
    figure environments.

    The figure NUMBER is intentionally never injected: LaTeX numbers the float
    where the fragment is included, so a hardcoded ``Figure N.`` here would
    fight the manuscript's own numbering. The caption text is emitted verbatim
    (LaTeX-escaped); any bold lead-in is the caption author's responsibility.

    Parameters
    ----------
    caption : str
        Caption text (already assembled; for composed figures this is the
        figure-level caption with per-panel ``(A) ...`` lines folded in).
    label_slug : str, optional
        When given, append ``\label{fig:<slug>}`` (typically the recipe stem),
        so a standalone fragment can ``\ref{fig:<stem>}``. When ``None`` (the
        manuscript-symlink path), the ``\label`` is OMITTED so the consumer
        (scitex-writer) can deterministically auto-label by the SYMLINK
        filename stem — a hardcoded label would otherwise win and break
        ``\ref{fig:<filename-stem>}``.

    Returns
    -------
    str
        ``"\\caption{...}\n"`` and, when ``label_slug`` is set, a following
        ``"\\label{fig:<slug>}\n"``.
    """
    tex_caption = escape_latex(caption)
    out = f"\\caption{{{tex_caption}}}\n"
    if label_slug:
        out += f"\\label{{fig:{label_slug}}}\n"
    return out


def format_caption_for_md(
    caption: str, figure_label: str, style: str, wrap_width: int
) -> str:
    """Format caption for Markdown file.

    Parameters
    ----------
    caption : str
        The caption text.
    figure_label : str
        Figure label (e.g., "Figure 1").
    style : str
        Caption style: "scientific", "nature", "ieee", "apa".
    wrap_width : int
        Text wrapping width.

    Returns
    -------
    str
        Formatted Markdown caption.
    """
    wrapped_text = textwrap.fill(caption, width=wrap_width)

    if style == "scientific":
        return f"""# {figure_label}

**{figure_label}.** {wrapped_text}

---

*Generated by figrecipe scientific caption system*
"""
    elif style == "nature":
        return f"""# {figure_label}

**{figure_label} |** {wrapped_text}

---

*Generated by figrecipe scientific caption system*
"""
    else:
        return f"""# {figure_label}

{figure_label}. {wrapped_text}

---

*Generated by figrecipe scientific caption system*
"""


def create_text_figure_list(
    output_file: str, caption_registry: Dict[str, Dict[str, Any]]
):
    """Create plain text figure list.

    Parameters
    ----------
    output_file : str
        Output file path.
    caption_registry : dict
        Dictionary of registered captions.
    """
    content = ["Figure List", "=" * 50, ""]
    for label, info in caption_registry.items():
        content.append(info["formatted"])
        content.append("")
    Path(output_file).write_text("\n".join(content), encoding="utf-8")


def create_latex_figure_list(
    output_file: str, caption_registry: Dict[str, Dict[str, Any]]
):
    """Create LaTeX figure list.

    Parameters
    ----------
    output_file : str
        Output file path.
    caption_registry : dict
        Dictionary of registered captions.
    """
    content = [
        "% Figure List - Generated by figrecipe",
        "\\section{List of Figures}",
        "",
    ]
    for label, info in caption_registry.items():
        escaped_caption = escape_latex(info["text"])
        content.append(f"\\textbf{{{label}.}} {escaped_caption}\\\\")
        content.append("")
    Path(output_file).write_text("\n".join(content), encoding="utf-8")


def create_markdown_figure_list(
    output_file: str, caption_registry: Dict[str, Dict[str, Any]]
):
    """Create Markdown figure list.

    Parameters
    ----------
    output_file : str
        Output file path.
    caption_registry : dict
        Dictionary of registered captions.
    """
    content = [
        "# Figure List",
        "",
        "*Generated by figrecipe scientific caption system*",
        "",
    ]
    for label, info in caption_registry.items():
        content.append(f"**{label}.** {info['text']}")
        content.append("")
    Path(output_file).write_text("\n".join(content), encoding="utf-8")


# EOF
