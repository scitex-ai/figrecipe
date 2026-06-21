#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image comparison utilities for roundtrip testing."""

from pathlib import Path
from typing import Tuple, Union

import numpy as np


def load_image(path: Union[str, Path]) -> np.ndarray:
    """Load image as numpy array.

    Parameters
    ----------
    path : str or Path
        Path to image file.

    Returns
    -------
    np.ndarray
        Image as (H, W, C) array with values 0-255.

    Raises
    ------
    ValueError
        If image exceeds maximum allowed size (decompression bomb protection).
    """
    from PIL import Image

    # Temporarily increase limit for scientific figures (some can be large)
    # Default is ~178M pixels, allow up to 500M
    old_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = 500_000_000

    try:
        img = Image.open(path).convert("RGB")
        return np.array(img)
    except Image.DecompressionBombError:
        raise ValueError(f"Image too large to load safely (>500M pixels): {path}")
    finally:
        Image.MAX_IMAGE_PIXELS = old_limit


def compute_diff(
    img1: np.ndarray,
    img2: np.ndarray,
) -> Tuple[float, np.ndarray]:
    """Compute pixel-level difference between two images.

    Parameters
    ----------
    img1 : np.ndarray
        First image (H, W, C).
    img2 : np.ndarray
        Second image (H, W, C).

    Returns
    -------
    mse : float
        Mean squared error (0 = identical).
    diff_img : np.ndarray
        Difference image (absolute difference).
    """
    # Ensure same shape
    if img1.shape != img2.shape:
        raise ValueError(f"Image shapes differ: {img1.shape} vs {img2.shape}")

    # Compute difference
    diff = np.abs(img1.astype(float) - img2.astype(float))
    mse = np.mean(diff**2)

    # Normalize diff for visualization
    diff_img = (
        (diff / diff.max() * 255).astype(np.uint8)
        if diff.max() > 0
        else diff.astype(np.uint8)
    )

    return mse, diff_img


def compare_images(
    path1: Union[str, Path],
    path2: Union[str, Path],
    diff_path: Union[str, Path] = None,
    size_tolerance: int = 2,
) -> dict:
    """Compare two image files.

    Parameters
    ----------
    path1 : str or Path
        Path to first image.
    path2 : str or Path
        Path to second image.
    diff_path : str or Path, optional
        If provided, save difference image here.
    size_tolerance : int
        Allow this many pixels of size difference (default: 2).
        If images differ by <= size_tolerance pixels in each dimension,
        compare the overlapping region.

    Returns
    -------
    dict
        Comparison results:
        - identical: bool (True if MSE == 0)
        - mse: float (mean squared error)
        - psnr: float (peak signal-to-noise ratio, inf if identical)
        - max_diff: float (maximum pixel difference)
        - size1: tuple (H, W) of first image
        - size2: tuple (H, W) of second image
        - same_size: bool (True if dimensions match)
        - file_size1: int (file size in bytes)
        - file_size2: int (file size in bytes)
    """
    import os

    img1 = load_image(path1)
    img2 = load_image(path2)

    # File sizes
    file_size1 = os.path.getsize(path1)
    file_size2 = os.path.getsize(path2)

    # Check if same size
    same_size = img1.shape == img2.shape

    if same_size:
        mse, diff_img = compute_diff(img1, img2)
    else:
        # Check if size difference is within tolerance
        h_diff = abs(img1.shape[0] - img2.shape[0])
        w_diff = abs(img1.shape[1] - img2.shape[1])

        if h_diff <= size_tolerance and w_diff <= size_tolerance:
            # Crop both images to overlapping region
            min_h = min(img1.shape[0], img2.shape[0])
            min_w = min(img1.shape[1], img2.shape[1])
            img1_cropped = img1[:min_h, :min_w]
            img2_cropped = img2[:min_h, :min_w]
            mse, diff_img = compute_diff(img1_cropped, img2_cropped)
        else:
            # Size difference too large
            mse = float("nan")
            diff_img = None

    # Peak signal-to-noise ratio
    if mse == 0:
        psnr = float("inf")
    elif np.isnan(mse):
        psnr = float("nan")
    else:
        psnr = 10 * np.log10(255**2 / mse)

    # Max difference
    if same_size:
        max_diff = np.max(np.abs(img1.astype(float) - img2.astype(float)))
    elif not np.isnan(mse):
        # Size within tolerance, compute max diff on overlapping region
        min_h = min(img1.shape[0], img2.shape[0])
        min_w = min(img1.shape[1], img2.shape[1])
        max_diff = np.max(
            np.abs(
                img1[:min_h, :min_w].astype(float) - img2[:min_h, :min_w].astype(float)
            )
        )
    else:
        max_diff = float("nan")

    # Save diff image if requested
    if diff_path is not None and diff_img is not None:
        from PIL import Image

        Image.fromarray(diff_img).save(diff_path)

    # Localize WHERE the images differ (helps diagnose a failed reproduction:
    # which fraction of the canvas changed, and the bounding box of the change as
    # fractions of H x W). Computed on the comparable (same-size or tolerance-
    # cropped) pixels; ``None`` when sizes are too different to overlap.
    diff_fraction, diff_bbox = _diff_region(img1, img2)

    return {
        "identical": mse == 0,
        "mse": float(mse),
        "psnr": float(psnr),
        "max_diff": float(max_diff),
        "size1": (img1.shape[0], img1.shape[1]),
        "size2": (img2.shape[0], img2.shape[1]),
        "same_size": img1.shape == img2.shape,
        "file_size1": file_size1,
        "file_size2": file_size2,
        "diff_fraction": diff_fraction,
        "diff_bbox": diff_bbox,
    }


