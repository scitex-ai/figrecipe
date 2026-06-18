#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions for save operations (extracted for modularity)."""

from pathlib import Path
from typing import Optional

from .._utils._grid import grid_id

# stx_* plotters that build their own make_axes_locatable marginals at draw
# time and re-build them on replay. Their recorded axes is the POST-divide
# (shrunken) main axes, so for crop-aware compose we record its PRE-divide
# extent (union with the marginals) -- see _capture_content_layout.
_DIVIDER_PLOTTERS = {"stx_scatter_hist"}


def _is_standalone_diagram_figure(fig) -> bool:
    """True for a single-axes figure whose content is a figrecipe Diagram.

    Two code paths produce such a figure and BOTH must be recognised so the save
    and the reproduce crop to the same recorded ``content_bbox`` (otherwise only
    one side would, defeating the fix):

    * Live render / the validator's re-save of the ORIGINAL: ``Diagram.render``
      tags the owned figure with ``_figrecipe_diagram`` (set only when it owns
      the figure -- composed multi-panel diagrams never set it).
    * The validator's re-save of the REPRODUCED figure: replay goes through
      ``replay_diagram_native_call`` (NOT ``ax.diagram``), so the live marker is
      absent; instead detect a single-axes figure whose sole recorded axes
      carries a ``function=="diagram"`` call.

    The single-axes guard keeps composed figures (which embed diagrams in a grid)
    on the normal content-aware crop path -- only the standalone case is
    size-sensitive to the content-aware crop's per-render ink drift.
    """
    if getattr(fig.fig, "_figrecipe_diagram", None) is not None:
        return True

    if len(fig.fig.get_axes()) != 1:
        return False

    axes_records = getattr(fig.record, "axes", {})
    if len(axes_records) != 1:
        return False
    only_axes = next(iter(axes_records.values()))
    return any(c.function == "diagram" for c in only_axes.calls)


def crop_to_content_bbox(
    image_path: Path,
    content_bbox,
    margins_mm,
    dpi: int,
) -> Optional[dict]:
    """Crop a saved raster to a RECORDED tight-ink bbox (dpi-independent).

    Diagram figures render with a hair of different text ink between the
    original save and the recipe-reproduced save, so a pixel-content-aware
    crop (``_utils._crop.crop``) lands on slightly different boxes -> the two
    cropped PNGs differ in height and reproducibility validation reports a SIZE
    mismatch (NeuroVista Fig 02 panel b). Instead, crop both to the SAME bbox
    captured once at save time (``FigureRecord.content_bbox``), so the original
    save and every reproduce crop to identical pixel dimensions.

    ``content_bbox`` is ``[l, b, w, h]`` in the *uncropped* figure fraction
    (matplotlib coords, y=0 at the bottom). It is a FRACTION, so it is applied
    to the actual saved-image pixel dimensions and therefore stays correct at
    any dpi (the validator re-saves at dpi=150 while the user's real save may be
    dpi=300). Margins (``crop_margin_{left,right,top,bottom}_mm``) are added in
    pixels at ``dpi`` to match the normal crop path.

    Returns the same ``crop_offset`` dict shape as ``_utils._crop.crop`` (so
    ``_capture_axes_bboxes`` keeps working), or ``None`` on failure (the caller
    then falls back to the content-aware crop with a warning).
    """
    from PIL import Image

    from .._utils._crop import crop, mm_to_pixels

    try:
        l, b, w, h = (float(v) for v in content_bbox)
    except (TypeError, ValueError):
        return None

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    # content_bbox is matplotlib y-up; PIL crop box is y-down (origin top-left).
    # top edge in mpl fraction = b + h ; bottom edge = b.
    left_px = round(l * img_w) - mm_to_pixels(margins_mm["left"], dpi)
    right_px = round((l + w) * img_w) + mm_to_pixels(margins_mm["right"], dpi)
    upper_px = round((1.0 - (b + h)) * img_h) - mm_to_pixels(margins_mm["top"], dpi)
    lower_px = round((1.0 - b) * img_h) + mm_to_pixels(margins_mm["bottom"], dpi)

    if right_px - left_px <= 0 or lower_px - upper_px <= 0:
        return None

    # Reuse crop()'s explicit-box path: it preserves DPI/PNG-text metadata and
    # extends the canvas with the detected background when the box exceeds the
    # image edge (content can overflow the canvas, so this is expected).
    _, crop_offset = crop(
        image_path,
        output_path=image_path,
        crop_box=(left_px, upper_px, right_px, lower_px),
        return_offset=True,
    )
    return crop_offset


