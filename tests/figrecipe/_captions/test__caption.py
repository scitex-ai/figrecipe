#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the scientific caption system."""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt

from figrecipe._captions import (
    ScientificCaption,
    add_figure_caption,
    add_panel_captions,
    caption_manager,
    create_figure_list,
    cross_ref,
    escape_latex,
    export_captions,
    format_caption_for_md,
    format_caption_for_tex,
    format_caption_for_txt,
    save_caption_multiple_formats,
)


class TestScientificCaption:
    """Tests for ScientificCaption class."""

    def setup_method(self):
        """Reset caption manager before each test."""
        caption_manager.reset()

    def test_init(self):
        """Test initialization."""
        sc = ScientificCaption()
        assert sc.figure_counter == 0
        assert sc.caption_registry == {}
        assert len(sc.panel_letters) == 26

    def test_add_figure_caption_auto_label(self):
        """Test auto-generated figure label."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        result = caption_manager.add_figure_caption(fig, "Test caption")

        assert "Figure 1" in result
        assert caption_manager.figure_counter == 1
        assert "Figure 1" in caption_manager.caption_registry
        plt.close(fig)

    def test_add_figure_caption_custom_label(self):
        """Test custom figure label."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        result = caption_manager.add_figure_caption(
            fig, "Test caption", figure_label="Figure S1"
        )

        assert "Figure S1" in result
        assert "Figure S1" in caption_manager.caption_registry
        plt.close(fig)

    def test_caption_styles(self):
        """Test different caption styles."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        # Scientific style
        result = caption_manager.add_figure_caption(
            fig, "Caption text", figure_label="Fig 1", style="scientific"
        )
        assert "**Fig 1.**" in result

        plt.close(fig)
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        # Nature style
        result = caption_manager.add_figure_caption(
            fig, "Caption text", figure_label="Fig 2", style="nature"
        )
        assert "**Fig 2 |**" in result

        plt.close(fig)

    def test_caption_position_bottom(self):
        """Test bottom caption position."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        caption_manager.add_figure_caption(fig, "Caption", position="bottom")

        # Check that subplots_adjust was called (bottom margin increased)
        # The bottom should be adjusted
        plt.close(fig)

    def test_caption_position_top(self):
        """Test top caption position."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        caption_manager.add_figure_caption(fig, "Caption", position="top")
        plt.close(fig)

    def test_export_all_captions(self):
        """Test exporting all captions."""
        fig1, ax1 = plt.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9])
        caption_manager.add_figure_caption(fig1, "First caption")

        fig2, ax2 = plt.subplots()
        ax2.plot([1, 2, 3], [1, 4, 9])
        caption_manager.add_figure_caption(fig2, "Second caption")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            caption_manager.export_all_captions(temp_path)
            content = Path(temp_path).read_text()
            assert "First caption" in content
            assert "Second caption" in content
        finally:
            Path(temp_path).unlink()
            plt.close(fig1)
            plt.close(fig2)

    def test_cross_reference(self):
        """Test cross-reference generation."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        caption_manager.add_figure_caption(fig, "Caption", figure_label="Figure 1")

        ref = caption_manager.get_cross_reference("Figure 1")
        assert ref == "(see Figure 1)"

        ref_not_found = caption_manager.get_cross_reference("Figure 99")
        assert "not found" in ref_not_found

        plt.close(fig)

    def test_reset(self):
        """Test reset functionality."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        caption_manager.add_figure_caption(fig, "Caption")

        assert caption_manager.figure_counter > 0
        assert len(caption_manager.caption_registry) > 0

        caption_manager.reset()

        assert caption_manager.figure_counter == 0
        assert len(caption_manager.caption_registry) == 0

        plt.close(fig)


class TestPanelCaptions:
    """Tests for panel caption functionality."""

    def setup_method(self):
        """Reset caption manager before each test."""
        caption_manager.reset()

    def test_add_panel_captions_list(self):
        """Test adding panel captions from a list."""
        fig, axes = plt.subplots(1, 2)
        axes[0].plot([1, 2, 3], [1, 4, 9])
        axes[1].bar([1, 2, 3], [1, 2, 3])

        result = caption_manager.add_panel_captions(
            fig, axes, ["Line plot", "Bar plot"]
        )

        assert "A" in result
        assert "B" in result
        assert "Line plot" in result["A"]
        assert "Bar plot" in result["B"]

        plt.close(fig)

    def test_add_panel_captions_dict(self):
        """Test adding panel captions from a dict."""
        fig, axes = plt.subplots(1, 2)
        axes[0].plot([1, 2, 3], [1, 4, 9])
        axes[1].bar([1, 2, 3], [1, 2, 3])

        result = caption_manager.add_panel_captions(
            fig, axes, {"A": "First panel", "B": "Second panel"}
        )

        assert "First panel" in result["A"]
        assert "Second panel" in result["B"]

        plt.close(fig)

    def test_panel_styles(self):
        """Test different panel label styles."""
        fig, axes = plt.subplots(1, 2)

        result = caption_manager.add_panel_captions(
            fig, axes, ["Panel 1", "Panel 2"], panel_style="letter_bold"
        )
        assert "**A**" in result["A"]

        plt.close(fig)

    def test_panel_positions(self):
        """Test different panel label positions."""
        fig, axes = plt.subplots(1, 2)

        # Top left (default)
        caption_manager.add_panel_captions(fig, axes, ["P1", "P2"], position="top_left")
        plt.close(fig)

        fig, axes = plt.subplots(1, 2)
        # Top right
        caption_manager.add_panel_captions(
            fig, axes, ["P1", "P2"], position="top_right"
        )
        plt.close(fig)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def setup_method(self):
        """Reset caption manager before each test."""
        caption_manager.reset()

    def test_add_figure_caption_func(self):
        """Test add_figure_caption convenience function."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        result = add_figure_caption(fig, "Test caption")

        assert "Figure 1" in result
        plt.close(fig)

    def test_add_panel_captions_func(self):
        """Test add_panel_captions convenience function."""
        fig, axes = plt.subplots(1, 2)

        result = add_panel_captions(fig, axes, ["P1", "P2"])

        assert "A" in result
        assert "B" in result
        plt.close(fig)

    def test_cross_ref_func(self):
        """Test cross_ref convenience function."""
        fig, ax = plt.subplots()
        add_figure_caption(fig, "Caption", figure_label="Figure 1")

        ref = cross_ref("Figure 1")
        assert "(see Figure 1)" == ref

        plt.close(fig)

    def test_export_captions_func(self):
        """Test export_captions convenience function."""
        fig, ax = plt.subplots()
        add_figure_caption(fig, "Caption")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            export_captions(temp_path)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()
            plt.close(fig)


