#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel-label WEIGHT is a style-owned field, not a hardcoded code default.

The auto (A)/(B)/(C) panel labels resolve their font weight from the active
style's ``fonts.panel_label_weight`` (SCITEX: 'bold') the same way size and
family are style-owned, with 'bold' only the ultimate fallback for styles
without the field. AAA layout, ONE assertion each, no mocks, headless Agg.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr  # noqa: E402
from figrecipe.styles._style_loader import load_style  # noqa: E402


def test_scitex_style_owns_panel_label_weight():
    # Arrange / Act: load the SCITEX preset.
    style = load_style("SCITEX")
    # Assert: the weight is a real field on the style's fonts block.
    assert style.fonts.panel_label_weight == "bold"


def test_auto_panel_labels_weight_comes_from_style():
    # Arrange: SCITEX active, auto panel labels on a multi-panel figure.
    style = load_style("SCITEX")
    fig, axes = fr.subplots(2, 2, panel_labels=True)
    # Act: the weight figrecipe recorded for the auto labels.
    recorded = fig.record.panel_labels["fontweight"]
    # Assert: it was sourced from the style field, not a hardcoded default.
    assert recorded == style.fonts.panel_label_weight
