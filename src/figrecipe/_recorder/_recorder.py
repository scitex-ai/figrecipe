#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Recorder engine: turns matplotlib calls into a FigureRecord.

Extracted from ``_core.py`` (which had grown past the module line limit) so the
record dataclasses (``CallRecord`` / ``AxesRecord`` / ``FigureRecord``) and the
recorder engine live in focused files. ``_recorder/__init__`` re-exports
``Recorder`` so imports are unchanged.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ._core import CallRecord, FigureRecord


class Recorder:
    """Central recorder for tracking matplotlib calls."""

    from .._params import DECORATION_METHODS, PLOTTING_METHODS

    def __init__(self):
        self._figure_record: Optional[FigureRecord] = None
        self._method_counters: Dict[str, int] = {}

    def start_figure(
        self,
        figsize: Tuple[float, float] = (6.4, 4.8),
        dpi: int = 300,
        nrows: Optional[int] = None,
        ncols: Optional[int] = None,
    ) -> FigureRecord:
        """Start recording a new figure.

        ``nrows`` / ``ncols`` are optional but recommended — the data-file
        and separate-legend filename builders use them to compute the panel
        letter so filenames match the rendered panel labels (A, B, …).
        """
        self._figure_record = FigureRecord(
            figsize=figsize, dpi=dpi, nrows=nrows, ncols=ncols
        )
        self._method_counters = {}
        return self._figure_record

    @property
    def figure_record(self) -> Optional[FigureRecord]:
        """Get current figure record."""
        return self._figure_record

    def _generate_call_id(self, method_name: str) -> str:
        """Generate unique call ID."""
        counter = self._method_counters.get(method_name, 0)
        self._method_counters[method_name] = counter + 1
        return f"{method_name}_{counter:03d}"

    def record_call(
        self,
        ax_position: Tuple[int, int],
        method_name: str,
        args: tuple,
        kwargs: Dict[str, Any],
        call_id: Optional[str] = None,
    ) -> CallRecord:
        """Record a plotting call.

        Parameters
        ----------
        ax_position : tuple
            (row, col) position of axes.
        method_name : str
            Name of the method called.
        args : tuple
            Positional arguments.
        kwargs : dict
            Keyword arguments.
        call_id : str, optional
            Custom ID for this call.

        Returns
        -------
        CallRecord
            The recorded call.
        """
        if self._figure_record is None:
            self.start_figure()

        # Generate ID if not provided
        if call_id is None:
            call_id = self._generate_call_id(method_name)

        # Extract stats from kwargs before processing (stats is metadata, not matplotlib arg)
        call_stats = kwargs.pop("stats", None) if "stats" in kwargs else None

        # Process args into serializable format
        processed_args = self._process_args(args, method_name)

        # Filter kwargs to non-default only (if signature available)
        processed_kwargs = self._process_kwargs(kwargs, method_name)

        record = CallRecord(
            id=call_id,
            function=method_name,
            args=processed_args,
            kwargs=processed_kwargs,
            ax_position=ax_position,
            stats=call_stats,
        )

        # Add to appropriate axes
        ax_record = self._figure_record.get_or_create_axes(*ax_position)

        if method_name in self.DECORATION_METHODS:
            ax_record.add_decoration(record)
        else:
            ax_record.add_call(record)

        return record

    def _process_args(
        self,
        args: tuple,
        method_name: str,
    ) -> List[Dict[str, Any]]:
        """Process positional arguments for storage."""
        from ._utils import process_args

        return process_args(
            args, method_name, self._get_arg_names, self._is_serializable
        )

    def _get_arg_names(self, method_name: str, n_args: int) -> List[str]:
        """Get argument names for a method from signatures.

        Parameters
        ----------
        method_name : str
            Name of the method.
        n_args : int
            Number of arguments.

        Returns
        -------
        list
            List of argument names.
        """
        try:
            from .._signatures import get_signature

            sig = get_signature(method_name)
            names = [arg["name"] for arg in sig["args"][:n_args]]
            # Pad with generic names if needed
            while len(names) < n_args:
                names.append(f"arg{len(names)}")
            return names
        except Exception:
            # Fallback to generic names
            return [f"arg{i}" for i in range(n_args)]

    def _process_kwargs(
        self,
        kwargs: Dict[str, Any],
        method_name: str,
    ) -> Dict[str, Any]:
        """Process keyword arguments for storage.

        Only stores non-default kwargs to keep recipes minimal.

        Parameters
        ----------
        kwargs : dict
            Raw keyword arguments.
        method_name : str
            Name of the method.

        Returns
        -------
        dict
            Processed kwargs (non-default only).
        """
        # Get defaults from signature
        defaults = {}
        try:
            from .._signatures import get_defaults

            defaults = get_defaults(method_name)
        except Exception:
            pass

        # Remove internal keys (stats is handled separately as metadata)
        skip_keys = {"id", "track", "_array", "stats"}
        processed = {}

        for key, value in kwargs.items():
            if key in skip_keys:
                continue

            # Skip if value matches default
            if key in defaults:
                default_val = defaults[key]
                # Compare values (handle None specially)
                if default_val is not None and value == default_val:
                    continue
                # Also skip if both are None
                if default_val is None and value is None:
                    continue

            # Serialize matplotlib transforms as portable markers so replay can
            # resolve them to the target axes' transforms; otherwise they fall
            # through to str() and replay crashes with "'str' object has no
            # attribute 'contains_branch_seperately'". transAxes reprs as
            # "BboxTransformTo..."; treat that as the "axes" marker.
            if key == "transform" and repr(value).startswith("BboxTransformTo"):
                processed[key] = "axes"
                continue

            if self._is_serializable(value):
                processed[key] = value
            elif isinstance(value, np.ndarray):
                processed[key] = value.tolist()
            elif hasattr(value, "values"):
                processed[key] = np.asarray(value).tolist()
            else:
                # Try to convert to string
                try:
                    processed[key] = str(value)
                except Exception:
                    pass

        return processed

    def _is_serializable(self, value: Any) -> bool:
        """Check if value is directly serializable to YAML."""
        if value is None:
            return True
        if isinstance(value, (bool, int, float, str)):
            return True
        if isinstance(value, (list, tuple)):
            return all(self._is_serializable(v) for v in value)
        if isinstance(value, dict):
            return all(
                isinstance(k, str) and self._is_serializable(v)
                for k, v in value.items()
            )
        return False


__all__ = ["Recorder"]

# EOF
