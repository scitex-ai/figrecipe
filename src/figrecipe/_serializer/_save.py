#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-side serialization for recipe files (YAML + data files)."""

from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
from ruamel.yaml import YAML

from .._recorder import FigureRecord
from .._utils._numpy_io import (
    CsvFormat,
    DataFormat,
    save_array,
    save_arrays_single_csv,
)
from ._utils import _convert_numpy_types, _sanitize_filename


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
                data, data_dir, source_data_dirs, record.id, data_format
            )
        else:
            # Save to separate files (original behavior)
            data = _process_arrays_for_save(data, data_dir, record.id, data_format)

    # Convert numpy types to native Python types
    data = _convert_numpy_types(data)

    # Save YAML.
    #
    # Write atomically via a sibling temp file + os.replace so a dump that
    # raises mid-serialization (e.g. a non-YAML-able object that slipped
    # into the record) NEVER leaves a truncated 0-byte recipe on disk that
    # would silently break downstream compose()/load_recipe(). Either the
    # full valid recipe lands, or the write fails loud and the previous
    # file (if any) is untouched.
    import os
    import tempfile

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.stem}.", suffix=".yaml.tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            yaml.dump(data, f)
    except Exception:
        # Fail loud: clean up the partial temp file, do not clobber path.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.replace(tmp_name, path)

    return path


def _process_arrays_for_save(
    data: Dict[str, Any],
    data_dir: Path,
    fig_id: str,
    data_format: DataFormat = "csv",
) -> Dict[str, Any]:
    """Process arrays in data dict, saving large ones to files."""
    data_dir_created = False

    for ax_key, ax_data in data.get("axes", {}).items():
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
                        filename = f"{safe_call_id}_{arg.get('name', f'arg{i}')}"
                        file_path = save_array(arr, data_dir / filename, data_format)
                        arg["data"] = str(file_path.relative_to(data_dir.parent))

    return data


def _process_arrays_with_symlinks(
    data: Dict[str, Any],
    data_dir: Path,
    source_data_dirs: Dict[str, Path],
    fig_id: str,
    data_format: DataFormat = "csv",
) -> Dict[str, Any]:
    """Process arrays using symlinks to source data directories."""
    import os

    data_dir_created = False

    for ax_key, ax_data in data.get("axes", {}).items():
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
                        filename = f"{safe_call_id}_{var_name}"
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
