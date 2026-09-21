#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audio processing for demo videos.

Provides TTS generation and audio mixing for demo narration.
"""

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

import scitex_logging as slogging

console = slogging.getConsole(f"{__name__}.console")

# Check for ElevenLabs API key
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def _sanitize_filename(text: str, max_length: int = 50) -> str:
    """Convert text to a safe filename prefix.

    Parameters
    ----------
    text : str
        Text to convert.
    max_length : int
        Maximum length of the result.

    Returns
    -------
    str
        Sanitized filename-safe string.
    """
    # Remove special characters, keep alphanumeric and spaces
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Replace spaces with underscores
    clean = re.sub(r"\s+", "_", clean.strip())
    # Truncate and lowercase
    return clean[:max_length].lower().rstrip("_")


def _get_cache_path(text: str, cache_dir: Path) -> Path:
    """Get cache file path using transcription-based naming.

    Format: {sanitized_text}_{hash}.mp3
    Example: enable_dark_mode_demo_a1b2c3d4.mp3

    Parameters
    ----------
    text : str
        Text content for TTS.
    cache_dir : Path
        Cache directory.

    Returns
    -------
    Path
        Cache file path.
    """
    # Create short hash for uniqueness
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    # Sanitize text for filename
    sanitized = _sanitize_filename(text)
    # Combine: readable prefix + hash for uniqueness
    filename = f"{sanitized}_{text_hash}.mp3"
    return cache_dir / filename


def generate_tts_segments(
    narrations: List[Tuple[str, str]],
    output_dir: Path,
) -> List[Path]:
    """Generate TTS audio files for narrations.

    Uses ElevenLabs if API key is available, falls back to gTTS.
    Cache files are named using transcription text for easy identification.

    Parameters
    ----------
    narrations : List[Tuple[str, str]]
        List of (name, text) tuples.
    output_dir : Path
        Output directory for audio files.

    Returns
    -------
    List[Path]
        List of generated audio file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []

    if ELEVENLABS_API_KEY:
        console.info("Using ElevenLabs TTS (high quality)")
        try:
            from elevenlabs import ElevenLabs

            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

            for name, text in narrations:
                cache_path = _get_cache_path(text, output_dir)

                # Check cache
                if cache_path.exists():
                    console.info(f"  [cache] {cache_path.name}")
                    audio_files.append(cache_path)
                    continue

                # Generate TTS
                audio = client.text_to_speech.convert(
                    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
                    text=text,
                    model_id="eleven_monolingual_v1",
                )

                # Save audio
                with open(cache_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)

                console.info(f"  ✓ ElevenLabs: {cache_path.name} - '{text[:40]}...'")
                audio_files.append(cache_path)

            return audio_files

        except Exception as e:
            console.error(f"  ElevenLabs failed: {e}, falling back to gTTS")

    # Fallback to gTTS
    console.info("Using gTTS (fallback)")
    try:
        from gtts import gTTS

        for name, text in narrations:
            cache_path = _get_cache_path(text, output_dir)

            # Check cache
            if cache_path.exists():
                console.info(f"  [cache] {cache_path.name}")
                audio_files.append(cache_path)
                continue

            # Generate TTS
            tts = gTTS(text=text, lang="en")
            tts.save(str(cache_path))

            console.info(f"  ✓ gTTS: {cache_path.name} - '{text[:40]}...'")
            audio_files.append(cache_path)

        return audio_files

    except ImportError:
        raise RuntimeError("Neither ElevenLabs nor gTTS available")


def mix_narration_with_bgm(
    narration_files: List[Path],
    narration_times: List[float],
    bgm_path: Path,
    output_path: Path,
    duration: float,
    bgm_volume: float = 0.10,
    narration_delay: float = 0.3,
    fade_in_duration: float = 0.5,
    fade_out_duration: float = 1.0,
) -> Path:
    """Mix narration audio with background music.

    Parameters
    ----------
    narration_files : List[Path]
        List of narration audio files.
    narration_times : List[float]
        Start times for each narration.
    bgm_path : Path
        Path to background music file.
    output_path : Path
        Output path for mixed audio.
    duration : float
        Total duration in seconds.
    bgm_volume : float
        Background music volume (0.0-1.0).
    narration_delay : float
        Delay before narration starts.
    fade_in_duration : float
        BGM fade-in duration.
    fade_out_duration : float
        BGM fade-out duration.

    Returns
    -------
    Path
        Path to mixed audio file.
    """
    # Build ffmpeg filter for mixing
    inputs = ["-i", str(bgm_path)]
    for f in narration_files:
        inputs.extend(["-i", str(f)])

    # BGM filter: loop, trim, volume, fade
    bgm_filter = (
        f"[0:a]aloop=loop=-1:size=2e+09,atrim=0:{duration},"
        f"volume={bgm_volume},"
        f"afade=t=in:st=0:d={fade_in_duration},"
        f"afade=t=out:st={duration - fade_out_duration}:d={fade_out_duration}[bgm]"
    )

    # Narration filters with delays
    narration_filters = []
    mix_inputs = "[bgm]"

    for i, (f, t) in enumerate(zip(narration_files, narration_times)):
        delay_ms = int((t + narration_delay) * 1000)
        narration_filters.append(f"[{i + 1}:a]adelay={delay_ms}|{delay_ms}[n{i}]")
        mix_inputs += f"[n{i}]"

    # Combine all filters
    all_filters = [bgm_filter] + narration_filters
    mix_filter = (
        f"{mix_inputs}amix=inputs={len(narration_files) + 1}:duration=first[out]"
    )
    all_filters.append(mix_filter)

    filter_complex = ";".join(all_filters)

    # Run ffmpeg
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", filter_complex, "-map", "[out]", str(output_path)]
    )

    subprocess.run(cmd, check=True, capture_output=True)

    return output_path


__all__ = ["generate_tts_segments", "mix_narration_with_bgm"]
