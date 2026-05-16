#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe CLI commands."""

import json

import pytest
from click.testing import CliRunner

from figrecipe._cli import main


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_recipe(tmp_path):
    """Create a sample recipe file for testing."""
    import figrecipe as fr

    # Create a simple figure
    fig, axes = fr.subplots(1, 1)
    axes.plot([1, 2, 3], [1, 4, 9], label="test")
    axes.set_xlabel("X")
    axes.set_ylabel("Y")

    # Save as recipe using RecordingFigure's save_recipe method
    recipe_path = tmp_path / "test_figure.yaml"
    fig.save_recipe(recipe_path)

    return recipe_path


class TestMainCommand:
    """Test main CLI group."""

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "figrecipe" in result.output
        assert "reproduce" in result.output

    def test_version_flag(self, runner):
        """Test -V flag shows version."""
        result = runner.invoke(main, ["-V"])
        assert result.exit_code == 0
        assert "figrecipe" in result.output

    def test_no_command_shows_help(self, runner):
        """Test that running without subcommand shows help (not editor)."""
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        # Should show help message, not launch editor
        assert "Usage:" in result.output
        # Check for categorized command sections
        assert "Figure Creation:" in result.output
        # Help should mention how to launch GUI editor
        assert "figrecipe start-gui" in result.output


class TestVersionCommand:
    """Test show-version command (renamed from `version` per audit-cli §1b)."""

    def test_show_version(self, runner):
        """Test show-version command shows version."""
        result = runner.invoke(main, ["show-version"])
        assert result.exit_code == 0
        assert "figrecipe" in result.output

    def test_show_version_full(self, runner):
        """Test show-version --full shows dependencies."""
        result = runner.invoke(main, ["show-version", "--full"])
        assert result.exit_code == 0
        assert "matplotlib" in result.output
        assert "numpy" in result.output
        assert "Python" in result.output

    def test_legacy_version_redirects(self, runner):
        """Test deprecated `version` exits 2 with redirect message."""
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 2
        # Click captures stderr in result.output by default
        assert "show-version" in result.output or "--version" in result.output


