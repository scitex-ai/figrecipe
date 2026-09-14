#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Editor service -- creation, caching.

Editors are cached in-process because route handlers mutate
the matplotlib figure directly (labels, legend, axes positions).
Uses a lightweight EditorState dataclass.
"""

import logging
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# In-process cache: session_key -> (editor, last_access_time)
_editor_cache: Dict[str, Tuple[Any, float]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class EditorState:
    """Lightweight editor state (replaces Flask FigureEditor)."""

    fig: Any = None
    recipe_path: Optional[Path] = None
    style: Optional[Dict[str, Any]] = None
    working_dir: Path = field(default_factory=Path.cwd)
    dark_mode: bool = False
    _color_map: Optional[Dict] = None
    _style_name: str = "SCITEX"
    _hitmap_generated: bool = False
    imported_table: Optional[Dict[str, Any]] = None

    # StyleOverrides for layered style management
    _overrides: Any = None

    # FilesBackend for file I/O abstraction (lazy-initialized)
    _files_backend: Any = None

    @property
    def files(self):
        """Get FilesBackend for file operations.

        Tries scitex-app's get_files() first (supports local + cloud),
        falls back to LocalFilesAdapter (pure pathlib, zero deps).
        """
        if self._files_backend is None:
            try:
                from scitex_app import get_files

                self._files_backend = get_files(root=str(self.working_dir))
            except ImportError:
                from ._local_files import LocalFilesAdapter

                self._files_backend = LocalFilesAdapter(self.working_dir)
        return self._files_backend

    @property
    def overrides(self):
        """Access the style overrides object."""
        if self._overrides is None:
            from figrecipe._editor._overrides import StyleOverrides

            self._overrides = StyleOverrides(self.style or {})
        return self._overrides

    @property
    def style_overrides(self):
        """Alias for overrides (used by style handlers)."""
        return self.overrides

    def get_effective_style(self) -> Dict[str, Any]:
        """Get the effective style with overrides."""
        if self._overrides is not None:
            return self._overrides.get_effective_style(dark_mode=self.dark_mode)
        return self.style or {}


def get_or_create_editor(
    session_key: str,
    recipe_path: str,
    style: Optional[str] = None,
) -> EditorState:
    """Get cached editor or create a new one."""
    _cleanup_expired()

    if session_key in _editor_cache:
        editor, _ = _editor_cache[session_key]
        _editor_cache[session_key] = (editor, time.time())
        return editor

    editor = _create_editor(recipe_path, style)
    _editor_cache[session_key] = (editor, time.time())
    return editor


def remove_editor(session_key: str) -> None:
    """Remove an editor from cache."""
    _editor_cache.pop(session_key, None)


def _create_editor(
    recipe_path: str,
    style: Optional[str] = None,
) -> EditorState:
    """Create an EditorState from recipe path."""
    from figrecipe._editor import _resolve_source, _resolve_style
    from figrecipe._editor._hitmap import generate_hitmap, hitmap_to_base64

    fig, resolved_path = _resolve_source(recipe_path)
    style_dict = _resolve_style(style)

    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    saved_facecolors = []
    for ax in mpl_fig.get_axes():
        saved_facecolors.append((ax, ax.get_facecolor()))
        ax.set_facecolor("none")
    static_png_path = Path(tempfile.mktemp(suffix="_figrecipe_static.png"))
    mpl_fig.savefig(static_png_path, format="png", dpi=150, transparent=True)
    for ax, fc in saved_facecolors:
        ax.set_facecolor(fc)

    hitmap_img, color_map = generate_hitmap(fig)
    hitmap_base64 = hitmap_to_base64(hitmap_img)

    editor = EditorState(
        fig=fig,
        recipe_path=resolved_path,
        style=style_dict,
        working_dir=Path(recipe_path).parent if recipe_path else Path.cwd(),
        _color_map=color_map,
        _hitmap_generated=True,
    )
    editor._hitmap_base64 = hitmap_base64
    logger.info("[FigRecipe] Created editor for %s", recipe_path)
    return editor


def _cleanup_expired() -> None:
    """Remove expired editors from cache."""
    now = time.time()
    expired = [
        k for k, (_, ts) in _editor_cache.items() if now - ts > _CACHE_TTL_SECONDS
    ]
    for k in expired:
        _editor_cache.pop(k, None)
