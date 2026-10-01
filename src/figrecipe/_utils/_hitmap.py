#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hitmap visualization for comparing original and reproduced figures."""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np

from .._utils._optional import missing_extra

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


def create_hitmap(
    original: Union[str, Path, np.ndarray],
    reproduced: Union[str, Path, np.ndarray],
    output_path: Optional[Union[str, Path]] = None,
    mode: str = "diff",
    threshold: int = 0,
    show_bbox: bool = True,
    min_region_area: int = 10,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Create a hitmap visualization showing pixel differences.

    Parameters
    ----------
    original : str, Path, or ndarray
        Path to original image or numpy array.
    reproduced : str, Path, or ndarray
        Path to reproduced image or numpy array.
    output_path : str or Path, optional
        If provided, save the hitmap to this path.
    mode : str
        Visualization mode:
        - "diff": Red intensity shows magnitude of difference
        - "binary": Green = match, Red = mismatch
        - "heatmap": Colormap showing diff magnitude
    threshold : int
        Pixel difference threshold (0-255). Differences <= threshold
        are considered matches. Default 0 (exact match required).
    show_bbox : bool
        If True, draw yellow bounding boxes around diff regions.
    min_region_area : int
        Minimum pixel area for a region to get a bounding box.

    Returns
    -------
    hitmap : ndarray
        RGB hitmap image array.
    stats : dict
        Statistics including:
        - match_ratio: Fraction of matching pixels
        - mismatch_ratio: Fraction of mismatching pixels
        - max_diff: Maximum pixel difference
        - mean_diff: Mean pixel difference
        - mse: Mean squared error
        - regions: List of bounding boxes [(x1, y1, x2, y2), ...]
    """
    # Load images
    if isinstance(original, (str, Path)):
        img1 = np.array(Image.open(original).convert("RGB"))
    else:
        img1 = original

    if isinstance(reproduced, (str, Path)):
        img2 = np.array(Image.open(reproduced).convert("RGB"))
    else:
        img2 = reproduced

    # Ensure same shape
    if img1.shape != img2.shape:
        # Resize to match (use smaller dimensions)
        h = min(img1.shape[0], img2.shape[0])
        w = min(img1.shape[1], img2.shape[1])
        img1 = img1[:h, :w]
        img2 = img2[:h, :w]

    # Calculate difference
    diff = np.abs(img1.astype(np.float32) - img2.astype(np.float32))
    diff_gray = np.mean(diff, axis=2)  # Average across RGB channels

    # Calculate statistics
    max_diff = float(np.max(diff_gray))
    mean_diff = float(np.mean(diff_gray))
    mse = float(np.mean(diff_gray**2))

    # Create match/mismatch masks
    match_mask = diff_gray <= threshold
    mismatch_mask = ~match_mask

    total_pixels = diff_gray.size
    match_count = np.sum(match_mask)
    mismatch_count = np.sum(mismatch_mask)

    stats = {
        "match_ratio": float(match_count / total_pixels),
        "mismatch_ratio": float(mismatch_count / total_pixels),
        "match_pixels": int(match_count),
        "mismatch_pixels": int(mismatch_count),
        "total_pixels": int(total_pixels),
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "mse": mse,
    }

    # Create hitmap based on mode
    if mode == "binary":
        hitmap = _create_binary_hitmap(match_mask, mismatch_mask, img1.shape)
    elif mode == "heatmap":
        hitmap = _create_heatmap_hitmap(diff_gray, img1.shape)
    else:  # "diff" mode (default)
        hitmap = _create_diff_hitmap(diff_gray, match_mask, img1.shape)

    # Find and draw bounding boxes for diff regions
    regions = []
    if show_bbox and mismatch_count > 0:
        try:
            regions = _find_diff_regions(mismatch_mask, min_area=min_region_area)
            if regions:
                hitmap = _draw_bbox_on_hitmap(hitmap, regions)
        except ImportError:
            # scipy not available, skip region detection
            pass

    stats["regions"] = regions
    stats["num_regions"] = len(regions)

    # Save if output path provided
    if output_path is not None:
        Image.fromarray(hitmap).save(output_path)

    return hitmap, stats


def _create_binary_hitmap(
    match_mask: np.ndarray, mismatch_mask: np.ndarray, shape: tuple
) -> np.ndarray:
    """Create binary hitmap: green=match, red=mismatch."""
    hitmap = np.zeros(shape, dtype=np.uint8)
    hitmap[match_mask, 1] = 200  # Green for match
    hitmap[mismatch_mask, 0] = 255  # Red for mismatch
    return hitmap


def _create_diff_hitmap(
    diff_gray: np.ndarray, match_mask: np.ndarray, shape: tuple
) -> np.ndarray:
    """Create diff hitmap: green=match, red intensity=diff magnitude."""
    hitmap = np.zeros(shape, dtype=np.uint8)

    # Green for matching pixels (dim green)
    hitmap[match_mask, 1] = 150

    # Red for mismatching pixels (intensity = diff magnitude)
    mismatch_mask = ~match_mask
    if np.any(mismatch_mask):
        # Normalize diff to 0-255 range
        diff_normalized = diff_gray[mismatch_mask]
        max_val = np.max(diff_normalized) if np.max(diff_normalized) > 0 else 1
        intensity = (diff_normalized / max_val * 255).astype(np.uint8)
        hitmap[mismatch_mask, 0] = np.maximum(intensity, 100)  # Min red=100

    return hitmap


def _find_diff_regions(mismatch_mask: np.ndarray, min_area: int = 10) -> list:
    """Find connected regions of pixel differences.

    Returns list of bounding boxes: [(x1, y1, x2, y2), ...]
    """
    from scipy import ndimage

    # Label connected components
    labeled, num_features = ndimage.label(mismatch_mask)

    regions = []
    for i in range(1, num_features + 1):
        component = labeled == i
        if np.sum(component) < min_area:
            continue

        # Find bounding box
        rows = np.any(component, axis=1)
        cols = np.any(component, axis=0)
        y1, y2 = np.where(rows)[0][[0, -1]]
        x1, x2 = np.where(cols)[0][[0, -1]]

        regions.append((int(x1), int(y1), int(x2), int(y2)))

    return regions


def _draw_bbox_on_hitmap(
    hitmap: np.ndarray,
    regions: list,
    color: tuple = (255, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draw bounding boxes on hitmap."""
    result = hitmap.copy()

    for x1, y1, x2, y2 in regions:
        # Draw rectangle
        # Top edge
        result[y1 : y1 + thickness, x1:x2, :] = color
        # Bottom edge
        result[y2 - thickness : y2, x1:x2, :] = color
        # Left edge
        result[y1:y2, x1 : x1 + thickness, :] = color
        # Right edge
        result[y1:y2, x2 - thickness : x2, :] = color

    return result


def _create_heatmap_hitmap(diff_gray: np.ndarray, shape: tuple) -> np.ndarray:
    """Create heatmap hitmap using colormap."""
    import matplotlib.pyplot as plt

    # Normalize diff to 0-1 range
    max_val = np.max(diff_gray) if np.max(diff_gray) > 0 else 1
    diff_normalized = diff_gray / max_val

    # Apply colormap (viridis or hot)
    cmap = plt.cm.hot
    colored = cmap(diff_normalized)[:, :, :3]  # Remove alpha
    hitmap = (colored * 255).astype(np.uint8)

    return hitmap


def generate_hitmap_report(
    original_path: Union[str, Path],
    reproduced_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict:
    """Generate a complete hitmap report for a figure comparison.

    Parameters
    ----------
    original_path : str or Path
        Path to original figure.
    reproduced_path : str or Path
        Path to reproduced figure.
    output_dir : str or Path, optional
        Directory to save hitmap. If None, uses original's directory.

    Returns
    -------
    dict
        Report containing paths and statistics.
    """
    original_path = Path(original_path)
    reproduced_path = Path(reproduced_path)

    if output_dir is None:
        output_dir = original_path.parent
    else:
        output_dir = Path(output_dir)

    # Generate hitmap filename
    stem = original_path.stem.replace("_reproduced", "")
    hitmap_path = output_dir / f"{stem}_hitmap.png"

    # Create hitmap
    hitmap, stats = create_hitmap(
        original_path, reproduced_path, output_path=hitmap_path, mode="diff"
    )

    # Determine pass/fail
    is_match = stats["mismatch_pixels"] == 0

    return {
        "original": str(original_path),
        "reproduced": str(reproduced_path),
        "hitmap": str(hitmap_path),
        "is_pixel_perfect": is_match,
        "stats": stats,
    }


def compute_diff_stats(
    original: Union[str, Path, np.ndarray],
    reproduced: Union[str, Path, np.ndarray],
    threshold: int = 0,
) -> Dict[str, float]:
    """Compute difference statistics between two images without visualization.

    Parameters
    ----------
    original : str, Path, or ndarray
        Path to original image or numpy array.
    reproduced : str, Path, or ndarray
        Path to reproduced image or numpy array.
    threshold : int
        Pixel difference threshold (0-255). Differences <= threshold
        are considered matches. Default 0 (exact match required).

    Returns
    -------
    stats : dict
        Statistics including:
        - match_ratio: Fraction of matching pixels
        - mismatch_ratio: Fraction of mismatching pixels
        - match_pixels: Number of matching pixels
        - mismatch_pixels: Number of mismatching pixels
        - total_pixels: Total number of pixels
        - max_diff: Maximum pixel difference
        - mean_diff: Mean pixel difference
        - mse: Mean squared error
    """
    # Load images
    if isinstance(original, (str, Path)):
        img1 = np.array(Image.open(original).convert("RGB"))
    else:
        img1 = original

    if isinstance(reproduced, (str, Path)):
        img2 = np.array(Image.open(reproduced).convert("RGB"))
    else:
        img2 = reproduced

    # Ensure same shape
    if img1.shape != img2.shape:
        h = min(img1.shape[0], img2.shape[0])
        w = min(img1.shape[1], img2.shape[1])
        img1 = img1[:h, :w]
        img2 = img2[:h, :w]

    # Calculate difference
    diff = np.abs(img1.astype(np.float32) - img2.astype(np.float32))
    diff_gray = np.mean(diff, axis=2)

    # Calculate statistics
    max_diff = float(np.max(diff_gray))
    mean_diff = float(np.mean(diff_gray))
    mse = float(np.mean(diff_gray**2))

    # Create match/mismatch masks
    match_mask = diff_gray <= threshold
    total_pixels = diff_gray.size
    match_count = np.sum(match_mask)
    mismatch_count = total_pixels - match_count

    return {
        "match_ratio": float(match_count / total_pixels),
        "mismatch_ratio": float(mismatch_count / total_pixels),
        "match_pixels": int(match_count),
        "mismatch_pixels": int(mismatch_count),
        "total_pixels": int(total_pixels),
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "mse": mse,
    }


__all__ = ["create_hitmap", "generate_hitmap_report", "compute_diff_stats"]
