#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducibility validation for figrecipe recipes."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np


@dataclass
class ValidationResult:
    """Result of reproducibility validation.

    Attributes
    ----------
    valid : bool
        True if reproduction is considered valid (MSE below threshold).
    mse : float
        Mean squared error between original and reproduced images.
    psnr : float
        Peak signal-to-noise ratio (higher is better, inf if identical).
    max_diff : float
        Maximum pixel difference (0-255 scale).
    size_original : tuple
        (height, width) of original image.
    size_reproduced : tuple
        (height, width) of reproduced image.
    same_size : bool
        True if dimensions match exactly.
    file_size_diff : int
        Difference in file sizes (bytes).
    message : str
        Human-readable summary.
    """

    valid: bool
    mse: float
    psnr: float
    max_diff: float
    size_original: tuple
    size_reproduced: tuple
    same_size: bool
    file_size_diff: int
    message: str
    # On failure, the reproduced figure is persisted here (``<stem>-not-
    # reproduced.<ext>`` beside the saved figure) for visual inspection; None
    # when validation passes or no image path was provided.
    not_reproduced_path: Optional[str] = None

    def __repr__(self) -> str:
        status = "VALID" if self.valid else "INVALID"
        return (
            f"ValidationResult({status}, mse={self.mse:.2f}, "
            f"size={'match' if self.same_size else 'differ'})"
        )

    def summary(self) -> str:
        """Return detailed summary string."""
        lines = [
            f"Reproducibility Validation: {'PASSED' if self.valid else 'FAILED'}",
            f"  Dimensions: {self.size_original} vs {self.size_reproduced} "
            f"({'match' if self.same_size else 'DIFFER'})",
            f"  Pixel MSE: {self.mse:.2f}",
            f"  Max pixel diff: {self.max_diff:.1f}",
            f"  PSNR: {self.psnr:.1f} dB"
            if not np.isinf(self.psnr)
            else "  PSNR: inf (identical)",
            f"  File size diff: {self.file_size_diff:+d} bytes",
        ]
        if not self.valid:
            lines.append(f"  Note: {self.message}")
        return "\n".join(lines)


def _pixel_divergence_message(mse: float, mse_threshold: float, diff: dict) -> str:
    """Actionable message for a same-size reproduction that diverges in pixels.

    States the MSE vs threshold, how much of the canvas changed, and where the
    change is concentrated (bounding box as % of the figure) so the cause is
    legible from the log instead of a bare "MSE exceeds threshold".
    """
    msg = (
        f"same image size but pixels differ: MSE ({mse:.2f}) exceeds threshold "
        f"({mse_threshold})"
    )
    frac = diff.get("diff_fraction")
    bbox = diff.get("diff_bbox")
    if frac is not None:
        msg += f"; {frac:.1%} of pixels changed"
    if bbox is not None:
        r0, r1, c0, c1 = bbox
        msg += (
            f", concentrated in rows {r0:.0%}-{r1:.0%} x cols {c0:.0%}-{c1:.0%} "
            f"(top-left origin)"
        )
    md = diff.get("max_diff")
    if md is not None and not np.isnan(md):
        msg += f"; max channel diff {md:.0f}/255"
    return msg


