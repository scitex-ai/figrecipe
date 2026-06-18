#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic post-save crop dispatch for raster figures.

The save path RE-MEASURES ink at save time -- ``bbox_inches="tight"`` for
constrained_layout figures and the content-aware pixel ``crop()`` for composed
mm-layout figures. That re-measure jitters sub-pixel between the ORIGINAL figure
(drawn many times during build/save) and a fresh ``reproduce()``-d one (drawn a
few times); at a pixel-rounding boundary a 0.2 px shift flips the saved width by
1 px, and the validator's ``size_tolerance=2`` turns a >=3 px delta into
``mse=nan`` -> ``image SIZE mismatch`` -> ``<stem>-not-reproduced.png``
(shared ``fig.colorbar(ax=[...])``, ``ax.pie()``, constrained_layout, composed
mm-layout).

This module generalises the standalone-diagram crop (#215): whenever a usable,
dpi-independent ``content_bbox`` exists (recorded for every figure by
``_capture_content_layout``, byte-identical on reproduce), the figure is saved
FULL-CANVAS and cropped to that ONE recorded box -- so the original and every
reproduce land at identical pixels regardless of draw count. The legacy
``bbox_inches="tight"`` / content-aware ``crop()`` path is used ONLY when
``content_bbox`` cannot be derived (and then with a ``UserWarning`` -- no silent
fallback). #227 ``settle_constrained_layout`` + #230 ``cax_bbox`` pinning are
kept upstream (they keep axes geometry matched so MSE stays low); only the final
CROP changes here. Vector (SVG/PDF) exports never reach this dispatch.
"""

from pathlib import Path
from typing import Optional

from ._save_helpers import _crop_to_recorded_content_bbox

__all__ = ["wants_content_crop", "dispatch_crop"]


def wants_content_crop(is_croppable: bool, use_constrained: bool, mm_layout) -> bool:
    """True when the figure should be cropped to its recorded ``content_bbox``.

    Covers exactly the two raster cases whose saved SIZE is otherwise
    re-measured at save time:

    * ``use_constrained`` -- would crop via ``bbox_inches="tight"``.
    * a composed / mm-layout figure carrying ``crop_margin_*`` -- would crop
      content-aware.

    Both are size-deterministic only when cropped to the single recorded box.
    Figures that already crop deterministically (no constrained_layout and no
    mm-layout crop margins) keep their existing path untouched.
    """
    if not is_croppable:
        return False
    if use_constrained:
        return True
    return mm_layout is not None and "crop_margin_left_mm" in mm_layout


def dispatch_crop(
    fig,
    image_path: Path,
    *,
    is_croppable: bool,
    is_svg: bool,
    use_tight: bool,
    use_content_crop: bool,
    crop_margin_mm: Optional[float],
    crop_margins_mm,
    mm_layout,
    dpi: int,
) -> Optional[dict]:
    """Crop the saved image and return the ``crop_offset`` (or ``None``).

    Strategy, in order:

    1. ``use_content_crop`` -- crop to the recorded ``content_bbox`` (the
       deterministic path). On failure (``content_bbox`` underivable) this
       returns ``None`` WITH a ``UserWarning`` and we fall through to (2)/(3) so
       a missing box never silently skips cropping.
    2. raster, not already tight-cropped -- the legacy content-aware ``crop()``
       (explicit ``crop_margin_mm`` or per-side mm-layout margins).
    3. SVG, not tight -- ``crop_svg`` viewBox adjustment.

    ``use_tight`` figures were already cropped by ``bbox_inches="tight"`` at save
    time, so (2) is skipped for them (unless the collapse fallback cleared it).
    """
    ml, mr, mt, mb = crop_margins_mm

    if use_content_crop:
        crop_offset = _crop_to_recorded_content_bbox(
            fig, image_path, crop_margin_mm, crop_margins_mm, dpi
        )
        if crop_offset is not None:
            return crop_offset
        # content_bbox underivable: fall through to the legacy crop (warned).

    if is_croppable and not use_tight:
        from .._utils._crop import crop

        if crop_margin_mm is not None:
            _, crop_offset = crop(
                image_path,
                margin_mm=crop_margin_mm,
                output_path=image_path,
                return_offset=True,
            )
            return crop_offset
        if mm_layout is not None and "crop_margin_left_mm" in mm_layout:
            _, crop_offset = crop(
                image_path,
                margin_left_mm=ml,
                margin_right_mm=mr,
                margin_top_mm=mt,
                margin_bottom_mm=mb,
                output_path=image_path,
                return_offset=True,
            )
            return crop_offset
        return None

    if is_svg and not use_tight:
        from .._utils._crop import crop_svg

        avg_margin_mm = (ml + mr + mt + mb) / 4
        if crop_margin_mm is not None:
            avg_margin_mm = crop_margin_mm
        crop_svg(image_path, fig.fig, margin_mm=avg_margin_mm)

    return None


# EOF
