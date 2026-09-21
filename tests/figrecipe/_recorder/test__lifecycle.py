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

import matplotlib

matplotlib.use("Agg")  # before figrecipe: the save path renders

import figrecipe as fr  # noqa: E402
from figrecipe._api._save_helpers import _live_artist_count
from figrecipe._params import DECORATION_METHODS
from figrecipe._params import (
    PLOTTING_METHODS as RECORDER_PLOTTING_METHODS,
)
from figrecipe._recorder._lifecycle import (
    ARTIST_DECORATIONS,
    PLOTTING_METHODS,
    ArtistLifecycleWarning,
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


class TestArtistBearingDecorations:
    """``ax.text()`` / ``ax.annotate()`` are DECORATIONS in the record, and they
    create artists.

    An ``AxesRecord`` holds ``calls`` and ``decorations`` as separate halves, and
    the shipped slice was handed ``calls`` alone — which made the card's own
    headline case (a text drawn, then removed) unreachable however wide the
    vocabulary was. These are the decision-level counterparts of the save-path
    tests below.
    """

    def test_text_raises_the_minimum_because_it_leaves_an_artist(self):
        # Arrange -- a decoration that owns an artist counts like a plot call.
        records = [FakeCall("plot"), FakeCall("text")]
        # Act
        minimum = minimum_artists_for(records)
        # Assert
        assert minimum == 2

    def test_a_decoration_outside_the_live_containers_is_not_counted(self):
        # Arrange -- ax.table() appends to ax.tables, which the live count does
        # not cover, so counting it would warn on a figure that lost nothing.
        records = [FakeCall("plot"), FakeCall("table")]
        # Act
        minimum = minimum_artists_for(records)
        # Assert
        assert minimum == 1


class TestTheVocabularyCannotDriftFromTheRecorder:
    """The detector must not keep its own copy of the recorder's vocabulary.

    The first shipped slice listed 24 of the recorder's 49 plotters; the artist of
    the other 26 could be removed and the save stayed silent. These tests make the
    divergence a failure instead of a silent undercount.
    """

    def test_the_plotting_vocabulary_is_the_recorders_own(self):
        # Arrange
        recorded = set(RECORDER_PLOTTING_METHODS)
        # Act
        detected = set(PLOTTING_METHODS)
        # Assert
        assert detected == recorded

    def test_every_counted_decoration_is_a_recorder_decoration(self):
        # Arrange
        recorded = set(DECORATION_METHODS)
        # Act
        counted = set(ARTIST_DECORATIONS)
        # Assert -- a name the recorder does not file as a decoration could never
        # arrive in the records this check reads.
        assert counted <= recorded

    def test_no_method_is_counted_in_both_vocabularies(self):
        # Arrange -- a name in both halves would be counted twice, once per half.
        overlapping = set(PLOTTING_METHODS).intersection(ARTIST_DECORATIONS)
        # Act
        doubled = sorted(overlapping - {"arrow"})
        # Assert -- arrow is recorded as a decoration only, so it is listed once.
        assert doubled == []


class TestTheCountedDecorationsAddALiveArtist:
    """The live-count counterpart of the vocabulary decision.

    A name in :data:`ARTIST_DECORATIONS` whose artist the live count cannot see
    would report a removal that never happened.
    """

    def test_text_lands_in_a_container_the_live_count_covers(self):
        # Arrange
        fig, ax = fr.subplots()
        # Act
        ax.text(0.5, 0.5, "T")
        # Assert
        assert _live_artist_count(fig.fig.get_axes()[0]) >= 1

    def test_annotate_lands_in_a_container_the_live_count_covers(self):
        # Arrange
        fig, ax = fr.subplots()
        # Act
        ax.annotate("A", xy=(1, 1), xytext=(2, 2))
        # Assert
        assert _live_artist_count(fig.fig.get_axes()[0]) >= 1

    def test_a_table_lands_nowhere_the_live_count_looks(self):
        # Arrange
        fig, ax = fr.subplots()
        # Act
        ax.table(cellText=[["a"]], loc="center")
        # Assert -- measured 0: this is why `table` stays out of the vocabulary.
        assert _live_artist_count(fig.fig.get_axes()[0]) == 0


class TestSavePathWiring:
    """The detector must fire from a REAL save, not only when called directly.

    The tests above prove the decision; these prove the WIRING in
    ``_api/_save_helpers.py`` — the part a function-level test cannot see, and
    the part that has twice in this repo been the actual defect (a correct pure
    layer behind a hook nobody reached).
    """

    @staticmethod
    def _save_with_removed_artist(tmp_path, name):
        """Draw two lines, remove one, save. Returns the lifecycle warnings."""
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 2, 3], label="keep")
        (doomed,) = ax.plot([1, 2, 3], [3, 2, 1], label="drop")
        doomed.remove()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fr.save(fig, tmp_path / name, validate=False, verbose=False)
        return [w for w in caught if "fewer artists" in str(w.message)]

    @staticmethod
    def _save_faithful_figure(tmp_path, name):
        """Draw one line and save. Returns the lifecycle warnings."""
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 2, 3], label="keep")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fr.save(fig, tmp_path / name, validate=False, verbose=False)
        return [w for w in caught if "fewer artists" in str(w.message)]

    @staticmethod
    def _save_with_removed_text(tmp_path, name):
        """The card's headline case verbatim: draw a text, remove it, save."""
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        drawn = ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        drawn.remove()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fr.save(fig, tmp_path / name, validate=False, verbose=False)
        return [w for w in caught if "fewer artists" in str(w.message)]

    @staticmethod
    def _save_with_a_text_still_shown(tmp_path, name):
        """The same figure with nothing removed: the false-positive control."""
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fr.save(fig, tmp_path / name, validate=False, verbose=False)
        return [w for w in caught if "fewer artists" in str(w.message)]

    @staticmethod
    def _save_with_removed_vlines(tmp_path, name):
        """Remove a vlines collection, a plotter the first vocabulary omitted."""
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 2, 3], label="keep")
        ruled = ax.vlines([1, 2], 0, 1)
        ruled.remove()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fr.save(fig, tmp_path / name, validate=False, verbose=False)
        return [w for w in caught if "fewer artists" in str(w.message)]

    def test_a_real_save_warns_when_an_artist_was_removed(self, tmp_path):
        # Arrange
        name = "removed.png"
        # Act
        hits = self._save_with_removed_artist(tmp_path, name)
        # Assert -- exactly one warning, not one per call or per axes.
        assert len(hits) == 1

    def test_a_real_save_is_silent_for_a_faithful_figure(self, tmp_path):
        # Arrange
        name = "faithful.png"
        # Act
        hits = self._save_faithful_figure(tmp_path, name)
        # Assert -- a faithful figure must produce no lifecycle noise at all.
        assert hits == []

    def test_a_real_save_warns_when_a_text_was_removed(self, tmp_path):
        # Arrange -- the headline case: a DECORATION that owns the removed artist.
        name = "text_removed.png"
        # Act
        hits = self._save_with_removed_text(tmp_path, name)
        # Assert
        assert len(hits) == 1

    def test_a_real_save_is_silent_when_the_text_is_still_shown(self, tmp_path):
        # Arrange -- the control that makes the line above mean something: the
        # same figure, nothing removed, must stay quiet.
        name = "text_kept.png"
        # Act
        hits = self._save_with_a_text_still_shown(tmp_path, name)
        # Assert
        assert hits == []

    def test_a_real_save_warns_when_a_vlines_artist_was_removed(self, tmp_path):
        # Arrange -- vlines is one of the 26 plotters the hand-copied vocabulary
        # never listed, so this is the derivation change earning its keep.
        name = "vlines_removed.png"
        # Act
        hits = self._save_with_removed_vlines(tmp_path, name)
        # Assert
        assert len(hits) == 1
