#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Narration processing for demo videos.

Provides utilities to extract captions from demo scripts,
estimate timing, and add TTS narration with BGM.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import scitex_logging as slogging

from ._audio import generate_tts_segments, mix_narration_with_bgm

console = slogging.getConsole(f"{__name__}.console")


def extract_captions_from_script(script_path: Path) -> List[str]:
    """Extract caption texts from a demo script.

    Parameters
    ----------
    script_path : Path
        Path to demo Python script.

    Returns
    -------
    List[str]
        List of caption texts in order.
    """
    content = script_path.read_text()
    pattern = r'await\s+self\.caption\s*\(\s*["\']([^"\']+)["\']'
    return re.findall(pattern, content)


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds.

    Parameters
    ----------
    video_path : Path
        Path to video file.

    Returns
    -------
    float
        Duration in seconds.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def estimate_caption_times(
    captions: List[str],
    video_duration: float,
    title_duration: float = 2.5,
    closing_duration: float = 2.5,
) -> List[float]:
    """Estimate caption start times based on video duration.

    Assumes captions are evenly distributed in the content portion
    (between title and closing screens).

    Parameters
    ----------
    captions : List[str]
        List of caption texts.
    video_duration : float
        Total video duration.
    title_duration : float
        Title screen duration at start.
    closing_duration : float
        Closing screen duration at end.

    Returns
    -------
    List[float]
        Estimated start times for each caption.
    """
    content_duration = video_duration - title_duration - closing_duration
    if len(captions) == 0:
        return []
    if len(captions) == 1:
        return [title_duration + content_duration / 2]
    interval = content_duration / (len(captions) + 1)
    return [title_duration + interval * (i + 1) for i in range(len(captions))]


def add_narration_to_video(
    video_path: Path,
    captions: List[str],
    output_path: Path,
    bgm_path: Path,
    tts_cache_dir: Path,
    title_text: str = "",
    bgm_volume: float = 0.08,
    narration_delay: float = 0.2,
    fade_in_duration: float = 0.5,
    fade_out_duration: float = 2.0,
    verbose: bool = True,
) -> Tuple[bool, Dict]:
    """Add TTS narration and BGM to a video.

    Parameters
    ----------
    video_path : Path
        Input video file.
    captions : List[str]
        List of caption texts.
    output_path : Path
        Output video file path.
    bgm_path : Path
        Path to BGM audio file.
    tts_cache_dir : Path
        Directory for TTS cache.
    title_text : str, optional
        Title narration text (spoken at start).
    bgm_volume : float, optional
        BGM volume level (0.0-1.0).
    narration_delay : float, optional
        Delay before each narration.
    fade_in_duration : float, optional
        BGM fade-in duration.
    fade_out_duration : float, optional
        BGM fade-out duration.
    verbose : bool, optional
        Print progress messages.

    Returns
    -------
    Tuple[bool, Dict]
        (success, info_dict)
    """
    try:
        duration = get_video_duration(video_path)
        if verbose:
            console.info(f"  Video duration: {duration:.2f}s")

        # Build narrations list
        narrations = []
        if title_text:
            narrations.append(("title", title_text))
        for i, caption in enumerate(captions):
            narrations.append((f"caption_{i}", caption))

        if verbose:
            console.info(f"  {len(narrations)} narration segments")

        # Estimate timing
        caption_times = estimate_caption_times(captions, duration)
        narration_times = [1.0] + caption_times if title_text else caption_times

        # Generate TTS
        tts_cache_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            console.info("  Generating TTS...")
        narration_files = generate_tts_segments(narrations, tts_cache_dir)

        # Mix audio
        mixed_audio = Path(f"/tmp/narration_mixed_{video_path.stem}.mp3")
        if verbose:
            console.info("  Mixing audio...")
        mix_narration_with_bgm(
            narration_files=narration_files,
            narration_times=narration_times,
            bgm_path=bgm_path,
            output_path=mixed_audio,
            duration=duration,
            bgm_volume=bgm_volume,
            narration_delay=narration_delay,
            fade_in_duration=fade_in_duration,
            fade_out_duration=fade_out_duration,
        )

        # Create final video
        if verbose:
            console.info(f"  Creating: {output_path.name}")

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(mixed_audio),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        # Cleanup
        mixed_audio.unlink(missing_ok=True)

        if result.returncode != 0:
            return False, {"error": result.stderr[:200]}

        return True, {
            "duration": duration,
            "captions": len(captions),
            "output": str(output_path),
        }

    except Exception as e:
        import traceback

        return False, {"error": str(e), "traceback": traceback.format_exc()}


__all__ = [
    "extract_captions_from_script",
    "get_video_duration",
    "estimate_caption_times",
    "add_narration_to_video",
]

# EOF
