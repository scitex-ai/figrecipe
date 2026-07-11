#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression: embedded/subpanel array data must be FILED, not left inline.

Root cause (residual trigger of the flaky imshow nested/compose-of-composed
round-trip, filed on scitex-todo as
``figrecipe-flaky-imshow-nested-roundtrip-datafile``): ``ax.embed(recipe)``
draws the source recipe's calls into a managed inset and attaches the
source's ALREADY-LOADED ``CallRecord`` objects to the host's
``subpanel_recorders`` (``_wrappers/_axes_embed.py::_draw_and_record_source``).
``load_recipe()`` fully materializes a data-file-backed arg as a plain Python
list (``arg["data"] = arr.tolist()``, plus ``_loaded_array``/``_source_file``)
so the source recipe can be replayed without a data directory of its own at
draw time.

The HOST save pipeline (``_serializer/_save.py``) only ever walked each
top-level axes' ``calls``/``decorations`` -- never the nested ``subpanels``
list that ``ax.embed()``/``ax.inset_axes()`` produce (see
``_recorder/_core.py::AxesRecord.to_dict()``). So an embedded source's
data-file-backed args were NEVER re-filed to a fresh CSV/NPZ on the host's
own save: they stayed inline, as the FULL nested Python list the loader
reconstructed, forever. For a small toy line this is invisible (a handful of
inline floats); for anything with real array volume (e.g. an ``imshow``
image) it turns ``_convert_numpy_types`` + ``ruamel.yaml.dump`` into an
O(N) walk over hundreds of thousands to millions of individual scalar nodes
-- pathologically slow (multi-minute, effectively a hang for practical CI
timeouts). This exactly reproduces the "flaky imshow nested round-trip" CI
symptom locally as a deterministic hang (confirmed via
``faulthandler.dump_traceback_later``, stuck inside
``ruamel.yaml.representer`` / ``_convert_numpy_types`` on the host's own
``fig.save_recipe()`` call, well before any validate/reproduce step runs).

Fix: ``_process_arrays_for_save`` / ``_process_arrays_with_symlinks`` now
recurse into ``subpanels`` (nested sub-sub-panels too), and for each arg
either write out a live ``_array`` (as before) or, when the arg only carries
a ``_source_file`` (the embed/loaded case), SYMLINK to that original backing
file -- the same treatment ``fr.compose()`` already gives composed panels,
extended to plain ``ax.embed()`` (which never set
``record.source_data_dirs`` and so never reached the symlink path at all).
The loader (``_serializer/_load.py::_resolve_data_references``) recurses into
``subpanels`` the same way, so a filed/symlinked subpanel reference resolves
back into real array data on load instead of leaving a raw filename string
as the "data" value.

AAA layout, ONE assertion focus per test, no mocks, headless Agg.
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
from ruamel.yaml import YAML  # noqa: E402

import figrecipe as fr  # noqa: E402

_yaml = YAML()


def _build_source_with_large_image(sdir: Path) -> Path:
    """Save a standalone imshow recipe with a sizeable (100x100) image."""
    rng = np.random.default_rng(0)
    fig, ax = fr.subplots(1, 1)
    ax.imshow(rng.uniform(0, 1, (100, 100)), id="big_image")
    recipe = sdir / "source.yaml"
    fr.save(fig, str(sdir / "source.png"), verbose=False)
    return recipe


def _load_raw_yaml(path: Path) -> dict:
    with open(path) as f:
        return _yaml.load(f)


def _find_subpanel_arg(data: dict, call_id: str, arg_name: str) -> dict:
    """Dig into ``axes -> subpanels -> axes -> calls`` for one arg dict."""
    for ax_data in data.get("axes", {}).values():
        for sp in ax_data.get("subpanels", []) or []:
            for call in sp.get("axes", {}).get("calls", []) or []:
                if call.get("id") == call_id:
                    for arg in call.get("args", []):
                        if arg.get("name") == arg_name:
                            return arg
    raise AssertionError(f"subpanel call {call_id!r} arg {arg_name!r} not found")