def _crop_to_recorded_content_bbox(
    fig,
    image_path: Path,
    crop_margin_mm: Optional[float],
    crop_margins_mm,
    dpi: int,
) -> Optional[dict]:
    """Crop a raster to its recorded ``content_bbox`` (deterministic size).

    Generalises the standalone-diagram crop (#215) to ANY croppable raster whose
    saved SIZE is otherwise re-measured at save time -- constrained_layout figures
    (which would crop via ``bbox_inches="tight"``) and composed/mm-layout figures
    (which would crop content-aware). Both re-measures jitter sub-pixel between the
    original (drawn many times) and a fresh ``reproduce()`` (drawn few), so at a
    pixel-rounding boundary the saved width can flip by ~1px and the validator's
    ``size_tolerance`` flips to a SIZE mismatch (colorbar/pie/CL/composed).

    Ensures ``fig.record.content_bbox`` exists BEFORE cropping: on the user's
    first real save it is still None, so it is computed here from the (uncropped)
    figure; on the validator's re-save of the original it is already set from the
    first save; and on a recipe-reproduced figure it is loaded from disk. All
    three therefore crop to the SAME dpi-independent fraction, so the saved file
    and every reproduce land at identical pixel dimensions.

    ``crop_margin_mm`` (explicit uniform override) wins over ``crop_margins_mm``
    (the per-side mm_layout margins, ``(left, right, top, bottom)``).

    Returns a ``crop_offset`` dict, or ``None`` (with a warning) when no
    ``content_bbox`` is available -- the caller then falls back to the normal
    ``bbox_inches="tight"`` / content-aware crop so a missing bbox never silently
    skips cropping (project rule: no silent fallback).
    """
    if getattr(fig.record, "content_bbox", None) is None:
        _capture_content_layout(fig)

    content_bbox = getattr(fig.record, "content_bbox", None)
    if content_bbox is None:
        import warnings

        warnings.warn(
            "Figure has no content_bbox; falling back to the legacy "
            "tight/content-aware crop (this figure may reproduce at a "
            "different pixel size under draw-count jitter).",
            UserWarning,
        )
        return None

    ml, mr, mt, mb = crop_margins_mm
    if crop_margin_mm is not None:
        ml = mr = mt = mb = crop_margin_mm
    margins = {"left": ml, "right": mr, "top": mt, "bottom": mb}

    return crop_to_content_bbox(image_path, content_bbox, margins, dpi)


