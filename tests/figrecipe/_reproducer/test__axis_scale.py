#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unsupported axis-scale warning on replay (figrecipe, NeuroVista Ask 2).

``set_xscale`` / ``set_yscale`` replay as generic decorations. A recognised scale
(log, symlog, logit, ...) must apply silently, but an unsupported / custom scale
must warn loudly instead of degrading silently to a linear axis (no silent
fallback).

The two silent cases below assert "no warning was raised" by turning warnings
into errors for the duration of ONE call. That must be scoped: `simplefilter`
mutates the PROCESS-global filter and is never undone, so an unscoped call leaves
every later test in the same process running with warnings-as-errors — and the
font fallback warning then fails an unrelated figure test. Measured before this
was scoped, in this environment (no Arial installed):

    pytest test__axis_scale.py test__core.py::TestPixelPerfect::test_bar_pixel_perfect
    -> 1 failed, 3 passed   (the second test failed on
       "font 'Arial' is not installed", which it never touched)

Under `-n 12 --dist load` the damage is a lottery rather than a constant, because
which tests share a worker with this module varies run to run: the same command on
the SAME tree failed 264 and then 269 tests, sharing only 185 of them.
"""

import warnings

import pytest

from figrecipe._reproducer._axis_scale import warn_if_unsupported_scale


def test_supported_scale_does_not_warn():
    # Arrange
    with warnings.catch_warnings():
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
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        # Act
        result = warn_if_unsupported_scale("set_xlim", ["bogus"])
    # Assert
    assert result is None


def test_the_error_filter_does_not_outlive_the_test():
    # Arrange -- the defect this guards: a process-global simplefilter("error")
    # survives the test that set it, so any later save errors on the font
    # fallback warning and a full-suite run reads as red for a reason no code
    # changed.
    before = [tuple(f) for f in warnings.filters]
    # Act
    test_supported_scale_does_not_warn()
    # Assert
    assert [tuple(f) for f in warnings.filters] == before