def test_embedded_large_array_is_filed_not_inlined():
    # Arrange: a host figure embedding a source recipe with a 100x100 image.
    with tempfile.TemporaryDirectory() as d:
        tmp_dir = Path(d)
        sdir = tmp_dir / "sources"
        sdir.mkdir()
        source_recipe = _build_source_with_large_image(sdir)
        host_fig, host_ax = fr.subplots(1, 1)
        host_ax.plot([0, 1, 2], [0, 1, 0], id="host_line")
        host_ax.embed(str(source_recipe), bounds=[0.5, 0.5, 0.4, 0.4])
        host_yaml = tmp_dir / "host.yaml"
        fr.save(host_fig, str(tmp_dir / "host.png"), verbose=False)
        # Act
        raw = _load_raw_yaml(host_yaml)
        arg = _find_subpanel_arg(raw, "big_image", "X")
        # Assert: filed as a real data-file reference, not an inline list.
        assert isinstance(arg.get("data"), str) and arg["data"].endswith(
            (".csv", ".npz", ".npy")
        )


def test_embedded_large_array_file_reference_exists_on_disk():
    # Arrange: same embed scenario as above.
    with tempfile.TemporaryDirectory() as d:
        tmp_dir = Path(d)
        sdir = tmp_dir / "sources"
        sdir.mkdir()
        source_recipe = _build_source_with_large_image(sdir)
        host_fig, host_ax = fr.subplots(1, 1)
        host_ax.plot([0, 1, 2], [0, 1, 0], id="host_line")
        host_ax.embed(str(source_recipe), bounds=[0.5, 0.5, 0.4, 0.4])
        host_yaml = tmp_dir / "host.yaml"
        fr.save(host_fig, str(tmp_dir / "host.png"), verbose=False)
        raw = _load_raw_yaml(host_yaml)
        arg = _find_subpanel_arg(raw, "big_image", "X")
        # Act
        file_path = host_yaml.parent / arg["data"]
        # Assert
        assert file_path.exists()


def test_small_embedded_array_stays_inline_and_validates():
    # Arrange: a host embedding a TINY (below-threshold) source line plot --
    # regression guard for a real bug this exact fix introduced: filing/
    # symlinking every subpanel array (regardless of size) broke the inset/
    # embed replay path (_reproducer/_replay_insets.py resolves a subpanel
    # arg's data straight from the recipe dict, not through the file-
    # reference resolver), causing a save-time reproducibility-validation
    # failure (MSE far over threshold) for the common small-embed case.
    with tempfile.TemporaryDirectory() as d:
        tmp_dir = Path(d)
        src_fig, src_ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
        src_ax.plot([0, 1, 2], [0, 2, 1])
        source_recipe = tmp_dir / "small_source.yaml"
        fr.save(src_fig, str(tmp_dir / "small_source.png"), verbose=False)
        host_fig, host_ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
        host_ax.plot([0, 1, 2, 3], [3, 2, 1, 0])
        host_ax.embed(str(source_recipe), bounds=[0.55, 0.55, 0.4, 0.4])
        # Act / Assert: validate=True raises on a reproducibility mismatch.
        fr.save(host_fig, str(tmp_dir / "small_host.png"), validate=True)


def test_embedded_recipe_round_trips_via_reproduce():
    # Arrange: save a host embedding a large-array source recipe.
    with tempfile.TemporaryDirectory() as d:
        tmp_dir = Path(d)
        sdir = tmp_dir / "sources"
        sdir.mkdir()
        source_recipe = _build_source_with_large_image(sdir)
        host_fig, host_ax = fr.subplots(1, 1)
        host_ax.plot([0, 1, 2], [0, 1, 0], id="host_line")
        host_ax.embed(str(source_recipe), bounds=[0.5, 0.5, 0.4, 0.4])
        host_yaml = tmp_dir / "host.yaml"
        fr.save(host_fig, str(tmp_dir / "host.png"), verbose=False)
        # Act: reproduce from the saved recipe (fresh load from disk).
        reproduced_fig, _ = fr.reproduce(str(host_yaml))
        # Assert: reproduces without raising (e.g. no FileNotFoundError on a
        # missing/broken subpanel data reference).
        assert reproduced_fig is not None
