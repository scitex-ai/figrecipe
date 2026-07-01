#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The save path records the rendered image as a clew session output.

figrecipe already records the recipe YAML + data files with clew; the rendered
image was the missing leg of clew's recipe->data->image chain. Without it, a
stale/hand-edited PNG next to a valid recipe would still verify -- so clew could
not honestly mark the manuscript figure "reproducible". This guard asserts the
image the reader sees is recorded as a session output at save time.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr


def test_save_records_rendered_image_as_clew_output(tmp_path, monkeypatch):
    # Arrange: a spy standing in for clew's active-session tracker, capturing
    # every path figrecipe records as a session output (clew is an optional
    # dependency, so this substitutes at that boundary -- not the SUT).
    recorded = []

    class _SpyTracker:
        def record_output(self, path):
            recorded.append(path)

        def record_input(self, path):
            pass

    monkeypatch.setattr(
        "figrecipe._serializer._clew._active_tracker", lambda: _SpyTracker()
    )
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    image_path = tmp_path / "line.png"
    # Act
    fr.save(fig, str(image_path), validate=False, verbose=False)
    # Assert
    assert str(image_path) in recorded