def _crop_to_axes_size(
    fig,
    image_path: Path,
    mm_layout: dict,
    dpi: int,
) -> Optional[dict]:
    """Crop image based on tight bounding box of figure content.

    Used for constrained_layout figures where content-based cropping doesn't work
    because matplotlib fills the canvas. Uses matplotlib's get_tightbbox() to find
    the actual content bounds including labels, titles, and legends.

    Parameters
    ----------
    fig : RecordingFigure
        The figure (needed to get tight bounding box)
    image_path : Path
        Path to the saved image
    mm_layout : dict
        Layout configuration with crop margins
    dpi : int
        Image DPI

    Returns
    -------
    dict or None
        Crop offset dictionary if cropping was performed, None otherwise
    """
    from PIL import Image

    from .._utils._crop import mm_to_pixels

    # Get crop margins from mm_layout
    margin_left_mm = mm_layout.get("crop_margin_left_mm", 1)
    margin_right_mm = mm_layout.get("crop_margin_right_mm", 1)
    margin_top_mm = mm_layout.get("crop_margin_top_mm", 1)
    margin_bottom_mm = mm_layout.get("crop_margin_bottom_mm", 1)

    # Get tight bounding box of figure content (includes labels, titles, legends)
    # Need to draw the figure first to get accurate bbox
    fig.fig.canvas.draw()
    renderer = fig.fig.canvas.get_renderer()
    tight_bbox = fig.fig.get_tightbbox(renderer)

    if tight_bbox is None:
        return None

    # Open image to get dimensions
    img = Image.open(image_path)
    orig_w, orig_h = img.size

    # tight_bbox is in inches, convert to pixels
    fig_dpi = fig.fig.dpi
    content_left_px = int(tight_bbox.x0 * fig_dpi)
    content_right_px = int(tight_bbox.x1 * fig_dpi)
    # Flip y coordinate: tight_bbox y=0 is bottom, image y=0 is top
    content_top_px = int(orig_h - tight_bbox.y1 * fig_dpi)
    content_bottom_px = int(orig_h - tight_bbox.y0 * fig_dpi)

    # Calculate margins in pixels
    margin_left_px = mm_to_pixels(margin_left_mm, dpi)
    margin_right_px = mm_to_pixels(margin_right_mm, dpi)
    margin_top_px = mm_to_pixels(margin_top_mm, dpi)
    margin_bottom_px = mm_to_pixels(margin_bottom_mm, dpi)

    # Calculate crop bounds with margins around content
    crop_left = content_left_px - margin_left_px
    crop_top = content_top_px - margin_top_px
    crop_right = content_right_px + margin_right_px
    crop_bottom = content_bottom_px + margin_bottom_px

    # Clamp to image boundaries
    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    crop_right = min(orig_w, crop_right)
    crop_bottom = min(orig_h, crop_bottom)

    # Crop the image
    cropped_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

    # Preserve DPI metadata
    save_kwargs = {}
    if "dpi" in img.info:
        save_kwargs["dpi"] = img.info["dpi"]

    ext = image_path.suffix.lower()
    if ext == ".png":
        save_kwargs["compress_level"] = 0
        save_kwargs["optimize"] = False

    cropped_img.save(image_path, **save_kwargs)

    return {
        "left": crop_left,
        "upper": crop_top,
        "right": crop_right,
        "lower": crop_bottom,
        "original_width": orig_w,
        "original_height": orig_h,
        "new_width": cropped_img.width,
        "new_height": cropped_img.height,
    }


