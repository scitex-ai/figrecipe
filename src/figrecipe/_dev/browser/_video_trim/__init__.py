#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Video trimming with spatiotemporal marker detection.

Uses visual markers with OCR-readable text for reliable detection
of start/end points. Markers encode metadata that can be re-extracted.

Spatiotemporal Encoding:
- Temporal: Peak detection finds marker frames (dark frames)
- Spatial: Text at fixed positions, extracted via OCR
- Metadata: Version, timestamp embedded and recoverable

Usage:
    # In recorder - inject markers
    await inject_start_marker(page, version="0.8.0", timestamp="2025-12-27")
    # ... record content ...
    await inject_end_marker(page, version="0.8.0", timestamp="2025-12-27")

    # Post-processing - detect and trim
    output, metadata = process_video_with_markers(input_path, output_path)
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

import scitex_logging as slogging

from ._detection import detect_markers
from ._markers import (
    MARKER_END_ID,
    MARKER_START_ID,
    inject_end_marker,
    inject_start_marker,
)

console = slogging.getConsole(f"{__name__}.console")


def trim_video(
    input_path: Path,
    output_path: Path,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    codec: str = "libx264",
) -> bool:
    """Trim video based on timestamps.

    Parameters
    ----------
    input_path : Path
        Input video file.
    output_path : Path
        Output video file.
    start_time : float, optional
        Start time in seconds (trim before this).
    end_time : float, optional
        End time in seconds (trim after this).
    codec : str
        Video codec (default: libx264 for H.264).

    Returns
    -------
    bool
        True if successful.
    """
    cmd = ["ffmpeg", "-y"]

    if start_time is not None:
        cmd.extend(["-ss", str(start_time)])

    cmd.extend(["-i", str(input_path)])

    if end_time is not None and start_time is not None:
        duration = end_time - start_time
        if duration > 0:
            cmd.extend(["-t", str(duration)])
    elif end_time is not None:
        cmd.extend(["-t", str(end_time)])

    cmd.extend(["-c:v", codec, "-preset", "fast", "-crf", "23", str(output_path)])

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def process_video_with_markers(
    input_path: Path,
    output_path: Path,
    cleanup: bool = True,
    verbose: bool = True,
) -> Tuple[Path, Dict]:
    """Full pipeline: detect markers, extract metadata, trim video.

    Parameters
    ----------
    input_path : Path
        Raw recorded video (with markers).
    output_path : Path
        Trimmed output video.
    cleanup : bool
        Remove input file after success.
    verbose : bool
        Print debug information.

    Returns
    -------
    Tuple[Path, Dict]
        (output_path, extracted_metadata)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Detect markers and extract metadata
    start_time, end_time, metadata = detect_markers(input_path)

    if verbose:
        console.info(f"  Marker detection: start={start_time}, end={end_time}")

    if start_time is None:
        console.warning("Warning: No start marker detected, using beginning")
        start_time = 0

    if end_time is None:
        console.warning("Warning: No end marker detected, using end of video")

    # Trim video
    success = trim_video(input_path, output_path, start_time, end_time)

    if not success:
        raise RuntimeError(f"Failed to trim video: {input_path}")

    if cleanup and input_path != output_path and input_path.exists():
        input_path.unlink()

    return output_path, metadata


# Aliases for backward compatibility
trim_video_by_markers = trim_video

__all__ = [
    "inject_start_marker",
    "inject_end_marker",
    "detect_markers",
    "trim_video",
    "trim_video_by_markers",
    "process_video_with_markers",
    "MARKER_START_ID",
    "MARKER_END_ID",
]

# EOF
