#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scientific figure caption class for publication-ready figures."""

__all__ = ["ScientificCaption", "caption_manager"]

import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ._formats import (
    create_latex_figure_list,
    create_markdown_figure_list,
    create_text_figure_list,
)


class ScientificCaption:
    """A comprehensive caption system for scientific figures.

    Supports:
    - Figure-level captions with automatic numbering
    - Panel-level captions (A, B, C, etc.)
    - Cross-references
    - Multiple formatting styles (scientific, nature, ieee, apa)
    - Export to TXT, TeX, and Markdown formats

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.subplots()
    >>> ax.plot([1, 2, 3], [1, 4, 9])
    >>> fr.add_figure_caption(fig, "Example plot showing quadratic growth.")
    """

    def __init__(self):
        self.figure_counter = 0
        self.caption_registry: Dict[str, Dict[str, Any]] = {}
        self.panel_letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def add_figure_caption(
        self,
        fig: Any,
        caption: str,
        figure_label: Optional[str] = None,
        style: str = "scientific",
        position: str = "bottom",
        width_ratio: float = 0.9,
        font_size: Union[str, int] = "small",
        wrap_width: int = 80,
        save_to_file: bool = False,
        file_path: Optional[str] = None,
        render: bool = True,
    ) -> str:
        """Add a scientific caption to a figure.

        Parameters
        ----------
        fig : matplotlib.figure.Figure or RecordingFigure
            The figure to add caption to.
        caption : str
            The caption text.
        figure_label : str, optional
            Custom figure label (e.g., "Figure 1"), auto-generated if None.
        style : str, optional
            Caption style: "scientific", "nature", "ieee", "apa".
            Default: "scientific".
        position : str, optional
            Caption position: "bottom" or "top". Default: "bottom".
        width_ratio : float, optional
            Width of caption relative to figure width. Default: 0.9.
        font_size : str or int, optional
            Font size for caption. Default: "small".
        wrap_width : int, optional
            Character width for text wrapping. Default: 80.
        save_to_file : bool, optional
            Whether to save caption to separate file. Default: False.
        file_path : str, optional
            Path for caption file. Default: None.
        render : bool, optional
            If True (default), draw the caption onto the figure and
            adjust the layout to reserve room for it.  Set to False to
            register/number the caption only — the public
            ``figrecipe.add_figure_caption`` API uses ``render=False`` so
            that ONE rendering pipeline (its own ``mpl_fig.text`` call)
            owns the visual output; otherwise the caption is drawn twice
            and the two stacked copies overlap each other.

        Returns
        -------
        str
            The formatted caption text.
        """
        # Get underlying figure if wrapped
        mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

        # Generate figure label if not provided
        if figure_label is None:
            self.figure_counter += 1
            figure_label = f"Figure {self.figure_counter}"

        # Format caption according to style
        formatted_caption = self._format_caption(
            caption, figure_label, style, wrap_width
        )

        # Add caption to figure — only when the caller asks us to render.
        # The public figrecipe.add_figure_caption draws the caption itself
        # and passes render=False here so we don't double-render.
        if render:
            self._add_caption_to_figure(
                mpl_fig, formatted_caption, position, width_ratio, font_size
            )

        # Persist caption on the figrecipe FigureRecord so it survives
        # save -> reproduce roundtrips. Falls back silently if `fig` is a
        # bare matplotlib Figure with no associated recorder.
        try:
            fr_record = None
            if hasattr(fig, "_recorder") and getattr(fig, "_recorder", None) is not None:
                fr_record = fig._recorder.figure_record
            elif hasattr(fig, "figure_record"):
                fr_record = fig.figure_record
            if fr_record is not None:
                fr_record.caption = caption
        except Exception:
            pass

        # Register caption
        self.caption_registry[figure_label] = {
            "text": caption,
            "formatted": formatted_caption,
            "style": style,
            "figure": fig,
        }

        # Save to file if requested
        if save_to_file:
            self._save_caption_to_file(formatted_caption, figure_label, file_path)

        return formatted_caption

    def add_panel_captions(
        self,
        fig: Any,
        axes: Any,
        panel_captions: Union[List[str], Dict[str, str]],
        main_caption: str = "",
        figure_label: Optional[str] = None,
        panel_style: str = "letter_bold",
        position: str = "top_left",
        font_size: Union[str, int] = "medium",
        offset: Tuple[float, float] = (0.02, 0.98),
    ) -> Dict[str, str]:
        """Add panel captions (A, B, C, etc.) to subplot panels.

        Parameters
        ----------
        fig : matplotlib.figure.Figure or RecordingFigure
            The figure containing panels.
        axes : Axes, list, or ndarray
            Axes objects for each panel.
        panel_captions : list or dict
            Caption text for each panel.
        main_caption : str, optional
            Main figure caption. Default: "".
        figure_label : str, optional
            Figure label. Default: None.
        panel_style : str, optional
            Panel label style: "letter_bold", "letter_italic", "number".
            Default: "letter_bold".
        position : str, optional
            Panel label position: "top_left", "top_right", "bottom_left",
            "bottom_right". Default: "top_left".
        font_size : str or int, optional
            Font size for panel labels. Default: "medium".
        offset : tuple, optional
            Position offset for panel labels. Default: (0.02, 0.98).

        Returns
        -------
        dict
            Dictionary mapping panel labels to full caption text.
        """
        # Ensure axes is a list
        if not isinstance(axes, (list, tuple)):
            if hasattr(axes, "plot"):
                axes = [axes]
            elif hasattr(axes, "flatten"):
                axes = axes.flatten()
            else:
                axes = list(axes)

        # Unwrap recording axes
        axes = [ax._ax if hasattr(ax, "_ax") else ax for ax in axes]

        # Handle different input formats for panel_captions
        if isinstance(panel_captions, list):
            panel_dict = {
                self.panel_letters[i]: panel_captions[i]
                for i in range(min(len(panel_captions), len(axes)))
            }
        else:
            panel_dict = panel_captions

        # Add panel labels to axes
        formatted_panels = {}
        for i, ax in enumerate(axes):
            if i < len(self.panel_letters):
                panel_letter = self.panel_letters[i]
                if panel_letter in panel_dict:
                    formatted_label = self._format_panel_label(
                        panel_letter, panel_style
                    )
                    panel_caption = panel_dict[panel_letter]

                    # Add label to axes
                    self._add_panel_label_to_axes(
                        ax, formatted_label, position, font_size, offset
                    )

                    formatted_panels[panel_letter] = (
                        f"{formatted_label} {panel_caption}"
                    )

        # Add main caption if provided
        if main_caption:
            full_caption = self._combine_panel_and_main_captions(
                formatted_panels, main_caption
            )
            self.add_figure_caption(fig, full_caption, figure_label)

        return formatted_panels

    def _format_caption(
        self, caption: str, figure_label: str, style: str, wrap_width: int
    ) -> str:
        """Format caption according to specified style."""
        wrapped_text = textwrap.fill(caption, width=wrap_width)
        styles = {
            "scientific": f"**{figure_label}.** {wrapped_text}",
            "nature": f"**{figure_label} |** {wrapped_text}",
            "ieee": f"{figure_label}. {wrapped_text}",
            "apa": f"*{figure_label}*\n{wrapped_text}",
        }
        return styles.get(style, f"{figure_label}. {wrapped_text}")

    def _format_panel_label(self, letter: str, style: str) -> str:
        """Format panel label according to style."""
        styles = {
            "letter_bold": f"**{letter}**",
            "letter_italic": f"*{letter}*",
            "number": f"**{ord(letter) - ord('A') + 1}**",
        }
        return styles.get(style, f"**{letter}**")

    def _add_caption_to_figure(
        self,
        fig: Any,
        caption: str,
        position: str,
        width_ratio: float,
        font_size: Union[str, int],
    ):
        """Add caption text to figure.

        Markdown markers (``**``, ``*``) introduced by ``_format_caption``'s
        style templates (e.g. ``**Figure 1.**``) are stripped here.
        matplotlib renders text literally — leaving the markers in would
        show ``**Figure 1.**`` as four asterisks instead of a bold label.
        """
        if position == "bottom":
            y_pos = 0.02
            va = "bottom"
        else:  # top
            y_pos = 0.98
            va = "top"

        clean = caption.replace("**", "").replace("*", "")
        fig.text(
            0.5,
            y_pos,
            clean,
            ha="center",
            va=va,
            fontsize=font_size,
            wrap=True,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
        )

        # Adjust layout to accommodate caption
        if position == "bottom":
            fig.subplots_adjust(bottom=0.15)
        else:
            fig.subplots_adjust(top=0.85)

    def _add_panel_label_to_axes(
        self,
        ax: Any,
        label: str,
        position: str,
        font_size: Union[str, int],
        offset: Tuple[float, float],
    ):
        """Add panel label to individual axes."""
        positions = {
            "top_left": (offset[0], offset[1]),
            "top_right": (1 - offset[0], offset[1]),
            "bottom_left": (offset[0], 1 - offset[1]),
            "bottom_right": (1 - offset[0], 1 - offset[1]),
        }

        x_pos, y_pos = positions.get(position, (offset[0], offset[1]))
        ha = "left" if "left" in position else "right"
        va = "top" if "top" in position else "bottom"

        # Remove markdown formatting for display
        display_label = label.replace("**", "").replace("*", "")

        ax.text(
            x_pos,
            y_pos,
            display_label,
            transform=ax.transAxes,
            fontsize=font_size,
            fontweight="bold",
            ha=ha,
            va=va,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
        )

    def _combine_panel_and_main_captions(
        self, panel_dict: Dict[str, str], main_caption: str
    ) -> str:
        """Combine panel captions with main caption."""
        panel_descriptions = []
        for letter in sorted(panel_dict.keys()):
            parts = panel_dict[letter].split(" ", 1)
            if len(parts) > 1:
                panel_descriptions.append(f"({letter}) {parts[1]}")

        combined = main_caption
        if panel_descriptions:
            combined += " " + " ".join(panel_descriptions)

        return combined

    def _save_caption_to_file(
        self, caption: str, figure_label: str, file_path: Optional[str] = None
    ):
        """Save caption to a text file."""
        if file_path is None:
            file_path = f"{figure_label.lower().replace(' ', '_')}_caption.txt"
        Path(file_path).write_text(caption, encoding="utf-8")

    def export_all_captions(
        self, file_path: str = "figure_captions.txt", style: str = "scientific"
    ):
        """Export all registered captions to a file."""
        content = ["Figure Captions", "=" * 50, ""]
        for label, info in self.caption_registry.items():
            content.append(info["formatted"])
            content.append("")
        Path(file_path).write_text("\n".join(content), encoding="utf-8")

    def get_cross_reference(self, figure_label: str) -> str:
        """Get a cross-reference string for a figure."""
        if figure_label in self.caption_registry:
            return f"(see {figure_label})"
        return f"(see {figure_label} - not found)"

    def create_figure_list(
        self, output_file: str = "figure_list.txt", fmt: str = "txt"
    ):
        """Create a comprehensive list of all figures and their captions.

        Parameters
        ----------
        output_file : str, optional
            Output filename. Default: "figure_list.txt".
        fmt : str, optional
            Output format: "txt", "tex", "md". Default: "txt".
        """
        if not self.caption_registry:
            return

        if fmt == "tex":
            create_latex_figure_list(output_file, self.caption_registry)
        elif fmt == "md":
            create_markdown_figure_list(output_file, self.caption_registry)
        else:
            create_text_figure_list(output_file, self.caption_registry)

    def reset(self):
        """Reset the caption manager state."""
        self.figure_counter = 0
        self.caption_registry.clear()


# Global caption manager instance
caption_manager = ScientificCaption()


# EOF
