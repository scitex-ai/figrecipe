#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression: serialization must NOT destroy the live record's data.

The save pipeline (``_process_arrays_for_save``) pops ``_array`` from a
record's args and rewrites ``data`` in place. ``CallRecord.to_dict()`` used
to return those args BY REFERENCE, so the FIRST save mutated the live
record -- stripping every arg's ``_array``. A second save/compose of the
same live record then emitted a data reference with no CSV written behind
it, and reproduce raised ``FileNotFoundError: <name>_data/<id>_x.csv`` (the
flaky imshow nested / compose-of-composed round-trip failure). ``to_dict()``
now returns a shallow-copied snapshot. AAA layout, ONE assertion each, no
mocks, headless Agg.
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._recorder import CallRecord  # noqa: E402


def test_to_dict_does_not_alias_live_args():
    # Arrange: an arg carrying an in-memory _array (what the save pipeline pops).
    record = CallRecord(
        id="plot_001",
        function="plot",
        args=[{"name": "x", "_array": np.array([1, 2, 3])}],
        kwargs={"color": "red"},
    )
    # Act: mutate the serialization snapshot the way the save pipeline does.
    record.to_dict()["args"][0].pop("_array")
    # Assert: the live record is untouched, so a later save still has its data.
    assert "_array" in record.args[0]


def test_second_save_of_same_figure_writes_data_files():
    # Arrange: one live figure whose line data is filed to CSV on save.
    with tempfile.TemporaryDirectory() as tmpdir:
        fig, ax = fr.subplots(1, 1)
        ax.plot([0, 1, 2, 3], [3, 2, 1, 0], id="host_line")
        fr.save(fig, str(Path(tmpdir) / "figA.png"))
        # Act: save the SAME live figure a second time to a fresh location.
        fr.save(fig, str(Path(tmpdir) / "figB.png"))
        # Assert: the second save wrote its own copy of the data file.
        assert (Path(tmpdir) / "figB_data" / "host_line_x.csv").exists()
