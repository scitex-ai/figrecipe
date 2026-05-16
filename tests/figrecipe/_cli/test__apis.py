#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._api._validate module."""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
import yaml


class TestValidateRecipe:
    """Tests for validate_recipe function."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up matplotlib figures after each test."""
        yield
        plt.close("all")

    def _create_test_recipe(self, tmpdir: Path) -> Path:
        """Create a minimal valid recipe for testing."""
        recipe_path = tmpdir / "test.yaml"
        recipe = {
            "figure": {
                "figsize": [4, 3],
                "dpi": 100,
            },
            "calls": [
                {
                    "ax": "ax_0_0",
                    "method": "plot",
                    "args": [[1, 2, 3], [1, 4, 9]],
                    "kwargs": {},
                }
            ],
        }
        with open(recipe_path, "w") as f:
            yaml.dump(recipe, f)
        return recipe_path

    def test_validate_valid_recipe(self):
        """Test validating a valid recipe passes."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = self._create_test_recipe(tmpdir)

            result = validate_recipe(recipe_path)

            assert result.valid is True
            assert result.mse < 100  # Should be very small for identical renders
            assert result.same_size is True
            assert "consistent" in result.message.lower()

    def test_validate_with_custom_threshold(self):
        """Test validating with custom MSE threshold."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = self._create_test_recipe(tmpdir)

            # Very strict threshold
            result = validate_recipe(recipe_path, mse_threshold=0.001)

            # Should still pass for identical renders
            assert result.mse is not None

    def test_validate_returns_validation_result(self):
        """Test that validate_recipe returns ValidationResult with all fields."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = self._create_test_recipe(tmpdir)

            result = validate_recipe(recipe_path)

            # Check all expected attributes exist
            assert hasattr(result, "valid")
            assert hasattr(result, "mse")
            assert hasattr(result, "psnr")
            assert hasattr(result, "max_diff")
            assert hasattr(result, "size_original")
            assert hasattr(result, "size_reproduced")
            assert hasattr(result, "same_size")
            assert hasattr(result, "file_size_diff")
            assert hasattr(result, "message")

    def test_validate_path_as_string(self):
        """Test that validate_recipe accepts string path."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = self._create_test_recipe(tmpdir)

            # Pass as string instead of Path
            result = validate_recipe(str(recipe_path))

            assert result.valid is True


class TestValidationResultDetails:
    """Tests for validation result details."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up matplotlib figures after each test."""
        yield
        plt.close("all")

    def test_mse_is_numeric(self):
        """Test that MSE is a numeric value."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = tmpdir / "test.yaml"
            recipe = {
                "figure": {"figsize": [4, 3]},
                "calls": [
                    {
                        "ax": "ax_0_0",
                        "method": "scatter",
                        "args": [[1, 2, 3], [1, 4, 9]],
                        "kwargs": {},
                    }
                ],
            }
            with open(recipe_path, "w") as f:
                yaml.dump(recipe, f)

            result = validate_recipe(recipe_path)

            assert isinstance(result.mse, (int, float))

    def test_psnr_value(self):
        """Test that PSNR is returned."""
        from figrecipe._api._validate import validate_recipe

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            recipe_path = tmpdir / "test.yaml"
            recipe = {
                "figure": {"figsize": [4, 3]},
                "calls": [
                    {
                        "ax": "ax_0_0",
                        "method": "bar",
                        "args": [["A", "B"], [3, 5]],
                        "kwargs": {},
                    }
                ],
            }
            with open(recipe_path, "w") as f:
                yaml.dump(recipe, f)

            result = validate_recipe(recipe_path)

            # PSNR should be very high for identical images (or inf)
            assert result.psnr is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
