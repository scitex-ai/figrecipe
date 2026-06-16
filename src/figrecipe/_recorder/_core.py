#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-23 09:57:28 (ywatanabe)"
# File: /home/ywatanabe/proj/figrecipe/src/figrecipe/_recorder.py


"""Core recording functionality for figrecipe."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import numpy as np

from .._utils._grid import grid_id, parse_grid_id


@dataclass
class CallRecord:
    """Record of a single plotting call."""

    id: str
    function: str
    args: List[Dict[str, Any]]
    kwargs: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    ax_position: Tuple[int, int] = (0, 0)
    # Statistics associated with this plot call (e.g., n, mean, sem)
    stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "function": self.function,
            "args": self.args,
            "kwargs": self.kwargs,
            "timestamp": self.timestamp,
        }
        if self.stats is not None:
            result["stats"] = self.stats
        return result

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], ax_position: Tuple[int, int] = (0, 0)
    ) -> "CallRecord":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            function=data["function"],
            args=data["args"],
            kwargs=data["kwargs"],
            timestamp=data.get("timestamp", ""),
            ax_position=ax_position,
            stats=data.get("stats"),
        )


@dataclass
class AxesRecord:
    """Record of all calls on a single axes."""

    position: Tuple[int, int]
    calls: List[CallRecord] = field(default_factory=list)
    decorations: List[CallRecord] = field(default_factory=list)
    # Panel-level caption (e.g., "(A) Description of this panel")
    caption: Optional[str] = None
    # Panel-level statistics (e.g., summary stats, comparison results)
    stats: Optional[Dict[str, Any]] = None
    # Panel visibility (for composition)
    visible: bool = True
    # Axes bbox [left, bottom, width, height] in the *cropped* image fraction
    # (see _capture_axes_bboxes) -- used for alignment/snap.
    bbox: Optional[List[float]] = None
    # Same, but in the *uncropped* figure fraction (mpl ax.get_position()).
    # Paired with FigureRecord.content_bbox it lets compose tile crop-aware.
    bbox_uncropped: Optional[List[float]] = None

    def add_call(self, record: CallRecord) -> None:
        """Add a plotting call record."""
        self.calls.append(record)

    def add_decoration(self, record: CallRecord) -> None:
        """Add a decoration call (set_xlabel, etc.)."""
        self.decorations.append(record)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "calls": [c.to_dict() for c in self.calls],
            "decorations": [d.to_dict() for d in self.decorations],
        }
        if self.bbox is not None:
            result["bbox"] = self.bbox
        if self.bbox_uncropped is not None:
            result["bbox_uncropped"] = self.bbox_uncropped
        if self.caption is not None:
            result["caption"] = self.caption
        if self.stats is not None:
            result["stats"] = self.stats
        if not self.visible:  # Only serialize if hidden (default is True)
            result["visible"] = False
        return result


@dataclass
class FigureRecord:
    """Record of an entire figure."""

    id: str = field(default_factory=lambda: f"fig_{uuid.uuid4().hex[:8]}")
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    matplotlib_version: str = field(default_factory=lambda: matplotlib.__version__)
    figsize: Tuple[float, float] = (6.4, 4.8)
    dpi: int = 300
    # Grid shape of the figure (nrows, ncols). Stored so the recipe / data-file
    # naming layer can compute deterministic, row-major panel labels (A, B, C,
    # …) from a panel's (row, col) position. ``None`` on legacy recipes loaded
    # from disk that pre-date this field — the consumer must treat that as
    # "single panel, no panel suffix".
    nrows: Optional[int] = None
    ncols: Optional[int] = None
    axes: Dict[str, AxesRecord] = field(default_factory=dict)
    # Layout parameters (subplots_adjust)
    layout: Optional[Dict[str, float]] = None
    # Style parameters
    style: Optional[Dict[str, Any]] = None
    # Constrained layout flag
    constrained_layout: bool = False
    # Figure-level decorations (suptitle, supxlabel, supylabel)
    suptitle: Optional[Dict[str, Any]] = None
    supxlabel: Optional[Dict[str, Any]] = None
    supylabel: Optional[Dict[str, Any]] = None
    # Arbitrary figure-level text annotations (fig.text() calls) —
    # each entry is {"x", "y", "s", "kwargs"}.
    figure_texts: List[Dict[str, Any]] = field(default_factory=list)
    # Panel labels (A, B, C, D for multi-panel figures)
    panel_labels: Optional[Dict[str, Any]] = None
    # Metadata for scientific figures (not rendered, stored in recipe)
    title_metadata: Optional[str] = None  # Figure title for publication/reference
    caption: Optional[str] = None  # Figure caption (e.g., "Fig. 1. Description...")
    # Figure-level statistics (e.g., comparisons across panels, summary)
    stats: Optional[Dict[str, Any]] = None
    # Crop information for post-save cropping (enables correct bbox recalculation)
    crop_info: Optional[Dict[str, Any]] = None
    # Tight content bbox [l, b, w, h] in *uncropped* figure fraction (from
    # get_tightbbox): real ink extent; may exceed [0,1]. Crop-aware compose.
    content_bbox: Optional[List[float]] = None
    # Tight content size [w_mm, h_mm] (content_bbox x figsize). dpi-independent.
    content_size_mm: Optional[List[float]] = None
    # mm_layout for auto-cropping during save (enables consistent cropping on reproduce)
    mm_layout: Optional[Dict[str, Any]] = None
    # Source data directories for composition (enables symlinks instead of copying)
    # Maps ax_key -> source data directory path
    source_data_dirs: Optional[Dict[str, Path]] = None
    # Colorbar calls: list of {mappable_id, ax_key, kwargs}
    colorbars: List[Dict[str, Any]] = field(default_factory=list)
    # Per-panel caption texts (set via fr.compose(panel_captions=...))
    figure_panel_captions: Optional[List[str]] = None

    def get_axes_key(self, row: int, col: int) -> str:
        """Get dictionary key for axes at position."""
        return grid_id(row, col)

    def get_or_create_axes(self, row: int, col: int) -> AxesRecord:
        """Get or create axes record at position."""
        key = self.get_axes_key(row, col)
        if key not in self.axes:
            self.axes[key] = AxesRecord(position=(row, col))
        return self.axes[key]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "figrecipe": "1.0",
            "id": self.id,
            "created": self.created,
            "matplotlib_version": self.matplotlib_version,
            "figure": {
                "figsize": list(self.figsize),
                "dpi": self.dpi,
            },
            "axes": {k: v.to_dict() for k, v in self.axes.items()},
        }
        # Persist grid shape (nrows, ncols) so panel-letter assignment is
        # deterministic when the recipe is re-loaded for reproduction.
        if self.nrows is not None and self.ncols is not None:
            result["figure"]["nrows"] = self.nrows
            result["figure"]["ncols"] = self.ncols
        # Add layout if set
        if self.layout is not None:
            result["figure"]["layout"] = self.layout
        # Add style if set
        if self.style is not None:
            result["figure"]["style"] = self.style
        # Add constrained_layout if True
        if self.constrained_layout:
            result["figure"]["constrained_layout"] = True
        # Add suptitle if set
        if self.suptitle is not None:
            result["figure"]["suptitle"] = self.suptitle
        # Add supxlabel if set
        if self.supxlabel is not None:
            result["figure"]["supxlabel"] = self.supxlabel
        # Add supylabel if set
        if self.supylabel is not None:
            result["figure"]["supylabel"] = self.supylabel
        # Add figure-level text annotations if any
        if self.figure_texts:
            result["figure"]["texts"] = self.figure_texts
        # Add panel_labels if set
        if self.panel_labels is not None:
            result["figure"]["panel_labels"] = self.panel_labels
        # Add metadata section for scientific figures
        metadata = {}
        if self.title_metadata is not None:
            metadata["title"] = self.title_metadata
        if self.caption is not None:
            metadata["caption"] = self.caption
        if self.stats is not None:
            metadata["stats"] = self.stats
        if metadata:
            result["metadata"] = metadata
        # Add crop_info if set (for bbox recalculation after cropping)
        if self.crop_info is not None:
            result["figure"]["crop_info"] = self.crop_info
        # Add tight-content layout if captured (for crop-aware composition)
        if self.content_bbox is not None:
            result["figure"]["content_bbox"] = self.content_bbox
        if self.content_size_mm is not None:
            result["figure"]["content_size_mm"] = self.content_size_mm
        # Add mm_layout if set (for consistent cropping on reproduce)
        if self.mm_layout is not None:
            result["figure"]["mm_layout"] = self.mm_layout
        # Add colorbars if set
        if self.colorbars:
            result["figure"]["colorbars"] = self.colorbars
        # Add per-panel caption texts if set
        if self.figure_panel_captions is not None:
            result["figure"]["panel_captions"] = self.figure_panel_captions
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FigureRecord":
        """Create from dictionary."""
        fig_data = data.get("figure", {})
        metadata = data.get("metadata", {})
        record = cls(
            id=data.get("id", f"fig_{uuid.uuid4().hex[:8]}"),
            created=data.get("created", ""),
            matplotlib_version=data.get("matplotlib_version", ""),
            figsize=tuple(fig_data.get("figsize", [6.4, 4.8])),
            dpi=fig_data.get("dpi", 300),
            nrows=fig_data.get("nrows"),
            ncols=fig_data.get("ncols"),
            layout=fig_data.get("layout"),
            style=fig_data.get("style"),
            constrained_layout=fig_data.get("constrained_layout", False),
            suptitle=fig_data.get("suptitle"),
            supxlabel=fig_data.get("supxlabel"),
            supylabel=fig_data.get("supylabel"),
            figure_texts=list(fig_data.get("texts", [])),
            panel_labels=fig_data.get("panel_labels"),
            title_metadata=metadata.get("title"),
            caption=metadata.get("caption"),
            stats=metadata.get("stats"),
            crop_info=fig_data.get("crop_info"),
            content_bbox=fig_data.get("content_bbox"),
            content_size_mm=fig_data.get("content_size_mm"),
            mm_layout=fig_data.get("mm_layout"),
            colorbars=fig_data.get("colorbars", []),
            figure_panel_captions=fig_data.get("panel_captions"),
        )

        # Reconstruct axes
        for ax_key, ax_data in data.get("axes", {}).items():
            # Parse position from key (accepts "r0c1" or legacy "ax_0_1")
            parsed = parse_grid_id(ax_key)
            row, col = parsed if parsed else (0, 0)

            ax_record = AxesRecord(
                position=(row, col),
                caption=ax_data.get("caption"),
                stats=ax_data.get("stats"),
                visible=ax_data.get("visible", True),
                bbox=ax_data.get("bbox"),
                bbox_uncropped=ax_data.get("bbox_uncropped"),
            )
            for call_data in ax_data.get("calls", []):
                ax_record.calls.append(CallRecord.from_dict(call_data, (row, col)))
            for dec_data in ax_data.get("decorations", []):
                ax_record.decorations.append(CallRecord.from_dict(dec_data, (row, col)))

            # Re-key to canonical grid id so downstream consumers always see
            # "r{row}c{col}" regardless of whether the recipe used the legacy
            # "ax_{row}_{col}" form.
            record.axes[grid_id(row, col)] = ax_record

        return record


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


# EOF
