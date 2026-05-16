#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for bundle and path resolution functionality.

These tests verify that reproduce() and edit() can handle:
- Direct YAML files
- Image files with associated YAML
- Bundle directories containing recipe.yaml
- ZIP archives containing recipe.yaml
"""

import shutil
import zipfile

import pytest


class TestResolveRecipePath:
    """Test the resolve_recipe_path utility function."""

    def test_resolve_yaml_file(self, tmp_path):
        """Test resolving a direct YAML file."""
        from figrecipe._utils._bundle import resolve_recipe_path

        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(yaml_file)
        assert path == yaml_file
        assert temp_dir is None

    def test_resolve_yml_file(self, tmp_path):
        """Test resolving a .yml file."""
        from figrecipe._utils._bundle import resolve_recipe_path

        yml_file = tmp_path / "test.yml"
        yml_file.write_text("figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(yml_file)
        assert path == yml_file
        assert temp_dir is None

    def test_resolve_png_with_yaml(self, tmp_path):
        """Test resolving PNG file finds associated YAML."""
        from figrecipe._utils._bundle import resolve_recipe_path

        yaml_file = tmp_path / "figure.yaml"
        yaml_file.write_text("figsize: [6, 4]\n")
        png_file = tmp_path / "figure.png"
        png_file.write_bytes(b"fake png")

        path, temp_dir = resolve_recipe_path(png_file)
        assert path == yaml_file
        assert temp_dir is None

    def test_resolve_png_missing_yaml_raises(self, tmp_path):
        """Test that PNG without YAML raises error."""
        from figrecipe._utils._bundle import resolve_recipe_path

        png_file = tmp_path / "figure.png"
        png_file.write_bytes(b"fake png")

        with pytest.raises(FileNotFoundError, match="Recipe file not found"):
            resolve_recipe_path(png_file)

    def test_resolve_directory_with_recipe_yaml(self, tmp_path):
        """Test resolving a directory bundle with recipe.yaml."""
        from figrecipe._utils._bundle import resolve_recipe_path

        bundle_dir = tmp_path / "figure_bundle"
        bundle_dir.mkdir()
        recipe = bundle_dir / "recipe.yaml"
        recipe.write_text("figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(bundle_dir)
        assert path == recipe
        assert temp_dir is None

    def test_resolve_directory_with_single_yaml(self, tmp_path):
        """Test resolving a directory with a single (non-recipe) YAML."""
        from figrecipe._utils._bundle import resolve_recipe_path

        bundle_dir = tmp_path / "figure_bundle"
        bundle_dir.mkdir()
        yaml_file = bundle_dir / "custom_name.yaml"
        yaml_file.write_text("figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(bundle_dir)
        assert path == yaml_file
        assert temp_dir is None

    def test_resolve_directory_no_yaml_raises(self, tmp_path):
        """Test that empty directory raises error."""
        from figrecipe._utils._bundle import resolve_recipe_path

        bundle_dir = tmp_path / "empty_bundle"
        bundle_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="No recipe found"):
            resolve_recipe_path(bundle_dir)

    def test_resolve_zip_with_recipe_yaml(self, tmp_path):
        """Test resolving a ZIP file containing recipe.yaml."""
        from figrecipe._utils._bundle import resolve_recipe_path

        # Create a ZIP file with recipe.yaml
        zip_path = tmp_path / "figure.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("recipe.yaml", "figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(zip_path)
        try:
            assert path.name == "recipe.yaml"
            assert path.exists()
            assert temp_dir is not None
            assert temp_dir.exists()
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_resolve_zip_with_nested_recipe(self, tmp_path):
        """Test resolving a ZIP with nested recipe.yaml."""
        from figrecipe._utils._bundle import resolve_recipe_path

        zip_path = tmp_path / "figure.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("figure/recipe.yaml", "figsize: [6, 4]\n")

        path, temp_dir = resolve_recipe_path(zip_path)
        try:
            assert path.name == "recipe.yaml"
            assert path.exists()
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_resolve_zip_no_yaml_raises(self, tmp_path):
        """Test that ZIP without YAML raises error."""
        from figrecipe._utils._bundle import resolve_recipe_path

        zip_path = tmp_path / "figure.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No recipe here")

        with pytest.raises(FileNotFoundError, match="No recipe found"):
            resolve_recipe_path(zip_path)

    def test_resolve_nonexistent_path_raises(self, tmp_path):
        """Test that nonexistent path raises error."""
        from figrecipe._utils._bundle import resolve_recipe_path

        with pytest.raises(FileNotFoundError, match="Path not found"):
            resolve_recipe_path(tmp_path / "nonexistent.yaml")


class TestIsBundlePath:
    """Test the is_bundle_path utility function."""

    def test_directory_is_bundle(self, tmp_path):
        """Test that directory is recognized as bundle."""
        from figrecipe._utils._bundle import is_bundle_path

        bundle_dir = tmp_path / "bundle"
        bundle_dir.mkdir()
        assert is_bundle_path(bundle_dir) is True

    def test_zip_is_bundle(self, tmp_path):
        """Test that ZIP file is recognized as bundle."""
        from figrecipe._utils._bundle import is_bundle_path

        zip_path = tmp_path / "bundle.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "test")
        assert is_bundle_path(zip_path) is True

    def test_yaml_is_not_bundle(self, tmp_path):
        """Test that YAML file is not recognized as bundle."""
        from figrecipe._utils._bundle import is_bundle_path

        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: true\n")
        assert is_bundle_path(yaml_file) is False

    def test_nonexistent_is_not_bundle(self, tmp_path):
        """Test that nonexistent path returns False."""
        from figrecipe._utils._bundle import is_bundle_path

        assert is_bundle_path(tmp_path / "nonexistent") is False


class TestReproduceFromBundle:
    """Test reproduce() with bundle directories and ZIPs."""

    @pytest.fixture
    def sample_recipe_content(self):
        """Create sample recipe content."""
        return """\
id: test_figure
created: '2024-01-01T00:00:00'
matplotlib_version: '3.8.0'
figsize: [6.0, 4.0]
dpi: 100
constrained_layout: false
axes:
  ax_0_0:
    calls: []
    decorations: []
"""

    def test_reproduce_from_directory(self, tmp_path, sample_recipe_content):
        """Test reproducing from a bundle directory."""
        import figrecipe as fr

        bundle_dir = tmp_path / "figure_bundle"
        bundle_dir.mkdir()
        recipe = bundle_dir / "recipe.yaml"
        recipe.write_text(sample_recipe_content)

        fig, ax = fr.reproduce(bundle_dir)
        assert fig is not None
        assert ax is not None

    def test_reproduce_from_zip(self, tmp_path, sample_recipe_content):
        """Test reproducing from a ZIP archive."""
        import figrecipe as fr

        zip_path = tmp_path / "figure.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("recipe.yaml", sample_recipe_content)

        fig, ax = fr.reproduce(zip_path)
        assert fig is not None
        assert ax is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
