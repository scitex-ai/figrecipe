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

    def test_help_part_1(self, runner):
        """Test --help flag."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_help_part_2(self, runner):
        """Test --help flag."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["--help"])
        assert "figrecipe" in result.output

    def test_help_part_3(self, runner):
        """Test --help flag."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["--help"])
        assert "reproduce" in result.output

    def test_version_flag_part_1(self, runner):
        """Test -V flag shows version."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["-V"])
        assert result.exit_code == 0

    def test_version_flag_part_2(self, runner):
        """Test -V flag shows version."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["-V"])
        assert "figrecipe" in result.output

    def test_no_command_shows_help_part_1(self, runner):
        """Test that running without subcommand shows help (not editor)."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_no_command_shows_help_part_2(self, runner):
        """Test that running without subcommand shows help (not editor)."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, [])
        assert "Usage:" in result.output

    def test_no_command_shows_help_part_3(self, runner):
        """Test that running without subcommand shows help (not editor)."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, [])
        assert "Figure Creation:" in result.output

    def test_no_command_shows_help_part_4(self, runner):
        """Test that running without subcommand shows help (not editor)."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, [])
        assert "figrecipe start-gui" in result.output


class TestVersionCommand:
    """Test show-version command (renamed from `version` per audit-cli §1b)."""

    def test_show_version_part_1(self, runner):
        """Test show-version command shows version."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version"])
        assert result.exit_code == 0

    def test_show_version_part_2(self, runner):
        """Test show-version command shows version."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version"])
        assert "figrecipe" in result.output

    def test_show_version_full_part_1(self, runner):
        """Test show-version --full shows dependencies."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version", "--full"])
        assert result.exit_code == 0

    def test_show_version_full_part_2(self, runner):
        """Test show-version --full shows dependencies."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version", "--full"])
        assert "matplotlib" in result.output

    def test_show_version_full_part_3(self, runner):
        """Test show-version --full shows dependencies."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version", "--full"])
        assert "numpy" in result.output

    def test_show_version_full_part_4(self, runner):
        """Test show-version --full shows dependencies."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["show-version", "--full"])
        assert "Python" in result.output

    def test_legacy_version_redirects_part_1(self, runner):
        """Test deprecated `version` exits 2 with redirect message."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 2

    def test_legacy_version_redirects_part_2(self, runner):
        """Test deprecated `version` exits 2 with redirect message."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["version"])
        assert "show-version" in result.output or "--version" in result.output


class TestInfoCommand:
    """Test info command."""

    def test_info_requires_source_part_1(self, runner):
        """Test info requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info"])
        assert result.exit_code != 0

    def test_info_requires_source_part_2(self, runner):
        """Test info requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info"])
        assert "Missing argument" in result.output

    def test_info_basic_part_1(self, runner, sample_recipe):
        """Test basic info output."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", str(sample_recipe)])
        assert result.exit_code == 0

    def test_info_basic_part_2(self, runner, sample_recipe):
        """Test basic info output."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", str(sample_recipe)])
        assert "Recipe Version" in result.output

    def test_info_basic_part_3(self, runner, sample_recipe):
        """Test basic info output."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", str(sample_recipe)])
        assert "Figure ID" in result.output

    def test_info_json_part_1(self, runner, sample_recipe):
        """Test info --json outputs valid JSON."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", "--json", str(sample_recipe)])
        assert result.exit_code == 0

    def test_info_json_part_2(self, runner, sample_recipe):
        """Test info --json outputs valid JSON."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", "--json", str(sample_recipe)])
        data = json.loads(result.output)
        assert "figrecipe_version" in data or "id" in data

    def test_info_verbose_part_1(self, runner, sample_recipe):
        """Test info -v shows detailed info."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", "-v", str(sample_recipe)])
        assert result.exit_code == 0

    def test_info_verbose_part_2(self, runner, sample_recipe):
        """Test info -v shows detailed info."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["info", "-v", str(sample_recipe)])
        assert "Figure ID" in result.output or "Matplotlib" in result.output


