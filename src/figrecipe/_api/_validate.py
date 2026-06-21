#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone validation implementation."""

import tempfile
from pathlib import Path
from typing import Union

import numpy as np

from .._reproducer import reproduce
from .._utils._image_diff import compare_images
from .._quality._validator import ValidationResult


def validate_recipe(
    path: Union[str, Path],
    mse_threshold: float = 100.0,
) -> ValidationResult:
    """Validate that a saved recipe can reproduce its original figure.

    For standalone validation, we reproduce twice and compare
    (This validates the recipe is self-consistent).

    Parameters
    ----------
    path : str or Path
        Path to .yaml recipe file.
    mse_threshold : float
        Maximum acceptable MSE for validation to pass (default: 100).

    Returns
    -------
    ValidationResult
        Detailed comparison results.
    """
    path = Path(path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Reproduce twice
        fig1, _ = reproduce(path)
        img1_path = tmpdir / "render1.png"
        fig1.savefig(img1_path, dpi=150)

        fig2, _ = reproduce(path)
        img2_path = tmpdir / "render2.png"
        fig2.savefig(img2_path, dpi=150)

        # Compare
        diff = compare_images(img1_path, img2_path)

        mse = diff["mse"]
        if np.isnan(mse):
            valid = False
            message = f"Image dimensions differ: {diff['size1']} vs {diff['size2']}"
        elif mse > mse_threshold:
            valid = False
            message = f"MSE ({mse:.2f}) exceeds threshold ({mse_threshold})"
        else:
            valid = True
            message = "Recipe produces consistent output"

        return ValidationResult(
            valid=valid,
            mse=mse if not np.isnan(mse) else float("inf"),
            psnr=diff["psnr"],
            max_diff=diff["max_diff"]
            if not np.isnan(diff["max_diff"])
            else float("inf"),
            size_original=diff["size1"],
            size_reproduced=diff["size2"],
            same_size=diff["same_size"],
            file_size_diff=diff["file_size2"] - diff["file_size1"],
            message=message,
        )


__all__ = ["validate_recipe"]

# EOF
