#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: figrecipe/_editable/_save.py

"""
Write the editable-figure JSON sidecar next to a saved image.
"""

import json
from pathlib import Path
from typing import Any, Union

from ._editable_export import export_editable_figure


def save_editable(
    fig,
    image_path: Union[str, Path],
    *,
    title: str = "",
    description: str = "",
    verbose: bool = True,
    **export_kwargs: Any,
) -> Path:
    """Export the editable-figure JSON and write it next to ``image_path``.

    The JSON is written to ``<stem>.json`` alongside the image (e.g.
    ``plot.png`` -> ``plot.json``).

    Parameters
    ----------
    fig : RecordingFigure or matplotlib.figure.Figure
        The figure to export.
    image_path : str or Path
        Path of the saved image; the JSON is written with the same stem.
    title, description : str
        Optional metadata embedded under ``meta``.
    verbose : bool
        If True, print the saved path.
    **export_kwargs
        Forwarded to :func:`export_editable_figure`
        (e.g. ``include_full_paths``, ``simplify_threshold``).

    Returns
    -------
    Path
        Path to the written JSON file.
    """
    data = export_editable_figure(
        fig, title=title, description=description, **export_kwargs
    )
    json_path = Path(image_path).with_suffix(".json")
    json_path.write_text(json.dumps(data, indent=2))
    if verbose:
        print(f"Saved editable: {json_path}")
    return json_path


# EOF
