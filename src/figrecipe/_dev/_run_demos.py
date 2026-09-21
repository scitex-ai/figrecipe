#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo runner for all plotters."""

from pathlib import Path

import scitex_logging as slogging

from .._utils._optional import missing_extra
from ._plotters import PLOTTERS

console = slogging.getConsole(f"{__name__}.console")


def _compare_images(
    img1_path, img2_path, tolerance=0, size_tolerance=2, hitmap_path=None
):
    """Compare two images pixel by pixel.

    Parameters
    ----------
    img1_path : Path
        Path to first image.
    img2_path : Path
        Path to second image.
    tolerance : int
        Maximum allowed pixel difference (0 for exact match).
    size_tolerance : int
        Maximum allowed size difference in each dimension (default: 2).
        If images differ by <= size_tolerance pixels in height/width,
        compare the overlapping region.
    hitmap_path : Path, optional
        If provided and images don't match, generate a hitmap at this path.

    Returns
    -------
    tuple
        (is_match, max_diff, mean_diff, diff_pixels, size_info)
    """
    import numpy as np
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    img1 = np.array(Image.open(img1_path))
    img2 = np.array(Image.open(img2_path))

    size_info = {"size1": img1.shape[:2], "size2": img2.shape[:2], "same_size": True}

    if img1.shape != img2.shape:
        # Check if size difference is within tolerance
        h_diff = abs(img1.shape[0] - img2.shape[0])
        w_diff = abs(img1.shape[1] - img2.shape[1])

        if h_diff <= size_tolerance and w_diff <= size_tolerance:
            # Crop both images to overlapping region
            min_h = min(img1.shape[0], img2.shape[0])
            min_w = min(img1.shape[1], img2.shape[1])
            img1 = img1[:min_h, :min_w]
            img2 = img2[:min_h, :min_w]
            size_info["same_size"] = False
        else:
            # Size difference too large
            return False, float("inf"), float("inf"), -1, size_info

    diff = np.abs(img1.astype(float) - img2.astype(float))
    max_diff = diff.max()
    mean_diff = diff.mean()
    diff_pixels = (diff > tolerance).sum()

    is_match = max_diff <= tolerance

    # Generate hitmap on mismatch if path provided
    if not is_match and hitmap_path is not None:
        try:
            from .._utils._hitmap import create_hitmap

            create_hitmap(
                img1, img2, output_path=hitmap_path, mode="diff", threshold=tolerance
            )
        except Exception:
            pass  # Hitmap generation is optional

    return is_match, max_diff, mean_diff, diff_pixels, size_info


