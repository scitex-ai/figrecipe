#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""An artist removed after being drawn must not pass unnoticed at save time.

Card figrecipe-recipe-keeps-artists-removed-before-save-20260906, detect-and-warn
slice (coordinator decision 2026-09-17). The check is deliberately conservative:
it may miss a removal, it must never invent one, because a bogus warning on every
save teaches users to ignore the warning entirely.

Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import warnings
from pathlib import Path

from figrecipe._recorder._lifecycle import (
    ArtistLifecycleWarning,
    PLOTTING_METHODS,
    RemovalReport,
    detect_removals,
    minimum_artists_for,
    removals_in_figure,
    warn_removals,
)


class FakeCall:
    """The only thing the check reads from a CallRecord: its function name."""

    def __init__(self, function: str):
        self.function = function


class TestMinimumArtists:
    def test_only_plotting_calls_raise_the_minimum(self):
        # Arrange -- a decoration must not inflate the lower bound, or the check
        # would cry wolf on ordinary figures.
        calls = [FakeCall("plot"), FakeCall("set_xlabel"), FakeCall("scatter")]
        # Act
        minimum = minimum_artists_for(calls)
        # Assert
        assert minimum == 2

    def test_a_figure_with_no_plotting_calls_has_nothing_to_compare(self):
        # Arrange
        calls = [FakeCall("set_xlabel"), FakeCall("legend")]
        # Act
        minimum = minimum_artists_for(calls)
        # Assert -- None, not 0: zero artists expected is not a claim worth making.
        assert minimum is None


class TestDetection:
    def test_fewer_live_artists_than_calls_is_reported(self):
        # Arrange -- three recorded plot calls, one artist left on the axes.
        calls = [FakeCall("plot"), FakeCall("plot"), FakeCall("plot")]
        # Act
        report = detect_removals("ax_0_0", calls, live_artists=1)
        # Assert
        assert report == RemovalReport(axes_key="ax_0_0", minimum=3, live=1)

    def test_the_report_says_how_many_were_lost(self):
        # Arrange
        report = RemovalReport(axes_key="ax_0_0", minimum=3, live=1)
        # Act
        missing = report.missing
        # Assert
        assert missing == 2

    def test_more_live_artists_than_calls_is_not_reported(self):
        # Arrange -- decorations, ticks and the user's own additions all add
        # artists, which is the ORDINARY case and must stay quiet.
        calls = [FakeCall("plot")]
        # Act
        report = detect_removals("ax_0_0", calls, live_artists=40)
        # Assert
        assert report is None

    def test_a_decoration_only_axes_is_never_reported(self):
        # Arrange
        calls = [FakeCall("set_ylabel")]
        # Act
        report = detect_removals("ax_0_0", calls, live_artists=0)
        # Assert
        assert report is None

    def test_every_axes_is_checked_not_just_the_first(self):
        # Arrange
        axes = [
            ("ax_0_0", [FakeCall("plot")], 0),
            ("ax_0_1", [FakeCall("plot")], 5),
        ]
        # Act
        reports = removals_in_figure(axes)
        # Assert
        assert [r.axes_key for r in reports] == ["ax_0_0"]


class TestTheWarning:
    def test_the_warning_states_the_consequence_and_its_own_limits(self):
        # Arrange
        reports = [RemovalReport(axes_key="ax_0_0", minimum=3, live=1)]
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            shortfall = warn_removals(reports)
        message = str(caught[0].message) if caught else ""
        # Assert -- the user is told what will happen AND that the check is a
        # lower bound, so a miss is not read as a guarantee.
        assert shortfall == 2 and "conservative" in message

    def test_it_says_nothing_was_changed_for_the_user(self):
        # Arrange -- the slice must not mutate artwork, and the message must not
        # imply it did.
        reports = [RemovalReport(axes_key="ax_0_0", minimum=2, live=1)]
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warn_removals(reports)
        message = str(caught[0].message) if caught else ""
        # Assert
        assert "Nothing was changed for you" in message

    def test_a_clean_figure_is_silent(self):
        # Arrange
        reports = []
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            shortfall = warn_removals(reports)
        # Assert -- a save of a faithful figure must produce no lifecycle noise.
        assert shortfall == 0 and not caught

    def test_the_warning_class_is_a_user_warning(self):
        # Arrange
        warning_class = ArtistLifecycleWarning
        # Act
        is_user_warning = issubclass(warning_class, UserWarning)
        # Assert
        assert is_user_warning


class TestModuleHygiene:
    def test_the_module_stays_dependency_free(self):
        # Arrange
        module = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "figrecipe"
            / "_recorder"
            / "_lifecycle.py"
        )
        # Act
        text = module.read_text(encoding="utf-8")
        # Assert -- it must run under the repo's expression tests.
        assert "import matplotlib" not in text and "from figrecipe" not in text

    def test_the_plotting_method_set_is_not_empty(self):
        # Arrange
        methods = PLOTTING_METHODS
        # Act
        has_core_methods = {"plot", "scatter", "bar"} <= methods
        # Assert
        assert has_core_methods
