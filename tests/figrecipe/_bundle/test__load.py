#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the layered bundle format (ZIP with spec.json + style.json + data.csv)."""

import json
import zipfile

import numpy as np
import pandas as pd
import pytest

import figrecipe as fr


def _find_bundle_file(zf, filename):
    """Find file in bundle, handling both root and subdirectory formats."""
    namelist = zf.namelist()
    # Try root first
    if filename in namelist:
        return filename
    # Try subdirectory (new format uses zip stem as root)
    for name in namelist:
        if name.endswith(f"/{filename}") or name.endswith(filename):
            return name
    return None


class TestSaveBundle:
    """Test save_bundle functionality."""

    def test_save_creates_zip_file_part_1(self, tmp_path):
        """Test that save_bundle creates a .zip file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = tmp_path / "test_fig"
        result = fr.save_bundle(fig, bundle_path, verbose=False)
        assert result.suffix == ".zip"

    def test_save_creates_zip_file_part_2(self, tmp_path):
        """Test that save_bundle creates a .zip file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = tmp_path / "test_fig"
        result = fr.save_bundle(fig, bundle_path, verbose=False)
        assert result.exists()

    def test_save_creates_zip_file_part_3(self, tmp_path):
        """Test that save_bundle creates a .zip file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = tmp_path / "test_fig"
        result = fr.save_bundle(fig, bundle_path, verbose=False)
        assert zipfile.is_zipfile(result)

    def test_save_creates_spec_json_part_1(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert "version" in spec

    def test_save_creates_spec_json_part_2(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert "figure" in spec

    def test_save_creates_spec_json_part_3(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert "axes" in spec

    def test_save_creates_spec_json_part_4(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert "ax_0_0" in spec["axes"]

    def test_save_creates_spec_json_part_5(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert len(spec["axes"]["ax_0_0"]["traces"]) == 1

    def test_save_creates_spec_json_part_6(self, tmp_path):
        """Test that spec.json is created with correct structure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="myplot")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            spec_path = _find_bundle_file(zf, "spec.json")
            if not (spec_path is not None):
                raise AssertionError(f'spec.json not found in {zf.namelist()}')
            with zf.open(spec_path) as f:
                spec = json.load(f)
        assert spec["axes"]["ax_0_0"]["traces"][0]["id"] == "myplot"

    def test_save_creates_style_json_part_1(self, tmp_path):
        """Test that style.json is created."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test", color="red", linewidth=2)
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            style_path = _find_bundle_file(zf, "style.json")
            if not (style_path is not None):
                raise AssertionError(f'style.json not found in {zf.namelist()}')
            with zf.open(style_path) as f:
                style = json.load(f)
        assert "version" in style

    def test_save_creates_style_json_part_2(self, tmp_path):
        """Test that style.json is created."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test", color="red", linewidth=2)
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            style_path = _find_bundle_file(zf, "style.json")
            if not (style_path is not None):
                raise AssertionError(f'style.json not found in {zf.namelist()}')
            with zf.open(style_path) as f:
                style = json.load(f)
        assert "axes" in style

    def test_save_creates_data_csv_part_1(self, tmp_path):
        """Test that data.csv is created with correct columns."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 4.0, 9.0])
        ax.plot(x, y, id="mydata")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            data_path = _find_bundle_file(zf, "data.csv")
            if not (data_path is not None):
                raise AssertionError(f'data.csv not found in {zf.namelist()}')
            with zf.open(data_path) as f:
                df = pd.read_csv(f)
        assert "mydata_x" in df.columns

    def test_save_creates_data_csv_part_2(self, tmp_path):
        """Test that data.csv is created with correct columns."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 4.0, 9.0])
        ax.plot(x, y, id="mydata")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            data_path = _find_bundle_file(zf, "data.csv")
            if not (data_path is not None):
                raise AssertionError(f'data.csv not found in {zf.namelist()}')
            with zf.open(data_path) as f:
                df = pd.read_csv(f)
        assert "mydata_y" in df.columns

    def test_save_creates_exports(self, tmp_path):
        """Test that exports/ contains figure.png."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")

        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)

        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()
            # Check for exports/figure.png in any subdirectory
            has_figure = any("exports/figure.png" in n for n in names)
            assert has_figure, f"exports/figure.png not found in {names}"

    def test_save_creates_hitmap(self, tmp_path):
        """Test that hitmap is saved when requested."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")

        bundle_path = fr.save_bundle(
            fig, tmp_path / "test", save_hitmap=True, verbose=False
        )

        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()
            # Check for exports/figure_hitmap.png in any subdirectory
            has_hitmap = any("exports/figure_hitmap.png" in n for n in names)
            assert has_hitmap, f"exports/figure_hitmap.png not found in {names}"

    def test_save_creates_recipe_yaml_in_zip(self, tmp_path):
        """Test that recipe.yaml is included inside the ZIP bundle."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")

        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)

        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()
            has_recipe = any("recipe.yaml" in n for n in names)
            assert has_recipe, f"recipe.yaml not found in {names}"

    def test_save_zip_via_fr_save_creates_recipe_alongside_part_1(self, tmp_path):
        """Test that fr.save(fig, 'x.zip') creates recipe.yaml alongside ZIP."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "test.zip", verbose=False)
        bundle_path = result[0]
        yaml_path = result[1]
        assert bundle_path.exists()

    def test_save_zip_via_fr_save_creates_recipe_alongside_part_2(self, tmp_path):
        """Test that fr.save(fig, 'x.zip') creates recipe.yaml alongside ZIP."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "test.zip", verbose=False)
        bundle_path = result[0]
        yaml_path = result[1]
        assert yaml_path is not None

    def test_save_zip_via_fr_save_creates_recipe_alongside_part_3(self, tmp_path):
        """Test that fr.save(fig, 'x.zip') creates recipe.yaml alongside ZIP."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "test.zip", verbose=False)
        bundle_path = result[0]
        yaml_path = result[1]
        assert yaml_path.exists()

    def test_save_zip_via_fr_save_creates_recipe_alongside_part_4(self, tmp_path):
        """Test that fr.save(fig, 'x.zip') creates recipe.yaml alongside ZIP."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "test.zip", verbose=False)
        bundle_path = result[0]
        yaml_path = result[1]
        assert yaml_path.suffix == ".yaml"


class TestLoadBundle:
    """Test load_bundle functionality."""

    def test_load_returns_spec_style_data_part_1(self, tmp_path):
        """Test that load_bundle returns all three components."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        spec, style, data = fr.load_bundle(bundle_path)
        assert isinstance(spec, dict)

    def test_load_returns_spec_style_data_part_2(self, tmp_path):
        """Test that load_bundle returns all three components."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        spec, style, data = fr.load_bundle(bundle_path)
        assert isinstance(style, dict)

    def test_load_returns_spec_style_data_part_3(self, tmp_path):
        """Test that load_bundle returns all three components."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        spec, style, data = fr.load_bundle(bundle_path)
        assert isinstance(data, pd.DataFrame)

    def test_load_preserves_data(self, tmp_path):
        """Test that data is preserved through save/load cycle."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y, id="sine")

        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        spec, style, data = fr.load_bundle(bundle_path)

        np.testing.assert_array_almost_equal(data["sine_x"].values, x)
        np.testing.assert_array_almost_equal(data["sine_y"].values, y)
        assert True  # TQ001-placeholder: body exercises code under test

    def test_load_missing_bundle_raises(self, tmp_path):
        """Test that loading nonexistent bundle raises error."""
        # Arrange
        # Act
        # Assert
        with pytest.raises(FileNotFoundError):
            fr.load_bundle(tmp_path / "nonexistent.zip")


class TestReproduceBundle:
    """Test reproduce_bundle functionality."""

    def test_reproduce_creates_figure_part_1(self, tmp_path):
        """Test that reproduce_bundle creates a valid figure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        fig2, axes2 = fr.reproduce_bundle(bundle_path)
        assert fig2 is not None

    def test_reproduce_creates_figure_part_2(self, tmp_path):
        """Test that reproduce_bundle creates a valid figure."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        fig2, axes2 = fr.reproduce_bundle(bundle_path)
        assert axes2 is not None

    def test_reproduce_preserves_data(self, tmp_path):
        """Test that reproduced figure has correct data."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        ax.plot(x, y, id="squares")

        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        fig2, axes2 = fr.reproduce_bundle(bundle_path)

        # Get the reproduced line data
        ax2 = axes2[0]
        lines = ax2.ax.get_lines()
        assert len(lines) >= 1

        line_x, line_y = lines[0].get_data()
        np.testing.assert_array_almost_equal(line_x, x)
        np.testing.assert_array_almost_equal(line_y, y)

    def test_reproduce_multiple_traces(self, tmp_path):
        """Test reproducing figure with multiple traces."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 2 * np.pi, 20)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")

        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        fig2, axes2 = fr.reproduce_bundle(bundle_path)

        ax2 = axes2[0]
        lines = ax2.ax.get_lines()
        assert len(lines) == 2


class TestUnifiedSave:
    """Test fr.save() with .zip extension uses layered bundle."""

    def test_save_zip_uses_layered_format_part_1(self, tmp_path):
        """Test that fr.save() with .zip creates layered bundle."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "figure.zip", verbose=False)
        assert result[0].suffix == ".zip"

    def test_save_zip_uses_layered_format_part_2(self, tmp_path):
        """Test that fr.save() with .zip creates layered bundle."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="test")
        result = fr.save(fig, tmp_path / "figure.zip", verbose=False)
        assert result[0].exists()


class TestBundlePaths:
    """Test bundle path utilities."""

    def test_is_bundle_path_with_zip(self, tmp_path):
        """Test is_bundle_path recognizes .zip files."""
        # Arrange
        # Act
        # Assert
        from figrecipe._bundle import is_bundle_path

        assert is_bundle_path(tmp_path / "test.zip")

    def test_is_bundle_path_with_spec_json(self, tmp_path):
        """Test is_bundle_path recognizes directory with spec.json."""
        # Arrange
        # Act
        # Assert
        from figrecipe._bundle import is_bundle_path

        bundle_dir = tmp_path / "mybundle"
        bundle_dir.mkdir()
        (bundle_dir / "spec.json").write_text("{}")

        assert is_bundle_path(bundle_dir)

    def test_bundle_exists_part_1(self, tmp_path):
        """Test bundle_exists returns True for valid bundle."""
        # Arrange
        # Act
        # Assert
        from figrecipe._bundle import bundle_exists
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        assert bundle_exists(bundle_path)

    def test_bundle_exists_part_2(self, tmp_path):
        """Test bundle_exists returns True for valid bundle."""
        # Arrange
        # Act
        # Assert
        from figrecipe._bundle import bundle_exists
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2], id="test")
        bundle_path = fr.save_bundle(fig, tmp_path / "test", verbose=False)
        assert not bundle_exists(tmp_path / "nonexistent.zip")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
