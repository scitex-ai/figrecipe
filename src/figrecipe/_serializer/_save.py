#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-side serialization for recipe files (YAML + data files)."""

import warnings
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
from ._clew import record_output
from ._utils import _convert_numpy_types, _sanitize_filename

# Sub-panel array args below this size stay inline on save: the inset/embed
# replay path (_reproducer/_replay_insets.py) doesn't resolve file-reference
# ``data`` strings, only the top-level loader does. Above it, re-filing wins
# (avoids the pathological large-array inline-YAML slowdown/CI hang).
_SUBPANEL_FILE_REF_MIN_ELEMENTS = 256


def _subpanel_arr_size(loaded_array) -> int:
    return int(getattr(loaded_array, "size", 0) or 0)


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


def _assert_tick_call_faithful(call: Dict[str, Any]) -> None:
    """Record-time faithfulness guard (FR-FAITHFUL-TICKS): a set_xticks/set_yticks
    op must carry as many tick POSITIONS as LABELS, else the recipe can't
    round-trip (replay raises "FixedLocator locations != labels"). Fail loud at
    save rather than ship a silently-unreproducible recipe."""
    if call.get("function") not in ("set_xticks", "set_yticks"):
        return
    labels = call.get("kwargs", {}).get("labels")
    args = call.get("args", [])
    if labels is None or not args:
        return
    pos = args[0]
    if isinstance(pos, dict) and "_array" in pos:
        n_pos = len(pos["_array"])
    elif isinstance(pos, dict) and isinstance(pos.get("data"), list):
        n_pos = len(pos["data"])
    else:
        return  # positions length not determinable here; skip
    if n_pos != len(labels):
        raise ValueError(
            f"figrecipe [FR-FAITHFUL-TICKS]: {call.get('function')} recorded "
            f"{n_pos} tick positions but {len(labels)} labels (call "
            f"{call.get('id')}). This recipe would not round-trip (replay would "
            f"raise FixedLocator count != labels) -- indicates a recording/"
            f"serialization bug. Not shipping a mismatched recipe."
        )


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

    # Fail loud (with file + which caption/panel) on caption content that breaks
    # downstream LaTeX (FR-CAP-001) -- the authoritative output-side check.
    _validate_record_captions(record, path)

    # Create data directory for large arrays (only for separate format)
    data_dir = path.parent / f"{path.stem}_data"

    # Capture the active rcParams (delta from matplotlib default, as primitives)
    # so the recipe reproduces under the identical style environment -- a loaded
    # theme (SCITEX_STYLE) or ANY globally-set rcParam that is not in figrecipe's
    # curated ``style`` block. Guard on ``is None`` so a reproduced figure being
    # re-saved keeps its recipe's recorded rcParams (never re-derives them from a
    # possibly-different live context).
    if getattr(record, "rcparams", None) is None:
        from ..styles._rcparams import capture_rcparams_delta

        record.rcparams = capture_rcparams_delta()

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

    # Emit a writer-compatible caption-only .tex sidecar next to the recipe
    # (loose-coupling seam: scitex-writer reads the file, never imports
    # figrecipe). Only when the recipe actually carries caption text.
    _emit_caption_sidecar(record, path)

    # Record the recipe as a clew output of the active session (no-op without
    # clew). This is the handle that connects a composed figure to its source
    # panels: compose later record_inputs these recipes -> clew links sessions.
    record_output(path)
    return path


def _validate_record_captions(record: FigureRecord, path: Path) -> None:
    """Fail loud on caption content that breaks LaTeX (FR-CAP-001), naming the
    file + which caption/panel offends."""
    from .._captions._validate import check_caption_latex_safe

    check_caption_latex_safe(
        getattr(record, "caption", None), f"the figure caption of {path.name}"
    )
    panel_caps = getattr(record, "figure_panel_captions", None) or []
    for i, cap in enumerate(panel_caps):
        check_caption_latex_safe(
            cap, f"the panel {chr(ord('A') + i)} caption of {path.name}"
        )


