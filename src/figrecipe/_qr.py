#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QR-code overlay for figure-level metadata visualization.

Adds a minimal QR code to a matplotlib figure encoding arbitrary
metadata (typically a URL + provenance dict). Used for embedding
reproducibility / source links directly on a publication-ready figure.

Migrated from ``scitex.io._qr_utils`` (2026-05-29) per SoC: QR
annotation is figure-domain, not I/O-domain.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def add_qr_to_figure(fig, metadata, position="bottom-right", size=0.08):
    """Add a minimal QR code to a matplotlib figure.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Target figure to overlay onto.
    metadata : dict
        Payload to encode. If ``"url"`` is absent, ``"https://scitex.ai"``
        is added so the QR resolves to something even when consumers
        don't provide one.
    position : str
        One of ``"bottom-right"``, ``"bottom-left"``, ``"top-right"``,
        ``"top-left"``. Unknown values fall back to ``"bottom-right"``.
    size : float
        Relative size of the QR overlay (fraction of figure width).

    Returns
    -------
    matplotlib.figure.Figure
        The same figure, with a QR overlay axes added. If the optional
        ``qrcode`` / ``Pillow`` dependencies are not installed, the
        figure is returned unmodified and a warning is logged.
    """
    try:
        import qrcode
    except ImportError:
        logger.warning(
            "qrcode library not available. Install with: pip install qrcode[pil]"
        )
        return fig

    if "url" not in metadata:
        metadata = dict(metadata)
        metadata["url"] = "https://scitex.ai"

    metadata_json = json.dumps(metadata, ensure_ascii=False)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,
        border=1,
    )
    qr.add_data(metadata_json)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    positions = {
        "bottom-right": (0.92, 0.02),
        "bottom-left": (0.02, 0.02),
        "top-right": (0.92, 0.88),
        "top-left": (0.02, 0.88),
    }
    if position not in positions:
        position = "bottom-right"
    x, y = positions[position]

    ax_qr = fig.add_axes(
        [x, y, size, size * (fig.get_figheight() / fig.get_figwidth())]
    )
    ax_qr.imshow(qr_img, cmap="gray")
    ax_qr.axis("off")

    return fig


__all__ = ["add_qr_to_figure"]