class TestInfoCommand:
    """Test info command."""

    def test_info_requires_source(self, runner):
        """Test info requires source argument."""
        result = runner.invoke(main, ["info"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_info_basic(self, runner, sample_recipe):
        """Test basic info output."""
        result = runner.invoke(main, ["info", str(sample_recipe)])
        assert result.exit_code == 0
        assert "Recipe Version" in result.output
        assert "Figure ID" in result.output

    def test_info_json(self, runner, sample_recipe):
        """Test info --json outputs valid JSON."""
        result = runner.invoke(main, ["info", "--json", str(sample_recipe)])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "figrecipe_version" in data or "id" in data

    def test_info_verbose(self, runner, sample_recipe):
        """Test info -v shows detailed info."""
        result = runner.invoke(main, ["info", "-v", str(sample_recipe)])
        assert result.exit_code == 0
        # Verbose mode should at least show basic info
        assert "Figure ID" in result.output or "Matplotlib" in result.output


class TestReproduceCommand:
    """Test reproduce command."""

    def test_reproduce_requires_source(self, runner):
        """Test reproduce requires source argument."""
        result = runner.invoke(main, ["reproduce"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_reproduce_basic(self, runner, sample_recipe, tmp_path):
        """Test basic reproduce."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["reproduce", str(sample_recipe), "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.exists()
        assert "Saved" in result.output

    def test_reproduce_formats(self, runner, sample_recipe, tmp_path):
        """Test reproduce with different formats."""
        for fmt in ["png", "pdf", "svg"]:
            output_path = tmp_path / f"output.{fmt}"
            result = runner.invoke(
                main,
                ["reproduce", str(sample_recipe), "-o", str(output_path), "-f", fmt],
            )
            assert result.exit_code == 0
            assert output_path.exists()

    def test_reproduce_help(self, runner):
        """Test reproduce --help."""
        result = runner.invoke(main, ["reproduce", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--format" in result.output
        assert "--dpi" in result.output


class TestValidateCommand:
    """Test validate command."""

    def test_validate_requires_source(self, runner):
        """Test validate requires source argument."""
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_validate_help(self, runner):
        """Test validate --help."""
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--threshold" in result.output
        assert "--strict" in result.output
        assert "--quiet" in result.output


class TestFontsCommand:
    """Test fonts command."""

    def test_fonts_list(self, runner):
        """Test list-fonts command lists fonts."""
        result = runner.invoke(main, ["list-fonts"])
        assert result.exit_code == 0
        assert "fonts" in result.output.lower()

    def test_fonts_search(self, runner):
        """Test list-fonts --search."""
        result = runner.invoke(main, ["list-fonts", "--search", "sans"])
        assert result.exit_code == 0
        assert "matching" in result.output.lower()

    def test_fonts_check_available(self, runner):
        """Test list-fonts --check with common font."""
        # DejaVu Sans is typically available
        result = runner.invoke(main, ["list-fonts", "--check", "DejaVu Sans"])
        # May or may not be available, just check it runs
        assert result.exit_code in [0, 1]

    def test_fonts_help(self, runner):
        """Test list-fonts --help."""
        result = runner.invoke(main, ["list-fonts", "--help"])
        assert result.exit_code == 0
        assert "--check" in result.output
        assert "--search" in result.output


class TestGuiCommand:
    """Test start-gui command."""

    def test_gui_help(self, runner):
        """Test start-gui --help."""
        result = runner.invoke(main, ["start-gui", "--help"])
        assert result.exit_code == 0
        assert "SOURCE" in result.output or "source" in result.output.lower()


class TestCropCommand:
    """Test crop command."""

    def test_crop_help(self, runner):
        """Test crop --help."""
        result = runner.invoke(main, ["crop", "--help"])
        assert result.exit_code == 0
        assert "IMAGE" in result.output or "image" in result.output.lower()


class TestComposeCommand:
    """Test compose command."""

    def test_compose_help(self, runner):
        """Test compose --help."""
        result = runner.invoke(main, ["compose", "--help"])
        assert result.exit_code == 0


class TestStyleCommand:
    """Test style command."""

    def test_style_help(self, runner):
        """Test style --help."""
        result = runner.invoke(main, ["style", "--help"])
        assert result.exit_code == 0


class TestCompletionCommand:
    """Test install-shell-completion + print-shell-completion (replaced
    the legacy `completion` group per audit-cli §1a)."""

    def test_install_shell_completion_help(self, runner):
        """Test install-shell-completion --help."""
        result = runner.invoke(main, ["install-shell-completion", "--help"])
        assert result.exit_code == 0
        assert "--shell" in result.output

    def test_print_shell_completion_help(self, runner):
        """Test print-shell-completion --help."""
        result = runner.invoke(main, ["print-shell-completion", "--help"])
        assert result.exit_code == 0
        assert "--shell" in result.output

    def test_print_shell_completion_bash(self, runner):
        """Print bash completion script."""
        result = runner.invoke(main, ["print-shell-completion", "--shell", "bash"])
        assert result.exit_code == 0
        assert "_FIGRECIPE_COMPLETE" in result.output or "figrecipe" in result.output


class TestConvertCommand:
    """Test convert command."""

    def test_convert_help(self, runner):
        """Test convert --help."""
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output or "format" in result.output.lower()


class TestExtractCommand:
    """Test extract command."""

    def test_extract_help(self, runner):
        """Test extract --help."""
        result = runner.invoke(main, ["extract", "--help"])
        assert result.exit_code == 0

    def test_extract_requires_source(self, runner):
        """Test extract requires source argument."""
        result = runner.invoke(main, ["extract"])
        assert result.exit_code != 0


class TestPlotCommand:
    """Test plot command for declarative figure creation."""

    @pytest.fixture
    def sample_spec(self, tmp_path):
        """Create a sample plot spec file."""
        spec_path = tmp_path / "spec.yaml"
        spec_path.write_text(
            """
figure:
  width_mm: 80
  height_mm: 60

plots:
  - type: line
    x: [1, 2, 3, 4, 5]
    y: [1, 4, 9, 16, 25]
    color: blue
    label: "quadratic"

xlabel: "X"
ylabel: "Y"
title: "Test Plot"
legend: true
"""
        )
        return spec_path

    def test_plot_help(self, runner):
        """Test plot --help."""
        result = runner.invoke(main, ["plot", "--help"])
        assert result.exit_code == 0
        assert "SPEC" in result.output
        assert "--output" in result.output
        assert "--format" in result.output

    def test_plot_requires_spec(self, runner):
        """Test plot requires spec argument."""
        result = runner.invoke(main, ["plot"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_plot_basic(self, runner, sample_spec, tmp_path):
        """Test basic plot from spec."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(main, ["plot", str(sample_spec), "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()
        assert "Saved" in result.output

    def test_plot_formats(self, runner, sample_spec, tmp_path):
        """Test plot with different output formats."""
        for fmt in ["png", "pdf", "svg"]:
            output_path = tmp_path / f"output.{fmt}"
            result = runner.invoke(
                main,
                ["plot", str(sample_spec), "-o", str(output_path), "-f", fmt],
            )
            assert result.exit_code == 0
            assert output_path.exists()

    def test_plot_with_recipe(self, runner, sample_spec, tmp_path):
        """Test plot with --save-recipe flag."""
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["plot", str(sample_spec), "-o", str(output_path), "--save-recipe"]
        )
        assert result.exit_code == 0
        assert output_path.exists()
        # Recipe should also be saved
        recipe_path = tmp_path / "output.yaml"
        assert recipe_path.exists()

    def test_plot_scatter(self, runner, tmp_path):
        """Test scatter plot type."""
        spec_path = tmp_path / "scatter_spec.yaml"
        spec_path.write_text(
            """
plots:
  - type: scatter
    x: [1, 2, 3, 4]
    y: [1, 4, 2, 3]
    color: red
"""
        )
        output_path = tmp_path / "scatter.png"
        result = runner.invoke(main, ["plot", str(spec_path), "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()

    def test_plot_bar(self, runner, tmp_path):
        """Test bar plot type."""
        spec_path = tmp_path / "bar_spec.yaml"
        spec_path.write_text(
            """
plots:
  - type: bar
    x: [1, 2, 3]
    y: [10, 20, 15]
xlabel: "Category"
ylabel: "Value"
"""
        )
        output_path = tmp_path / "bar.png"
        result = runner.invoke(main, ["plot", str(spec_path), "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()

    def test_plot_multiple_types(self, runner, tmp_path):
        """Test multiple plot types in one figure."""
        spec_path = tmp_path / "multi_spec.yaml"
        spec_path.write_text(
            """
plots:
  - type: line
    x: [1, 2, 3, 4]
    y: [1, 2, 3, 4]
    color: blue
    label: "linear"
  - type: scatter
    x: [1, 2, 3, 4]
    y: [1, 4, 9, 16]
    color: red
    label: "quadratic"
legend: true
"""
        )
        output_path = tmp_path / "multi.png"
        result = runner.invoke(main, ["plot", str(spec_path), "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()

    def test_plot_csv_columns(self, runner, tmp_path):
        """Test plot with CSV column names as data source."""
        # Create sample CSV file
        csv_path = tmp_path / "data.csv"
        csv_path.write_text(
            """time,temperature,pressure
0,20.5,101.3
1,21.0,101.2
2,22.5,101.1
3,23.0,101.0
4,24.5,100.9
"""
        )

        # Create spec using CSV columns
        spec_path = tmp_path / "csv_spec.yaml"
        spec_path.write_text(
            f"""
plots:
  - type: scatter
    data_file: {csv_path}
    x: time
    y: temperature
    color: blue
    label: "Temperature"
xlabel: "Time (s)"
ylabel: "Temperature (°C)"
title: "CSV Column Test"
"""
        )
        output_path = tmp_path / "csv_plot.png"
        result = runner.invoke(main, ["plot", str(spec_path), "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()

    def test_plot_csv_invalid_column(self, runner, tmp_path):
        """Test plot with invalid CSV column raises error."""
        # Create sample CSV file
        csv_path = tmp_path / "data.csv"
        csv_path.write_text("x,y\n1,2\n3,4\n")

        # Create spec using invalid column
        spec_path = tmp_path / "invalid_csv_spec.yaml"
        spec_path.write_text(
            f"""
plots:
  - type: line
    data_file: {csv_path}
    x: x
    y: nonexistent_column
"""
        )
        output_path = tmp_path / "invalid_csv.png"
        result = runner.invoke(main, ["plot", str(spec_path), "-o", str(output_path)])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_module_invocation(self):
        """Test python -m figrecipe works."""
        import subprocess

        result = subprocess.run(
            ["python", "-m", "figrecipe", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "figrecipe" in result.stdout

    def test_full_workflow(self, runner, tmp_path):
        """Test full workflow: create -> info -> reproduce -> validate."""
        import figrecipe as fr

        # Create figure
        fig, axes = fr.subplots(1, 1)
        axes.plot([1, 2, 3], [1, 4, 9])
        recipe_path = tmp_path / "workflow_test.yaml"
        fig.save_recipe(recipe_path)

        # Info
        result = runner.invoke(main, ["info", str(recipe_path)])
        assert result.exit_code == 0

        # Reproduce
        output_path = tmp_path / "reproduced.png"
        result = runner.invoke(
            main, ["reproduce", str(recipe_path), "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.exists()