class TestReproduceCommand:
    """Test reproduce command."""

    def test_reproduce_requires_source_part_1(self, runner):
        """Test reproduce requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce"])
        assert result.exit_code != 0

    def test_reproduce_requires_source_part_2(self, runner):
        """Test reproduce requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce"])
        assert "Missing argument" in result.output

    def test_reproduce_basic_part_1(self, runner, sample_recipe, tmp_path):
        """Test basic reproduce."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["reproduce", str(sample_recipe), "-o", str(output_path)]
        )
        assert result.exit_code == 0

    def test_reproduce_basic_part_2(self, runner, sample_recipe, tmp_path):
        """Test basic reproduce."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["reproduce", str(sample_recipe), "-o", str(output_path)]
        )
        assert output_path.exists()

    def test_reproduce_basic_part_3(self, runner, sample_recipe, tmp_path):
        """Test basic reproduce."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["reproduce", str(sample_recipe), "-o", str(output_path)]
        )
        assert "Saved" in result.output

    def test_reproduce_formats_command(self, runner, sample_recipe, tmp_path):
        """Test reproduce with different formats."""
        # Arrange
        # Act
        # Assert
        for fmt in ["png", "pdf", "svg"]:
            output_path = tmp_path / f"output.{fmt}"
            result = runner.invoke(
                main,
                ["reproduce", str(sample_recipe), "-o", str(output_path), "-f", fmt],
            )
            assert result.exit_code == 0
            assert output_path.exists()

    def test_reproduce_help_part_1(self, runner):
        """Test reproduce --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce", "--help"])
        assert result.exit_code == 0

    def test_reproduce_help_part_2(self, runner):
        """Test reproduce --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce", "--help"])
        assert "--output" in result.output

    def test_reproduce_help_part_3(self, runner):
        """Test reproduce --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce", "--help"])
        assert "--format" in result.output

    def test_reproduce_help_part_4(self, runner):
        """Test reproduce --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["reproduce", "--help"])
        assert "--dpi" in result.output


class TestValidateCommand:
    """Test validate command."""

    def test_validate_requires_source_part_1(self, runner):
        """Test validate requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0

    def test_validate_requires_source_part_2(self, runner):
        """Test validate requires source argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate"])
        assert "Missing argument" in result.output

    def test_validate_help_part_1(self, runner):
        """Test validate --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0

    def test_validate_help_part_2(self, runner):
        """Test validate --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate", "--help"])
        assert "--threshold" in result.output

    def test_validate_help_part_3(self, runner):
        """Test validate --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate", "--help"])
        assert "--strict" in result.output

    def test_validate_help_part_4(self, runner):
        """Test validate --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["validate", "--help"])
        assert "--quiet" in result.output


class TestFontsCommand:
    """Test fonts command."""

    def test_fonts_list_part_1(self, runner):
        """Test list-fonts command lists fonts."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts"])
        assert result.exit_code == 0

    def test_fonts_list_part_2(self, runner):
        """Test list-fonts command lists fonts."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts"])
        assert "fonts" in result.output.lower()

    def test_fonts_search_part_1(self, runner):
        """Test list-fonts --search."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--search", "sans"])
        assert result.exit_code == 0

    def test_fonts_search_part_2(self, runner):
        """Test list-fonts --search."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--search", "sans"])
        assert "matching" in result.output.lower()

    def test_fonts_check_available(self, runner):
        """Test list-fonts --check with common font."""
        # DejaVu Sans is typically available
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--check", "DejaVu Sans"])
        # May or may not be available, just check it runs
        assert result.exit_code in [0, 1]

    def test_fonts_help_part_1(self, runner):
        """Test list-fonts --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--help"])
        assert result.exit_code == 0

    def test_fonts_help_part_2(self, runner):
        """Test list-fonts --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--help"])
        assert "--check" in result.output

    def test_fonts_help_part_3(self, runner):
        """Test list-fonts --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["list-fonts", "--help"])
        assert "--search" in result.output


class TestGuiCommand:
    """Test start-gui command."""

    def test_gui_help_part_1(self, runner):
        """Test start-gui --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["start-gui", "--help"])
        assert result.exit_code == 0

    def test_gui_help_part_2(self, runner):
        """Test start-gui --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["start-gui", "--help"])
        assert "SOURCE" in result.output or "source" in result.output.lower()


class TestCropCommand:
    """Test crop command."""

    def test_crop_help_part_1(self, runner):
        """Test crop --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["crop", "--help"])
        assert result.exit_code == 0

    def test_crop_help_part_2(self, runner):
        """Test crop --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["crop", "--help"])
        assert "IMAGE" in result.output or "image" in result.output.lower()


class TestComposeCommand:
    """Test compose command."""

    def test_compose_help_command(self, runner):
        """Test compose --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["compose", "--help"])
        assert result.exit_code == 0


class TestStyleCommand:
    """Test style command."""

    def test_style_help_command(self, runner):
        """Test style --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["style", "--help"])
        assert result.exit_code == 0


