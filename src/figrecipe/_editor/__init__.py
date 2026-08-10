#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe GUI Editor - Django+React based interactive figure editor.

This module provides the public gui() function and utility functions
needed by Django handlers.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union


def _check_figure_has_content(fig) -> bool:
    """Check if figure has any plot content."""
    for ax in fig.get_axes():
        if ax.lines or ax.patches or ax.images or ax.collections or ax.texts:
            return True
    return False


def _resolve_source(source):
    """Resolve source to figure and optional recipe path.

    Parameters
    ----------
    source : RecordingFigure, str, Path, or None

    Returns
    -------
    tuple
        (RecordingFigure, Path or None)
    """
    from .._wrappers import RecordingFigure

    if source is None:
        from .. import subplots

        fig, ax = subplots()
        ax.set_title("New Figure")
        return fig, None

    if isinstance(source, RecordingFigure):
        return source, None

    from matplotlib.figure import Figure

    if isinstance(source, Figure):
        from .._recorder import FigureRecord, Recorder
        from .._wrappers._figure import RecordingFigure as RF

        wrapped_fig = RF.__new__(RF)
        wrapped_fig._fig = source
        wrapped_fig._axes = [[ax] for ax in source.axes]
        wrapped_fig._recorder = Recorder()
        wrapped_fig._recorder._figure_record = FigureRecord(
            figsize=tuple(source.get_size_inches()),
            dpi=int(source.dpi),
        )
        return wrapped_fig, None

    from .._utils._bundle import resolve_recipe_path

    path, _temp_dir = resolve_recipe_path(source)

    from .._reproducer import reproduce

    fig, axes = reproduce(path)

    if not isinstance(fig, RecordingFigure):
        from .._recorder import FigureRecord
        from .._wrappers._figure import RecordingFigure as RF

        wrapped_fig = RF.__new__(RF)
        wrapped_fig.fig = fig
        wrapped_fig._axes = axes if isinstance(axes, list) else [axes]
        wrapped_fig.record = FigureRecord(
            figsize=fig.get_size_inches().tolist(),
            dpi=fig.dpi,
        )
        fig = wrapped_fig

    return fig, path


def _resolve_style(style):
    """Resolve style to dictionary."""
    if style is None:
        from ..styles._style_loader import _STYLE_CACHE

        if _STYLE_CACHE is not None:
            from ..styles._internal import to_subplots_kwargs

            return to_subplots_kwargs(_STYLE_CACHE)
        return None

    if isinstance(style, dict):
        return style

    if isinstance(style, str):
        from ..styles import load_style
        from ..styles._internal import to_subplots_kwargs

        loaded = load_style(style)
        return to_subplots_kwargs(loaded) if loaded else None

    raise TypeError(f"style must be str, dict, or None, got {type(style)}")


def gui(
    source: Optional[Union[str, Path]] = None,
    style: Optional[Union[str, Dict[str, Any]]] = None,
    port: int = 31296,
    host: str = "127.0.0.1",
    open_browser: bool = True,
    hot_reload: bool = False,
    working_dir: Optional[Union[str, Path]] = None,
    desktop: bool = False,
) -> None:
    """Launch interactive GUI editor using Django + React.

    Parameters
    ----------
    source : str, Path, or None
        Path to recipe file, bundle, or directory. None for blank figure.
    style : str or dict, optional
        Style preset name or dict.
    port : int
        Server port (default: 31296 — figrecipe's reserved port in the
        scitex-dev 3129X per-package GUI scheme; see
        scitex-todo card figrecipe-gui-cli-noun-verb-normalize-20260712).
    host : str
        Host to bind (default: "127.0.0.1").
    open_browser : bool
        Whether to open browser automatically (default: True).
    hot_reload : bool
        Enable hot reload (default: False).
    working_dir : str or Path, optional
        Working directory for file browser.
    desktop : bool
        Launch as native desktop window (default: False).
    """
    import os

    # Resolve working directory
    if working_dir:
        wd = str(Path(working_dir).resolve())
    elif source:
        src_path = Path(source)
        wd = str(src_path.resolve() if src_path.is_dir() else src_path.parent.resolve())
    else:
        wd = str(Path.cwd())

    os.environ["FIGRECIPE_WORKING_DIR"] = wd

    # Extra env for recipe source
    extra_env = {}
    if source:
        extra_env["FIGRECIPE_INITIAL_RECIPE"] = str(Path(source))

    # Start terminal WebSocket server on port+1 (before Django setup)
    def _start_terminal():
        try:
            from figrecipe._django.terminal import start_terminal_server

            start_terminal_server(port + 1)
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning("Terminal server failed: %s", e)

    import threading

    threading.Thread(target=_start_terminal, daemon=True).start()

    # Use shared standalone launcher from scitex-app
    try:
        from scitex_app._standalone import run_standalone

        # Pre-configure Django with figrecipe's settings (includes DB + chat app)
        # before run_standalone, so _standalone.py skips its own bare config.
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
        if wd:
            os.environ.setdefault("FIGRECIPE_WORKING_DIR", wd)

        import django

        django.setup()

        from django.core.management import call_command

        call_command("migrate", "--run-syncdb", verbosity=0)

        run_standalone(
            app_module="figrecipe._django",
            port=port,
            host=host,
            open_browser=open_browser,
            hot_reload=hot_reload,
            working_dir=wd,
            desktop=desktop,
            extra_env=extra_env,
        )
    except ImportError:
        # Fallback: use figrecipe's own Django settings if scitex-app not installed
        import webbrowser

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")

        import django

        django.setup()

        url = f"http://{host}:{port}/"
        if open_browser:
            threading.Timer(1.5, webbrowser.open, args=[url]).start()

        from django.core.management import call_command

        # Auto-migrate database (creates tables for chat sessions on first run)
        call_command("migrate", "--run-syncdb", verbosity=0)

        noreload = [] if hot_reload else ["--noreload"]
        call_command("runserver", f"{host}:{port}", *noreload)


__all__ = [
    "gui",
    "_resolve_source",
    "_resolve_style",
    "_check_figure_has_content",
]