def _capture_axes_bboxes(fig, crop_offset: Optional[dict] = None) -> None:
    """Capture bounding boxes of all axes for alignment/snap functionality.

    Stores bbox as [left, bottom, width, height] in figure coordinates (0-1).
    If crop_offset is provided, adjusts bbox to post-crop coordinate system.

    Parameters
    ----------
    fig : RecordingFigure
        The figure with record to update.
    crop_offset : dict, optional
        Crop information from crop() with return_offset=True.
        Contains: left, upper, right, lower, original_width, original_height,
        new_width, new_height (all in pixels).
    """

    def _to_cropped(bbox) -> list:
        """Convert an mpl axes position to (cropped) figure-fraction bbox."""
        bbox_list = [bbox.x0, bbox.y0, bbox.width, bbox.height]
        if crop_offset is None:
            return bbox_list
        # Convert from figure coords to pixel coords, then to cropped coords
        orig_w = crop_offset["original_width"]
        orig_h = crop_offset["original_height"]
        new_w = crop_offset["new_width"]
        new_h = crop_offset["new_height"]
        crop_left = crop_offset["left"]
        crop_upper = crop_offset["upper"]

        # Original pixel positions (matplotlib y=0 is bottom, image y=0 is top)
        x0_px = bbox.x0 * orig_w
        y0_px = (1 - bbox.y0 - bbox.height) * orig_h  # Convert to image coords
        w_px = bbox.width * orig_w
        h_px = bbox.height * orig_h

        # Adjust for crop (translate origin)
        x0_cropped = x0_px - crop_left
        y0_cropped = y0_px - crop_upper

        # Convert back to figure coordinates (0-1 range in cropped image)
        new_x0 = x0_cropped / new_w
        new_y0 = 1 - (y0_cropped + h_px) / new_h  # Back to matplotlib coords
        new_w_frac = w_px / new_w
        new_h_frac = h_px / new_h
        return [new_x0, new_y0, new_w_frac, new_h_frac]

    # Map each AxesRecord to ITS OWN mpl axes via the wrapped RecordingAxes
    # (which carry both ``_position`` and the underlying ``_ax``). The previous
    # implementation looped over fig.get_axes() and matched by position, but
    # every mpl axes matched the first record whose key-derived position equalled
    # its own — so for a multi-subplot figure all subplots overwrote r0c0's bbox,
    # and r1c0/r2c0 ended up with no bbox at all. Marginal axes created via
    # make_axes_locatable are not wrapped, so they are correctly skipped here.
    matched_records = set()
    for row in fig.axes:
        for rec_ax in row:
            mpl_ax = getattr(rec_ax, "_ax", rec_ax)
            position = getattr(rec_ax, "_position", None)
            if position is None:
                continue
            key = grid_id(position[0], position[1])
            ax_record = fig.record.axes.get(key)
            if ax_record is None:
                continue
            ax_record.bbox = _to_cropped(mpl_ax.get_position())
            # Capture the FINAL rendered view limits (post-render, after every
            # call/decoration/tick-finalizer has run on the live axes) so the
            # reproducer can re-apply the TRUE final view rather than the
            # set_xlim/set_ylim args -- those args miss a legitimate later
            # widening such as rotate_labels snapping the view to the outermost
            # tick (NeuroVista Fig 01c). float() strips np.float64 for clean YAML.
            try:
                xlo, xhi = mpl_ax.get_xlim()
                ylo, yhi = mpl_ax.get_ylim()
                ax_record.final_xlim = (float(xlo), float(xhi))
                ax_record.final_ylim = (float(ylo), float(yhi))
            except Exception:
                pass  # best-effort; reproducer falls back to set_*lim args
            matched_records.add(key)

    # Fallback for mm-based composition records (keyed "ax_mm_idx"), which are
    # not represented in fig.axes positions. Match in order against any
    # remaining mpl axes.
    remaining = [k for k in fig.record.axes if k not in matched_records]
    if remaining:
        mpl_axes = list(fig.fig.get_axes())
        for key, mpl_ax in zip(remaining, mpl_axes):
            if key.startswith("ax_mm_"):
                fig.record.axes[key].bbox = _to_cropped(mpl_ax.get_position())