def _diff_region(img1: np.ndarray, img2: np.ndarray, thresh: float = 10.0):
    """Fraction of differing pixels + their bounding box (H/W fractions).

    Returns ``(fraction, bbox)`` where ``bbox`` is
    ``(row_min, row_max, col_min, col_max)`` as fractions of height/width, or
    ``(None, None)`` if the images don't overlap. A pixel "differs" when its
    mean abs channel difference exceeds ``thresh`` (0-255), which ignores
    anti-aliasing jitter and isolates real changes.
    """
    min_h = min(img1.shape[0], img2.shape[0])
    min_w = min(img1.shape[1], img2.shape[1])
    if min_h == 0 or min_w == 0:
        return None, None
    a = img1[:min_h, :min_w].astype(float)
    b = img2[:min_h, :min_w].astype(float)
    dmap = np.abs(a - b).mean(axis=2) if a.ndim == 3 else np.abs(a - b)
    mask = dmap > thresh
    fraction = float(mask.mean())
    if not mask.any():
        return fraction, None
    ys, xs = np.where(mask)
    h, w = dmap.shape
    bbox = (
        round(float(ys.min()) / h, 3),
        round(float(ys.max()) / h, 3),
        round(float(xs.min()) / w, 3),
        round(float(xs.max()) / w, 3),
    )
    return fraction, bbox


def create_comparison_figure(
    original_path: Union[str, Path],
    reproduced_path: Union[str, Path],
    output_path: Union[str, Path],
    title: str = "Roundtrip Comparison",
):
    """Create a side-by-side comparison figure.

    Parameters
    ----------
    original_path : str or Path
        Path to original image.
    reproduced_path : str or Path
        Path to reproduced image.
    output_path : str or Path
        Path to save comparison figure.
    title : str
        Title for the comparison.
    """
    import matplotlib.pyplot as plt

    img1 = load_image(original_path)
    img2 = load_image(reproduced_path)

    try:
        mse, diff_img = compute_diff(img1, img2)
    except ValueError:
        # Different sizes, just show side by side
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        axes[0].imshow(img1)
        axes[0].set_title("Original")
        axes[0].axis("off")
        axes[1].imshow(img2)
        axes[1].set_title("Reproduced")
        axes[1].axis("off")
        fig.suptitle(f"{title}\n(Different sizes)", fontsize=14)
        fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(img1)
    axes[0].set_title("Original")
    axes[0].axis("off")

    axes[1].imshow(img2)
    axes[1].set_title("Reproduced")
    axes[1].axis("off")

    axes[2].imshow(diff_img)
    axes[2].set_title(f"Difference (MSE: {mse:.2f})")
    axes[2].axis("off")

    status = "IDENTICAL" if mse == 0 else f"MSE: {mse:.2f}"
    fig.suptitle(f"{title}\n{status}", fontsize=14, fontweight="bold")

    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