class TestCompletionCommand:
    """Test install-shell-completion + print-shell-completion (replaced
    the legacy `completion` group per audit-cli §1a)."""

    def test_install_shell_completion_help_part_1(self, runner):
        """Test install-shell-completion --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["install-shell-completion", "--help"])
        assert result.exit_code == 0

    def test_install_shell_completion_help_part_2(self, runner):
        """Test install-shell-completion --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["install-shell-completion", "--help"])
        assert "--shell" in result.output

    def test_print_shell_completion_help_part_1(self, runner):
        """Test print-shell-completion --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["print-shell-completion", "--help"])
        assert result.exit_code == 0

    def test_print_shell_completion_help_part_2(self, runner):
        """Test print-shell-completion --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["print-shell-completion", "--help"])
        assert "--shell" in result.output

    def test_print_shell_completion_bash_part_1(self, runner):
        """Print bash completion script."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["print-shell-completion", "--shell", "bash"])
        assert result.exit_code == 0

    def test_print_shell_completion_bash_part_2(self, runner):
        """Print bash completion script."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["print-shell-completion", "--shell", "bash"])
        assert "_FIGRECIPE_COMPLETE" in result.output or "figrecipe" in result.output


class TestConvertCommand:
    """Test convert command."""

    def test_convert_help_part_1(self, runner):
        """Test convert --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0

    def test_convert_help_part_2(self, runner):
        """Test convert --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["convert", "--help"])
        assert "--format" in result.output or "format" in result.output.lower()