def _capture_content_layout(fig) -> None:
    """Record the tight content layout for crop-aware composition.

    Captures, into ``fig.record``:
      * ``content_bbox``  -- the figure's tight ink bbox [l, b, w, h] in the
        *uncropped* figure fraction (from ``get_tightbbox``); includes axis
        labels, ticks, titles, legends and make_axes_locatable marginals, and
        may exceed [0, 1] when content overflows the canvas.
      * ``content_size_mm`` -- that bbox's [w, h] in millimetres.
      * per-axes ``bbox_uncropped`` -- each axes' ``get_position()`` in the
        uncropped fraction.

    All values are dpi-independent fractions/mm, so a composer can size and
    place each panel by its true (cropped) extent and reproduce the clean
    standalone render pixel-for-pixel. Best-effort: failures leave the fields
    unset and the composer falls back to the legacy ``bbox`` path.
    """
    mpl_fig = fig.fig
    try:
        mpl_fig.canvas.draw()
        renderer = mpl_fig.canvas.get_renderer()
        tight = mpl_fig.get_tightbbox(renderer)
    except Exception:
        tight = None

    # Everything below is best-effort: any failure leaves the fields unset and
    # the composer falls back to the legacy bbox path -- never crash a save.
    try:
        fw_in, fh_in = (float(v) for v in mpl_fig.get_size_inches())
        if tight is not None and fw_in > 0 and fh_in > 0:
            cb = [
                tight.x0 / fw_in,
                tight.y0 / fh_in,
                tight.width / fw_in,
                tight.height / fh_in,
            ]
            fig.record.content_bbox = cb
            fig.record.content_size_mm = [cb[2] * fw_in * 25.4, cb[3] * fh_in * 25.4]

        recorded_ids = set()
        divider_axes = []  # (ax_record, center_x, center_y) for re-splitting plots
        for row in fig.axes:
            for rec_ax in row:
                mpl_ax = getattr(rec_ax, "_ax", rec_ax)
                position = getattr(rec_ax, "_position", None)
                if position is None:
                    continue
                ax_record = fig.record.axes.get(grid_id(position[0], position[1]))
                if ax_record is None:
                    continue
                pos = mpl_ax.get_position()
                ax_record.bbox_uncropped = [pos.x0, pos.y0, pos.width, pos.height]
                recorded_ids.add(id(mpl_ax))
                if any(c.function in _DIVIDER_PLOTTERS for c in ax_record.calls):
                    divider_axes.append(
                        (ax_record, pos.x0 + pos.width / 2, pos.y0 + pos.height / 2)
                    )

        # make_axes_locatable marginals are NOT recorded as RecordingAxes, so a
        # divider plotter's axes is captured at its POST-divide (shrunken) size.
        # The plotter re-splits on replay, so place it at the PRE-divide extent:
        # union each divider axes with its nearest un-recorded marginal axes.
        for m in mpl_fig.get_axes() if divider_axes else []:
            if id(m) in recorded_ids:
                continue
            mp = m.get_position()
            mcx, mcy = mp.x0 + mp.width / 2, mp.y0 + mp.height / 2
            rec = min(
                divider_axes, key=lambda d: (d[1] - mcx) ** 2 + (d[2] - mcy) ** 2
            )[0]
            bx0, by0, bw, bh = rec.bbox_uncropped
            nx0, ny0 = min(bx0, mp.x0), min(by0, mp.y0)
            nx1 = max(bx0 + bw, mp.x0 + mp.width)
            ny1 = max(by0 + bh, mp.y0 + mp.height)
            rec.bbox_uncropped = [nx0, ny0, nx1 - nx0, ny1 - ny0]
    except Exception:
        pass


def save_hitmap(
    fig,
    image_path: Path,
    dpi: int,
    verbose: bool,
    bbox_inches: Optional[str] = None,
    pad_inches: float = 0.0,
) -> Optional[Path]:
    """Save hitmap image for GUI editor element selection.

    Parameters
    ----------
    bbox_inches : str, optional
        If "tight", hitmap is rendered with bbox_inches="tight" to match
        figures saved with constrained_layout (e.g. pie, imshow).
    pad_inches : float
        Padding in inches when bbox_inches="tight".

    Returns
    -------
    Path or None
    """
    try:
        hitmap_path = image_path.with_stem(image_path.stem + "_hitmap")
        mpl_fig = fig.fig if hasattr(fig, "fig") else fig
        diagram = getattr(mpl_fig, "_figrecipe_diagram", None)

        if diagram is not None:
            from .._diagram._diagram._hitmap import save_diagram_hitmap

            save_diagram_hitmap(diagram, hitmap_path, dpi=min(dpi, 150))
        else:
            from .._editor._hitmap import generate_hitmap

            hitmap_img, _ = generate_hitmap(
                fig,
                dpi=min(dpi, 150),
                bbox_inches=bbox_inches,
                pad_inches=pad_inches,
            )
            hitmap_img.save(hitmap_path)

        if verbose:
            print(f"  Hitmap: {hitmap_path}")
        return hitmap_path
    except Exception as e:
        if verbose:
            print(f"  Hitmap generation failed: {e}")
        return None