def _assemble_caption_text(record: FigureRecord) -> str:
    """Fold the figure caption + per-panel captions into one manuscript caption.

    Returns the figure-level ``record.caption`` followed by ``(A) ...`` lines
    for each non-empty per-panel caption, in panel order — the complete text a
    manuscript ``\\caption{...}`` wants. Empty string when there is nothing.
    """
    parts = []
    if record.caption:
        parts.append(str(record.caption).strip())
    panel_caps = getattr(record, "figure_panel_captions", None)
    if panel_caps:
        for i, cap in enumerate(panel_caps):
            if cap and str(cap).strip():
                label = chr(ord("A") + i)
                parts.append(f"({label}) {str(cap).strip()}")
    return " ".join(p for p in parts if p)


def _emit_caption_sidecar(record: FigureRecord, path: Path) -> None:
    """Write ``<stem>.tex`` (caption-only fragment) next to the recipe, if any.

    No-op when the recipe carries no caption text, so a figure without a
    caption produces no stray sidecar.
    """
    text = _assemble_caption_text(record)
    if not text:
        return
    from .._captions._formats import format_caption_only_tex
    from .._captions._manuscript_mode import is_manuscript_mode

    # In manuscript mode the .tex is symlinked into the manuscript under a
    # different filename and scitex-writer auto-labels by that symlink stem;
    # a hardcoded \label here would win and break \ref{fig:<filename-stem>}.
    # So omit the label in manuscript mode; keep it for standalone use.
    label_slug = None if is_manuscript_mode() else path.stem
    tex_path = path.with_suffix(".tex")
    tex_path.write_text(
        format_caption_only_tex(text, label_slug=label_slug), encoding="utf-8"
    )


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

    Recurses into ``subpanels`` (``ax.embed()``/``ax.inset_axes()``): an
    embedded source's LARGE array-backed calls (e.g. an ``imshow`` image,
    >= ``_SUBPANEL_FILE_REF_MIN_ELEMENTS``) are re-filed/symlinked to their
    original backing file instead of staying inline forever -- avoids the
    pathologically slow ``_convert_numpy_types``+``ruamel.yaml.dump`` walk
    over a giant nested-list literal (the "flaky imshow nested round-trip"
    CI hang, see ``tests/integration/test_embed_subpanel_data_filing.py``).
    Small sub-panel arrays stay inline: the inset replay path
    (``_reproducer/_replay_insets.py``) resolves sub-panel args straight
    from the recipe dict, not through the file-reference resolver.
    """
    import os

    data_dir_created = False

    def _process_call_list(
        call_list, panel_prefix: str, id_prefix: str, in_subpanel: bool
    ) -> None:
        nonlocal data_dir_created
        for call in call_list:
            call_id = call.get("id", "unknown")
            safe_call_id = _sanitize_filename(f"{id_prefix}{call_id}")

            for i, arg in enumerate(call.get("args", [])):
                arr = arg.pop("_array", None)
                source_file_path = arg.pop("_source_file", None)
                loaded_array = arg.pop("_loaded_array", None)

                if arr is not None:
                    if not data_dir_created:
                        data_dir.mkdir(parents=True, exist_ok=True)
                        data_dir_created = True

                    filename = (
                        f"{panel_prefix}{safe_call_id}_{arg.get('name', f'arg{i}')}"
                    )
                    file_path = save_array(arr, data_dir / filename, data_format)
                    arg["data"] = str(file_path.relative_to(data_dir.parent))
                    record_output(file_path)  # clew: data file as session output

                elif source_file_path and (
                    not in_subpanel
                    or _subpanel_arr_size(loaded_array)
                    >= _SUBPANEL_FILE_REF_MIN_ELEMENTS
                ):
                    source_file = Path(source_file_path)
                    if source_file.exists():
                        if not data_dir_created:
                            data_dir.mkdir(parents=True, exist_ok=True)
                            data_dir_created = True

                        target_path = data_dir / source_file.name
                        # Refresh: drop any stale/broken link left by a prior
                        # run so the symlink always points at the CURRENT
                        # source, never a renamed/moved phantom.
                        if target_path.is_symlink() or target_path.exists():
                            target_path.unlink()
                        rel_source = os.path.relpath(source_file, target_path.parent)
                        os.symlink(rel_source, target_path)
                        arg["data"] = str(target_path.relative_to(data_dir.parent))
                        record_output(target_path)
                    else:
                        # The source file that backed this loaded value has
                        # vanished. Best-effort here (this is a re-filing
                        # OPTIMIZATION, not the sole path to correctness) --
                        # leave the inline "data" load already reconstructed
                        # rather than failing loud, since the recipe still
                        # reproduces (just without the size/speed win). Warn
                        # so a bloated re-saved recipe doesn't go unnoticed.
                        warnings.warn(
                            f"figrecipe: source data file for call "
                            f"{call_id!r} no longer exists at "
                            f"{source_file_path!r}; this array will be "
                            f"re-saved INLINE in the recipe YAML instead of "
                            f"filed/symlinked, which can bloat the file for "
                            f"large arrays.",
                            stacklevel=2,
                        )

    def _process_ax_data(
        ax_data, panel_prefix: str, id_prefix: str, in_subpanel: bool
    ) -> None:
        _process_call_list(
            ax_data.get("calls", []), panel_prefix, id_prefix, in_subpanel
        )
        _process_call_list(
            ax_data.get("decorations", []), panel_prefix, id_prefix, in_subpanel
        )
        for sp_idx, sp in enumerate(ax_data.get("subpanels", []) or []):
            sp_axes = sp.get("axes")
            if sp_axes is not None:
                _process_ax_data(
                    sp_axes, panel_prefix, f"{id_prefix}sub{sp_idx}_", True
                )

    for ax_key, ax_data in data.get("axes", {}).items():
        panel_prefix = _panel_prefix(ax_key, nrows, ncols)
        _process_ax_data(ax_data, panel_prefix, "", False)

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

    Recurses into ``subpanels`` for the same reason ``_process_arrays_for_save``
    does (see its docstring): an embedded source's array-backed calls must be
    re-filed (symlinked or written), never left inline, or a sizeable embedded
    array turns every save into a multi-minute ``_convert_numpy_types`` +
    ``ruamel.yaml.dump`` walk over a giant nested-list literal.
    """
    import os

    data_dir_created = False

    def _process_call_list(call_list, panel_prefix: str, id_prefix: str) -> None:
        nonlocal data_dir_created
        for call in call_list:
            call_id = call.get("id", "unknown")
            safe_call_id = _sanitize_filename(f"{id_prefix}{call_id}")
            _assert_tick_call_faithful(call)

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

                    # Fail loud: composition references the REAL source data
                    # (single source of truth); a missing source must never
                    # produce a silently-broken recipe symlink.
                    if not source_file.exists():
                        raise FileNotFoundError(
                            f"compose source data file missing: {source_file} "
                            f"(call {call_id}). Cannot create a valid data "
                            f"symlink for the composed recipe."
                        )
                    # Refresh: drop any stale/broken link left by a prior run
                    # so the symlink always points at the CURRENT source, never
                    # a renamed/moved phantom.
                    if target_path.is_symlink() or target_path.exists():
                        target_path.unlink()
                    rel_source = os.path.relpath(source_file, target_path.parent)
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

    def _process_ax_data(ax_data, panel_prefix: str, id_prefix: str) -> None:
        _process_call_list(ax_data.get("calls", []), panel_prefix, id_prefix)
        _process_call_list(ax_data.get("decorations", []), panel_prefix, id_prefix)
        for sp_idx, sp in enumerate(ax_data.get("subpanels", []) or []):
            sp_axes = sp.get("axes")
            if sp_axes is not None:
                _process_ax_data(sp_axes, panel_prefix, f"{id_prefix}sub{sp_idx}_")

    for ax_key, ax_data in data.get("axes", {}).items():
        panel_prefix = _panel_prefix(ax_key, nrows, ncols)
        _process_ax_data(ax_data, panel_prefix, "")

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