def validate_recipe(
    fig,
    recipe_path: Union[str, Path],
    mse_threshold: float = 100.0,
    dpi: int = 150,
    image_path: Union[str, Path, None] = None,
) -> ValidationResult:
    """Validate that a recipe can faithfully reproduce the original figure.

    Parameters
    ----------
    fig : RecordingFigure
        The original figure (with matplotlib figure accessible via fig.fig).
    recipe_path : str or Path
        Path to the saved recipe file.
    mse_threshold : float
        Maximum acceptable MSE for validation to pass (default: 100).
        Lower values require closer matches.
    dpi : int
        DPI for comparison images (default: 150).

    Returns
    -------
    ValidationResult
        Detailed comparison results.
    """
    import matplotlib.pyplot as plt

    # NB: these are siblings of figrecipe/, NOT siblings of figrecipe/_quality/.
    # Pre-#141 this file lived at figrecipe/_validator.py, so `from ._reproducer`
    # / `from ._utils._image_diff` resolved correctly. After the move into
    # _quality/, the original rename pass updated other files' references to
    # the moved modules but missed THIS file's internal relative imports back
    # to its (former) siblings. Bump one level.
    from .._reproducer import reproduce
    from .._utils._image_diff import compare_images

    recipe_path = Path(recipe_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Save original figure to temp image
        # Use the same saving approach for both to ensure consistent comparison
        original_path = tmpdir / "original.png"

        # Use RecordingFigure.savefig for original to ensure consistent
        # tick finalization and cropping behavior with reproduced figure
        fig.savefig(original_path, save_recipe=False, dpi=dpi, verbose=False)

        # Reproduce from recipe
        reproduced_fig, _ = reproduce(recipe_path)

        # Save reproduced figure using same method as original
        reproduced_path = tmpdir / "reproduced.png"
        reproduced_fig.savefig(
            reproduced_path, save_recipe=False, dpi=dpi, verbose=False
        )

        # Compare images
        diff = compare_images(original_path, reproduced_path)

        # Determine validity, with an ACTIONABLE message on failure: say whether
        # it's a size mismatch or a same-size pixel divergence, and for the latter
        # how much of the canvas changed + where (so the cause is obvious from the
        # log, not a bare "FAILED").
        mse = diff["mse"]
        if np.isnan(mse):
            valid = False
            message = (
                f"image SIZE mismatch: original {diff['size1']} (HxW) vs "
                f"reproduced {diff['size2']} -- the reproduced figure has "
                f"different pixel dimensions (layout/figsize not reproduced)"
            )
        elif mse > mse_threshold:
            valid = False
            message = _pixel_divergence_message(mse, mse_threshold, diff)
        else:
            valid = True
            message = "Reproduction matches original within threshold"

        # On FAILURE, persist the reproduced figure next to the saved one as
        # ``<stem>-not-reproduced.<ext>`` so the divergence is inspectable (the
        # whole point: see WHAT the recipe failed to reproduce). On success,
        # remove any stale artifact from a previous failing run so a green save
        # never leaves a misleading "-not-reproduced" file behind.
        not_reproduced_path = None
        if image_path is not None:
            p = Path(image_path)
            artifact = p.parent / f"{p.stem}-not-reproduced{p.suffix}"
            if not valid:
                try:
                    reproduced_fig.savefig(
                        artifact, save_recipe=False, dpi=dpi, verbose=False
                    )
                    not_reproduced_path = str(artifact)
                except Exception:
                    not_reproduced_path = None
            elif artifact.exists():
                try:
                    artifact.unlink()
                except OSError:
                    pass

        # Close reproduced figure to prevent double display in notebooks. Use
        # .fig to get the underlying matplotlib Figure (reproduce() returns a
        # RecordingFigure).
        mpl_fig = (
            reproduced_fig.fig if hasattr(reproduced_fig, "fig") else reproduced_fig
        )
        plt.close(mpl_fig)

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
            not_reproduced_path=not_reproduced_path,
        )


def validate_on_save(
    fig,
    recipe_path: Union[str, Path],
    mse_threshold: float = 100.0,
    dpi: int = 150,
    raise_on_failure: bool = False,
    image_path: Union[str, Path, None] = None,
) -> Optional[ValidationResult]:
    """Validate recipe immediately after saving.

    Parameters
    ----------
    fig : RecordingFigure
        The original figure.
    recipe_path : str or Path
        Path where recipe was saved.
    mse_threshold : float
        Maximum acceptable MSE.
    dpi : int
        DPI for comparison.
    raise_on_failure : bool
        If True, raise ValueError when validation fails.
    image_path : str or Path, optional
        Path of the saved figure image. When given and validation fails, the
        reproduced figure is written beside it as ``<stem>-not-reproduced.<ext>``
        for inspection.

    Returns
    -------
    ValidationResult
        Validation results.

    Raises
    ------
    ValueError
        If raise_on_failure=True and validation fails.
    """
    result = validate_recipe(
        fig, recipe_path, mse_threshold, dpi, image_path=image_path
    )

    if raise_on_failure and not result.valid:
        raise ValueError(f"Recipe validation failed: {result.message}")

    return result
