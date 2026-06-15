#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-side serialization for recipe files (YAML + data files)."""

from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
from ruamel.yaml import YAML

from .._recorder import FigureRecord
from .._recorder._panel_id import panel_label_for_position
from .._utils._grid import parse_grid_id
from .._utils._numpy_io import (
    CsvFormat,
    DataFormat,
    save_array,
    save_arrays_single_csv,
)
from ._utils import _convert_numpy_types, _sanitize_filename


def _panel_prefix(ax_key: str, nrows, ncols) -> str:
    """Return ``"A_"`` / ``"B_"`` / … for the panel at *ax_key*, or ``""``.

    Empty string for single-panel figures and legacy recipes (missing grid
    shape), so filenames stay clutter-free in those cases — matches the
    rendered behaviour where ``fr.subplots(1, 1)`` skips the panel label.
    """
    pos = parse_grid_id(ax_key)
    if pos is None:
        return ""
    label = panel_label_for_position(pos[0], pos[1], nrows, ncols)
    return f"{label}_" if label else ""


def save_recipe(
    record: FigureRecord,
    path: Union[str, Path],
    include_data: bool = True,
    data_format: DataFormat = "csv",
    csv_format: CsvFormat = "separate",
    use_symlinks: bool = True,
) -> Path:
    """Save a figure record to YAML file.

    Parameters
    ----------
    record : FigureRecord
        The figure record to save.
    path : str or Path
        Output path (.yaml).
    include_data : bool
        If True, save large arrays to separate files.
    data_format : str
        Format for data files: 'csv' (default), 'npz', or 'inline'.
    csv_format : str
        CSV file structure: 'separate' (default) or 'single'.
    use_symlinks : bool
        If True and record has source_data_dirs (from composition),
        create symlinks to original data files instead of copying.

    Returns
    -------
    Path
        Path to saved YAML file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create data directory for large arrays (only for separate format)
    data_dir = path.parent / f"{path.stem}_data"

    # Convert record to dict
    data = record.to_dict()

    # Check if we can use symlinks for composed figures
    source_data_dirs = getattr(record, "source_data_dirs", None)

    # Process arrays: save large ones to files, update references
    if include_data and data_format != "inline":
        if data_format == "csv" and csv_format == "single":
            # Save all arrays to single CSV file
            csv_path = path.with_suffix(".csv")
            data = _process_arrays_for_single_csv(data, csv_path)
        elif use_symlinks and source_data_dirs:
            # Use symlinks to source data directories
            data = _process_arrays_with_symlinks(
                data,
                data_dir,
                source_data_dirs,
                record.id,
                data_format,
                nrows=record.nrows,
                ncols=record.ncols,
            )
        else:
            # Save to separate files (original behavior)
            data = _process_arrays_for_save(
                data,
                data_dir,
                record.id,
                data_format,
                nrows=record.nrows,
                ncols=record.ncols,
            )

    # Convert numpy types to native Python types
    data = _convert_numpy_types(data)

    # Save YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path, "w") as f:
        yaml.dump(data, f)

    return path


def _process_arrays_for_save(
    data: Dict[str, Any],
    data_dir: Path,
    fig_id: str,
    data_format: DataFormat = "csv",
    nrows=None,
    ncols=None,
) -> Dict[str, Any]:
    """Process arrays in data dict, saving large ones to files.

    Data-file naming follows the rendered panel labels: for a 2x3 figure the
    data from panel A (top-left) lands in ``A_<call_id>_<argname>.csv`` while
    panel F's data lands in ``F_<call_id>_<argname>.csv``. Single-panel
    figures and legacy recipes that don't carry the grid shape get no panel
    prefix (the operator never thinks of them as having "panels").
    """
    data_dir_created = False

    for ax_key, ax_data in data.get("axes", {}).items():
        panel_prefix = _panel_prefix(ax_key, nrows, ncols)
        for call_list in [ax_data.get("calls", []), ax_data.get("decorations", [])]:
            for call in call_list:
                call_id = call.get("id", "unknown")
                safe_call_id = _sanitize_filename(call_id)

                # Process args
                for i, arg in enumerate(call.get("args", [])):
                    if "_array" in arg:
                        if not data_dir_created:
                            data_dir.mkdir(parents=True, exist_ok=True)
                            data_dir_created = True

                        arr = arg.pop("_array")
                        filename = (
                            f"{panel_prefix}{safe_call_id}_{arg.get('name', f'arg{i}')}"
                        )
                        file_path = save_array(arr, data_dir / filename, data_format)
                        arg["data"] = str(file_path.relative_to(data_dir.parent))

    return data


def _process_arrays_with_symlinks(
    data: Dict[str, Any],
    data_dir: Path,
    source_data_dirs: Dict[str, Path],
    fig_id: str,
    data_format: DataFormat = "csv",
    nrows=None,
    ncols=None,
) -> Dict[str, Any]:
    """Process arrays using symlinks to source data directories.

    For arrays that aren't symlinked (no ``_source_file`` recorded), the
    panel-letter prefix is applied to the resulting filename so the
    composition path uses the same naming convention as the standard save.
    """
    import os

    data_dir_created = False

    for ax_key, ax_data in data.get("axes", {}).items():
        panel_prefix = _panel_prefix(ax_key, nrows, ncols)
        for call_list in [ax_data.get("calls", []), ax_data.get("decorations", [])]:
            for call in call_list:
                call_id = call.get("id", "unknown")
                safe_call_id = _sanitize_filename(call_id)

                for i, arg in enumerate(call.get("args", [])):
                    source_file_path = arg.pop("_source_file", None)
                    arr = arg.pop("_array", None)
                    arg.pop("_loaded_array", None)

                    if source_file_path:
                        if not data_dir_created:
                            data_dir.mkdir(parents=True, exist_ok=True)
                            data_dir_created = True

                        source_file = Path(source_file_path)
                        target_path = data_dir / source_file.name

                        if not target_path.exists() and source_file.exists():
                            rel_source = os.path.relpath(
                                source_file, target_path.parent
                            )
                            os.symlink(rel_source, target_path)

                        arg["data"] = str(target_path.relative_to(data_dir.parent))

                    elif arr is not None:
                        if not data_dir_created:
                            data_dir.mkdir(parents=True, exist_ok=True)
                            data_dir_created = True

                        var_name = arg.get("name", f"arg{i}")
                        filename = f"{panel_prefix}{safe_call_id}_{var_name}"
                        file_path = save_array(arr, data_dir / filename, data_format)
                        arg["data"] = str(file_path.relative_to(data_dir.parent))

    return data


def _process_arrays_for_single_csv(
    data: Dict[str, Any],
    csv_path: Path,
) -> Dict[str, Any]:
    """Process arrays in data dict, saving all to single CSV file."""
    arrays_by_trace = {}

    for ax_key, ax_data in data.get("axes", {}).items():
        arrays_by_trace[ax_key] = {}

        for call_list in [ax_data.get("calls", []), ax_data.get("decorations", [])]:
            for call in call_list:
                call_id = call.get("id", "unknown")

                trace_arrays = {}
                for arg in call.get("args", []):
                    var_name = arg.get("name", "data")

                    if "_array" in arg:
                        arr = arg.pop("_array")
                        trace_arrays[var_name] = arr
                        arg["data"] = str(csv_path.name)
                    elif isinstance(arg.get("data"), list):
                        arr = np.array(arg["data"])
                        trace_arrays[var_name] = arr
                        arg["data"] = str(csv_path.name)

                if trace_arrays:
                    arrays_by_trace[ax_key][call_id] = trace_arrays

    if any(traces for traces in arrays_by_trace.values()):
        save_arrays_single_csv(arrays_by_trace, csv_path)

        data["data"] = {
            "csv_path": str(csv_path.name),
            "csv_format": "single",
        }

    return data
