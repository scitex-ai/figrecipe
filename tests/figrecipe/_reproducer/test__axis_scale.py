#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unsupported axis-scale warning on replay (figrecipe, NeuroVista Ask 2).

``set_xscale`` / ``set_yscale`` replay as generic decorations. A recognised scale
(log, symlog, logit, ...) must apply silently, but an unsupported / custom scale
must warn loudly instead of degrading silently to a linear axis (no silent
fallback).
"""

import warnings

import pytest

from figrecipe._reproducer._axis_scale import warn_if_unsupported_scale


def test_supported_scale_does_not_warn():
    # Arrange
    warnings.simplefilter("error")
    # Act
    result = warn_if_unsupported_scale("set_yscale", ["log"])
    # Assert
    assert result is None


def test_unsupported_scale_warns():
    # Arrange
    args = ["totally-made-up-scale"]
    # Act
    # Assert
    with pytest.warns(UserWarning, match="unsupported axis scale"):
        warn_if_unsupported_scale("set_yscale", args)


def test_non_scale_method_does_not_warn():
    # Arrange
    warnings.simplefilter("error")
    # Act
    result = warn_if_unsupported_scale("set_xlim", ["bogus"])
    # Assert
    assert result is None