def run_all_demos(
    fr,
    output_dir=None,
    show=False,
    verbose=True,
    reproduce=False,
    pixel_perfect=False,
    tolerance=0,
    save_hitmap=True,
    representative_only=False,
):
    """Run all demo plotters and save outputs using fr.save().

    Parameters
    ----------
    fr : module
        figrecipe module (e.g., `import figrecipe as fr`).
    output_dir : Path or str, optional
        Directory to save output images. If None, uses /tmp/figrecipe_demos.
    show : bool
        Whether to show figures interactively.
    verbose : bool
        Whether to print progress.
    reproduce : bool
        Whether to also generate reproduced plots from YAML recipes.
    pixel_perfect : bool
        If True, compare each plot with its reproduction immediately and
        STOP on first non-matching plot. Implies reproduce=True.
    tolerance : int
        Maximum allowed pixel difference for pixel_perfect mode (0 for exact).
    save_hitmap : bool
        If True (default), save GUI editor hitmaps alongside each figure.
    representative_only : bool
        If True, run only 18 representative plot types for faster testing.
        If False (default), run all 47 plot types.

    Returns
    -------
    dict
        Results for each demo: {name: {'success': bool, 'error': str or None, 'path': str}}
    """
    import matplotlib.pyplot as _plt
    import numpy as np

    from ._plotters import list_plotters

    rng = np.random.default_rng(42)
    results = {}

    if output_dir is None:
        output_dir = Path("/tmp/figrecipe_demos")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # pixel_perfect implies reproduce
    if pixel_perfect:
        reproduce = True

    # Get plotters to run
    plotter_names = list_plotters(representative_only=representative_only)
    plotters_to_run = {
        name: PLOTTERS[name] for name in plotter_names if name in PLOTTERS
    }
    total = len(plotters_to_run)

    # Sequential mode: plot -> reproduce -> verify -> next
    if pixel_perfect:
        if verbose:
            console.info("=" * 60)
            console.info("PIXEL-PERFECT VERIFICATION MODE")
            console.info(f"Tolerance: {tolerance} (0 = exact match)")
            console.info("=" * 60)

        for i, (name, func) in enumerate(sorted(plotters_to_run.items()), 1):
            if verbose:
                console.info(f"\n[{i}/{total}] Testing: {name}")
                console.info("-" * 40)

            # Step 1: Generate original plot
            try:
                fig, ax = func(fr, rng)
                out_path = output_dir / f"plot_{name}.png"
                yaml_path = output_dir / f"plot_{name}.yaml"
                fr.save(
                    fig,
                    out_path,
                    validate=False,
                    verbose=False,
                    save_hitmap=save_hitmap,
                )
                _plt.close("all")
                if verbose:
                    console.info(f"  [1/3] Original saved: {out_path.name}")
            except Exception as e:
                results[name] = {"success": False, "error": str(e), "path": None}
                console.error(f"  FAILED to generate: {e}")
                raise RuntimeError(f"Failed to generate {name}: {e}")

            # Step 2: Reproduce from YAML
            reproduced_path = output_dir / f"plot_{name}_reproduced.png"
            try:
                fig2, ax2 = fr.reproduce(str(yaml_path))
                fr.save(fig2, reproduced_path, validate=False, verbose=False)
                _plt.close("all")
                if verbose:
                    console.info(f"  [2/3] Reproduced saved: {reproduced_path.name}")
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": f"Reproduce failed: {e}",
                    "path": str(out_path),
                }
                console.error(f"  FAILED to reproduce: {e}")
                raise RuntimeError(f"Failed to reproduce {name}: {e}")

            # Step 3: Compare pixel by pixel
            hitmap_path = output_dir / f"plot_{name}_hitmap.png"
            is_match, max_diff, mean_diff, diff_pixels, size_info = _compare_images(
                out_path, reproduced_path, tolerance, hitmap_path=hitmap_path
            )

            if is_match:
                results[name] = {"success": True, "error": None, "path": str(out_path)}
                if verbose:
                    console.info("  [3/3] PIXEL-PERFECT MATCH ✓")
                    size_note = (
                        ""
                        if size_info["same_size"]
                        else f" (size tolerance: {size_info['size1']} vs {size_info['size2']})"
                    )
                    console.info(
                        f"        Max diff: {max_diff}, Mean diff: {mean_diff:.4f}{size_note}"
                    )
            else:
                results[name] = {
                    "success": False,
                    "error": f"Pixel mismatch: max={max_diff}, mean={mean_diff:.4f}, diff_pixels={diff_pixels}",
                    "path": str(out_path),
                    "hitmap": str(hitmap_path) if hitmap_path.exists() else None,
                }
                console.info("  [3/3] PIXEL MISMATCH ✗")
                console.info(f"        Size: {size_info['size1']} vs {size_info['size2']}")
                console.info(f"        Max diff: {max_diff}")
                console.info(f"        Mean diff: {mean_diff:.4f}")
                console.info(f"        Pixels differing: {diff_pixels}")
                if hitmap_path.exists():
                    console.info(f"        Hitmap: {hitmap_path}")
                console.info("\n" + "=" * 60)
                console.info(f"STOPPED AT: {name}")
                console.info(f"Original:   {out_path}")
                console.info(f"Reproduced: {reproduced_path}")
                if hitmap_path.exists():
                    console.info(f"Hitmap:     {hitmap_path}")
                console.info("=" * 60)
                assert False, (
                    f"Pixel-perfect reproduction FAILED for '{name}': "
                    f"max_diff={max_diff}, mean_diff={mean_diff:.4f}, "
                    f"original={out_path}, reproduced={reproduced_path}"
                )

        if verbose:
            console.info("\n" + "=" * 60)
            console.info(f"ALL {total} PLOTS PIXEL-PERFECT ✓")
            console.info("=" * 60)

        return results

    # Original batch mode
    for i, (name, func) in enumerate(sorted(plotters_to_run.items()), 1):
        try:
            fig, ax = func(fr, rng)
            out_path = output_dir / f"plot_{name}.png"
            # Use fr.save() for proper mm layout and auto-cropping
            fr.save(
                fig, out_path, validate=False, verbose=False, save_hitmap=save_hitmap
            )
            if show:
                _plt.show()
            else:
                _plt.close("all")
            results[name] = {"success": True, "error": None, "path": str(out_path)}
            if verbose:
                console.info(f"[{i}/{total}] {name}: OK")
        except Exception as e:
            results[name] = {"success": False, "error": str(e), "path": None}
            if verbose:
                console.error(f"[{i}/{total}] {name}: FAILED - {e}")
            _plt.close("all")

    # Generate reproduced plots if requested
    if reproduce:
        if verbose:
            console.info("\nGenerating reproduced plots...")
        reproduced_count = 0
        failed_reproductions = []
        for name, result in results.items():
            if result["success"]:
                yaml_path = output_dir / f"plot_{name}.yaml"
                reproduced_path = output_dir / f"plot_{name}_reproduced.png"
                if yaml_path.exists():
                    try:
                        # fr.reproduce returns (fig, ax), use fr.save for proper styling
                        fig, ax = fr.reproduce(str(yaml_path))
                        fr.save(fig, reproduced_path, validate=False, verbose=False)
                        reproduced_count += 1
                        if verbose:
                            console.info(f"  Reproduced: {name}")
                    except Exception as e:
                        failed_reproductions.append((name, str(e)))
                        if verbose:
                            console.error(f"  FAILED to reproduce {name}: {e}")
                    _plt.close("all")
        if verbose:
            console.info(f"Reproduced {reproduced_count} plots")
        if failed_reproductions:
            raise RuntimeError(
                f"Failed to reproduce {len(failed_reproductions)} plots: "
                + ", ".join(f"{n}: {e}" for n, e in failed_reproductions)
            )

    # Summary
    success = sum(1 for r in results.values() if r["success"])
    if verbose:
        console.info(f"\nSummary: {success}/{total} demos succeeded")
        console.info(f"Output directory: {output_dir}")

    return results


# EOF