class TestFormatFunctions:
    """Tests for format conversion functions."""

    def test_format_caption_for_txt(self):
        """Test plain text format."""
        result = format_caption_for_txt(
            "Test caption", "Figure 1", "scientific", wrap_width=80
        )
        assert "Figure 1. Test caption" == result

        result = format_caption_for_txt(
            "Test caption", "Figure 1", "nature", wrap_width=80
        )
        assert "Figure 1 | Test caption" == result

    def test_format_caption_for_tex(self):
        """Test LaTeX format."""
        result = format_caption_for_tex(
            "Test caption", "Figure 1", "scientific", wrap_width=80
        )
        assert "\\begin{figure}" in result
        assert "\\caption" in result
        assert "\\label{fig:figure_1}" in result
        assert "\\textbf{Figure 1.}" in result

    def test_format_caption_for_md(self):
        """Test Markdown format."""
        result = format_caption_for_md(
            "Test caption", "Figure 1", "scientific", wrap_width=80
        )
        assert "# Figure 1" in result
        assert "**Figure 1.**" in result
        assert "figrecipe" in result

    def test_escape_latex(self):
        """Test LaTeX character escaping."""
        assert escape_latex("test & test") == r"test \& test"
        assert escape_latex("50%") == r"50\%"
        assert escape_latex("$100") == r"\$100"
        assert escape_latex("test_var") == r"test\_var"


class TestMultiFormatSave:
    """Tests for saving captions in multiple formats."""

    def setup_method(self):
        """Reset caption manager before each test."""
        caption_manager.reset()

    def test_save_caption_multiple_formats(self):
        """Test saving to multiple formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_figure"

            save_caption_multiple_formats(
                "Test caption",
                str(base_path),
                figure_label="Figure 1",
                save_txt=True,
                save_tex=True,
                save_md=True,
            )

            txt_file = Path(f"{base_path}_caption.txt")
            tex_file = Path(f"{base_path}_caption.tex")
            md_file = Path(f"{base_path}_caption.md")

            assert txt_file.exists()
            assert tex_file.exists()
            assert md_file.exists()

            assert "Test caption" in txt_file.read_text()
            assert "\\caption" in tex_file.read_text()
            assert "**Figure 1.**" in md_file.read_text()


class TestFigureList:
    """Tests for figure list creation."""

    def setup_method(self):
        """Reset caption manager before each test."""
        caption_manager.reset()

    def test_create_figure_list_txt(self):
        """Test creating text figure list."""
        fig, ax = plt.subplots()
        add_figure_caption(fig, "First caption")
        add_figure_caption(fig, "Second caption", figure_label="Figure 2")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            create_figure_list(temp_path, fmt="txt")
            content = Path(temp_path).read_text()
            assert "Figure List" in content
            assert "First caption" in content
        finally:
            Path(temp_path).unlink()
            plt.close(fig)

    def test_create_figure_list_md(self):
        """Test creating Markdown figure list."""
        fig, ax = plt.subplots()
        add_figure_caption(fig, "Caption")

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            temp_path = f.name

        try:
            create_figure_list(temp_path, fmt="md")
            content = Path(temp_path).read_text()
            assert "# Figure List" in content
        finally:
            Path(temp_path).unlink()
            plt.close(fig)

    def test_create_figure_list_tex(self):
        """Test creating LaTeX figure list."""
        fig, ax = plt.subplots()
        add_figure_caption(fig, "Caption")

        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as f:
            temp_path = f.name

        try:
            create_figure_list(temp_path, fmt="tex")
            content = Path(temp_path).read_text()
            assert "\\section{List of Figures}" in content
        finally:
            Path(temp_path).unlink()
            plt.close(fig)


class TestImports:
    """Test that imports work correctly."""

    def test_import_from_captions(self):
        """Test imports from captions module."""
        from figrecipe._captions import (
            ScientificCaption,
            add_figure_caption,
            add_panel_captions,
            caption_manager,
            cross_ref,
            export_captions,
        )

        assert callable(add_figure_caption)
        assert callable(add_panel_captions)
        assert callable(cross_ref)
        assert callable(export_captions)
        assert isinstance(caption_manager, ScientificCaption)


# EOF