class TestExtractCommand:
    """Test extract command."""

    def test_extract_help_command(self, runner):
        """Test extract --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["extract", "--help"])
        assert result.exit_code == 0

    def test_extract_requires_source(self, runner):
        """Test extract requires source argument."""
        # Arrange
        # Act
        # Assert
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

    def test_plot_help_part_1(self, runner):
        """Test plot --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot", "--help"])
        assert result.exit_code == 0

    def test_plot_help_part_2(self, runner):
        """Test plot --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot", "--help"])
        assert "SPEC" in result.output

    def test_plot_help_part_3(self, runner):
        """Test plot --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot", "--help"])
        assert "--output" in result.output

    def test_plot_help_part_4(self, runner):
        """Test plot --help."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot", "--help"])
        assert "--format" in result.output

    def test_plot_requires_spec_part_1(self, runner):
        """Test plot requires spec argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot"])
        assert result.exit_code != 0

    def test_plot_requires_spec_part_2(self, runner):
        """Test plot requires spec argument."""
        # Arrange
        # Act
        # Assert
        result = runner.invoke(main, ["plot"])
        assert "Missing argument" in result.output

    def test_plot_basic_part_1(self, runner, sample_spec, tmp_path):
        """Test basic plot from spec."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(main, ["plot", str(sample_spec), "-o", str(output_path)])
        assert result.exit_code == 0

    def test_plot_basic_part_2(self, runner, sample_spec, tmp_path):
        """Test basic plot from spec."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(main, ["plot", str(sample_spec), "-o", str(output_path)])
        assert output_path.exists()

    def test_plot_basic_part_3(self, runner, sample_spec, tmp_path):
        """Test basic plot from spec."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(main, ["plot", str(sample_spec), "-o", str(output_path)])
        assert "Saved" in result.output

    def test_plot_formats_command(self, runner, sample_spec, tmp_path):
        """Test plot with different output formats."""
        # Arrange
        # Act
        # Assert
        for fmt in ["png", "pdf", "svg"]:
            output_path = tmp_path / f"output.{fmt}"
            result = runner.invoke(
                main,
                ["plot", str(sample_spec), "-o", str(output_path), "-f", fmt],
            )
            assert result.exit_code == 0
            assert output_path.exists()

    def test_plot_with_recipe_part_1(self, runner, sample_spec, tmp_path):
        """Test plot with --save-recipe flag."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["plot", str(sample_spec), "-o", str(output_path), "--save-recipe"]
        )
        assert result.exit_code == 0

    def test_plot_with_recipe_part_2(self, runner, sample_spec, tmp_path):
        """Test plot with --save-recipe flag."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["plot", str(sample_spec), "-o", str(output_path), "--save-recipe"]
        )
        assert output_path.exists()

    def test_plot_with_recipe_part_3(self, runner, sample_spec, tmp_path):
        """Test plot with --save-recipe flag."""
        # Arrange
        # Act
        # Assert
        output_path = tmp_path / "output.png"
        result = runner.invoke(
            main, ["plot", str(sample_spec), "-o", str(output_path), "--save-recipe"]
        )
        recipe_path = tmp_path / "output.yaml"
        assert recipe_path.exists()

    def test_plot_scatter_part_1(self, runner, tmp_path):
        """Test scatter plot type."""
        # Arrange
        # Act
        # Assert
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

    def test_plot_scatter_part_2(self, runner, tmp_path):
        """Test scatter plot type."""
        # Arrange
        # Act
        # Assert
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
        assert output_path.exists()

    def test_plot_bar_part_1(self, runner, tmp_path):
        """Test bar plot type."""
        # Arrange
        # Act
        # Assert
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

    def test_plot_bar_part_2(self, runner, tmp_path):
        """Test bar plot type."""
        # Arrange
        # Act
        # Assert
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
        assert output_path.exists()

    def test_plot_multiple_types_part_1(self, runner, tmp_path):
        """Test multiple plot types in one figure."""
        # Arrange
        # Act
        # Assert
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

    def test_plot_multiple_types_part_2(self, runner, tmp_path):
        """Test multiple plot types in one figure."""
        # Arrange
        # Act
        # Assert
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
        assert output_path.exists()

    def test_plot_csv_columns_part_1(self, runner, tmp_path):
        """Test plot with CSV column names as data source."""
        # Arrange
        # Act
        # Assert
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

    def test_plot_csv_columns_part_2(self, runner, tmp_path):
        """Test plot with CSV column names as data source."""
        # Arrange
        # Act
        # Assert
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
        assert output_path.exists()

    def test_plot_csv_invalid_column_part_1(self, runner, tmp_path):
        """Test plot with invalid CSV column raises error."""
        # Arrange
        # Act
        # Assert
        csv_path = tmp_path / "data.csv"
        csv_path.write_text("x,y\n1,2\n3,4\n")
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

    def test_plot_csv_invalid_column_part_2(self, runner, tmp_path):
        """Test plot with invalid CSV column raises error."""
        # Arrange
        # Act
        # Assert
        csv_path = tmp_path / "data.csv"
        csv_path.write_text("x,y\n1,2\n3,4\n")
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
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_module_invocation_part_1(self):
        """Test python -m figrecipe works."""
        # Arrange
        # Act
        # Assert
        import subprocess
        result = subprocess.run(
            ["python", "-m", "figrecipe", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_module_invocation_part_2(self):
        """Test python -m figrecipe works."""
        # Arrange
        # Act
        # Assert
        import subprocess
        result = subprocess.run(
            ["python", "-m", "figrecipe", "--help"],
            capture_output=True,
            text=True,
        )
        assert "figrecipe" in result.stdout

    def test_full_workflow_part_1(self, runner, tmp_path):
        """Test full workflow: create -> info -> reproduce -> validate."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        fig, axes = fr.subplots(1, 1)
        axes.plot([1, 2, 3], [1, 4, 9])
        recipe_path = tmp_path / "workflow_test.yaml"
        fig.save_recipe(recipe_path)
        result = runner.invoke(main, ["info", str(recipe_path)])
        assert result.exit_code == 0

    def test_full_workflow_part_2(self, runner, tmp_path):
        """Test full workflow: create -> info -> reproduce -> validate."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        fig, axes = fr.subplots(1, 1)
        axes.plot([1, 2, 3], [1, 4, 9])
        recipe_path = tmp_path / "workflow_test.yaml"
        fig.save_recipe(recipe_path)
        result = runner.invoke(main, ["info", str(recipe_path)])
        output_path = tmp_path / "reproduced.png"
        result = runner.invoke(
            main, ["reproduce", str(recipe_path), "-o", str(output_path)]
        )
        assert result.exit_code == 0

    def test_full_workflow_part_3(self, runner, tmp_path):
        """Test full workflow: create -> info -> reproduce -> validate."""
        # Arrange
        # Act
        # Assert
        import figrecipe as fr
        fig, axes = fr.subplots(1, 1)
        axes.plot([1, 2, 3], [1, 4, 9])
        recipe_path = tmp_path / "workflow_test.yaml"
        fig.save_recipe(recipe_path)
        result = runner.invoke(main, ["info", str(recipe_path)])
        output_path = tmp_path / "reproduced.png"
        result = runner.invoke(
            main, ["reproduce", str(recipe_path), "-o", str(output_path)]
        )
        assert output_path.exists()
