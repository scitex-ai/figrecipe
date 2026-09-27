#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A recorded call whose artists left the figure must not reach the recipe.

Card figrecipe-recipe-keeps-artists-removed-before-save-20260906, REPAIR slice.
The detection slice (_lifecycle.py) reports the divergence and leaves the recipe
wrong; validation then rejects a figure that is CORRECT (measured MSE 353.09 for
the card's headline case). These tests are about the repair: the record is
reconciled to the artists the live figure still holds, so a replay draws what the
PNG shows.

Two properties matter equally, and both are asserted below:
  * the failing cases become faithful (MSE 0.00 from a REAL save), and
  * NOTHING ELSE MOVES -- a figure with no removal must come out of the save with
    exactly the recipe it had before, and an invisible artist is not a removed
    one.

Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import warnings
import weakref
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # before figrecipe: the save path renders

import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.text import Text  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._quality._validator import validate_on_save  # noqa: E402
from figrecipe._recorder._artists import (  # noqa: E402
    call_is_gone,
    flatten_artists,
    live_artist_ids,
    note_call_artists,
    prune,
    referenced_call_ids,
)
from figrecipe._recorder._lifecycle import ArtistLifecycleWarning  # noqa: E402


class FakeRecord:
    """The only things the prune reads from a CallRecord: id and function."""

    def __init__(self, call_id: str, function: str, args=None):
        self.id = call_id
        self.function = function
        self.args = args or []
        # An AxesRecord is read by referenced_call_ids as both halves.
        self.calls: list = []
        self.decorations: list = []


def _save(fig, path):
    """Save with warnings captured; returns (lifecycle warnings, yaml path)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _, yml, _ = fr.save(fig, path, validate=False, verbose=False)
    lifecycle = [w for w in caught if issubclass(w.category, ArtistLifecycleWarning)]
    return lifecycle, Path(yml)


def _recipe(yml):
    """(calls, decorations) function names per axes, from the written recipe."""
    data = yaml.safe_load(Path(yml).read_text())
    out = {}
    for key, axrec in (data.get("axes") or {}).items():
        out[key] = (
            [c["function"] for c in (axrec.get("calls") or [])],
            [d["function"] for d in (axrec.get("decorations") or [])],
        )
    return out


def _record_functions(fig):
    """The same fingerprint as :func:`_recipe`, read off the LIVE record."""
    return {
        key: (
            [c.function for c in axrec.calls],
            [d.function for d in axrec.decorations],
        )
        for key, axrec in fig.record.axes.items()
    }


class TestWhichObjectsAreArtists:
    """The registry must never hold data, or a numpy array would read as an
    artist that "left the figure" and the call behind it would be dropped."""

    def test_a_line_is_an_artist(self):
        # Arrange
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        # Act
        artists = flatten_artists(line)
        # Assert
        assert artists == [line]

    def test_a_numpy_array_is_not_an_artist(self):
        # Arrange -- plot() hands back data arrays in other shapes; only the
        # artists may be registered.
        data = np.arange(3.0)
        # Act
        artists = flatten_artists(data)
        # Assert
        assert artists == []

    def test_every_artist_inside_a_container_is_registered(self):
        # Arrange -- ax.errorbar() returns an ErrorbarContainer (a tuple) whose
        # parts are artists; iterating only the top level would register none.
        fig, ax = fr.subplots()
        container = ax.errorbar([1, 2], [1, 2], yerr=[0.1, 0.1])
        # Act
        artists = flatten_artists(container)
        # Assert -- more than the container itself: its lines and collections.
        assert len(artists) > 1


class TestLivenessDecision:
    def test_a_kept_artist_is_not_gone(self):
        # Arrange
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        registry: dict = {}
        note_call_artists(registry, "plot", "c", line)
        # Act
        gone = call_is_gone(registry["c"], live_artist_ids(fig))
        # Assert
        assert gone is False

    def test_a_removed_artist_is_gone(self):
        # Arrange
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        note_call_artists({}, "plot", "c", line)
        line.remove()
        # Act
        gone = call_is_gone([weakref.ref(line)], live_artist_ids(fig))
        # Assert
        assert gone is True

    def test_an_invisible_artist_is_still_on_the_figure(self):
        # Arrange -- set_visible(False) is NOT a removal: the artist is still the
        # axes' business and the call behind it still holds real data.
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        line.set_visible(False)
        note_call_artists({}, "plot", "c", line)
        # Act
        gone = call_is_gone([weakref.ref(line)], live_artist_ids(fig))
        # Assert
        assert gone is False

    def test_a_call_that_lost_only_one_of_two_artists_is_not_gone(self):
        # Arrange -- the record cannot express half a call, so a wrong "gone"
        # here would delete data from the recipe.
        fig, ax = fr.subplots()
        lines = ax.plot([1, 2], [1, 2], [3, 4])
        lines[0].remove()
        # Act
        gone = call_is_gone(
            [weakref.ref(x) for x in lines], live_artist_ids(fig)
        )
        # Assert
        assert gone is False


class TestRegistration:
    def test_a_method_outside_the_vocabulary_is_not_registered(self):
        # Arrange -- set_title() -> a Title the NEXT set_title() replaces; that is
        # last-write-wins, not a removal.
        fig, ax = fr.subplots()
        title = ax.set_title("t")
        registry = {}
        # Act
        note_call_artists(registry, "set_title", "c", title)
        # Assert
        assert registry == {}

    def test_a_non_artist_result_is_not_registered(self):
        # Arrange
        registry = {}
        # Act
        note_call_artists(registry, "plot", "c", "not an artist")
        # Assert
        assert registry == {}

    def test_an_unattached_artist_is_not_registered(self):
        # Arrange -- a wrapper returning something the axes never took must not
        # make its own call look removable.
        registry = {}
        loose = Text(x=0, y=0, text="loose")
        # Act
        note_call_artists(registry, "text", "c", loose)
        # Assert
        assert registry == {}

    def test_a_plot_call_is_registered_weakly(self):
        # Arrange
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        registry = {}
        # Act
        note_call_artists(registry, "plot", "c", line)
        # Assert -- a weakref, so the registry can never keep the artist alive.
        assert registry["c"][0]() is line


class TestThePruneDecision:
    def test_a_call_whose_artists_are_gone_is_dropped(self):
        # Arrange
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        registry = {}
        note_call_artists(registry, "plot", "c", line)
        line.remove()
        # Act
        kept, dropped = prune(
            [FakeRecord("c", "plot")], registry, live_artist_ids(fig), set(), "r0c0", "calls"
        )
        # Assert
        assert kept == [] and [d.call_id for d in dropped] == ["c"]

    def test_a_referenced_call_is_kept_even_when_its_artists_are_gone(self):
        # Arrange -- contour -> clabel: dropping the referenced call would turn a
        # faithful recipe into an unreplayable one.
        fig, ax = fr.subplots()
        (line,) = ax.plot([1, 2], [1, 2])
        registry = {}
        note_call_artists(registry, "plot", "c", line)
        line.remove()
        # Act
        kept, _ = prune(
            [FakeRecord("c", "plot")],
            registry,
            live_artist_ids(fig),
            {"c"},
            "r0c0",
            "calls",
        )
        # Assert
        assert [r.id for r in kept] == ["c"]

    def test_a_call_with_no_registry_entry_is_kept(self):
        # Arrange -- an unregistered path (bar, boxplot, legend) is simply not
        # this slice's business: no evidence, no drop.
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])
        # Act
        kept, _ = prune(
            [FakeRecord("c", "bar")], {}, live_artist_ids(fig), set(), "r0c0", "calls"
        )
        # Assert
        assert [r.id for r in kept] == ["c"]


class TestReferencedIds:
    def test_an_axes_with_no_ref_arguments_contributes_nothing(self):
        # Arrange -- an axes whose records carry no {"__ref__": ...} at all.
        # Act
        referenced = referenced_call_ids([FakeRecord("ax", "x")])
        # Assert
        assert referenced == set()

    def test_ref_arguments_are_collected_from_both_halves(self):
        # Arrange
        axes = FakeRecord("ax", "x")
        axes.calls = [FakeRecord("c", "clabel", args=[{"__ref__": "contour_1"}])]
        axes.decorations = [FakeRecord("d", "clabel", args=[{"__ref__": "contour_2"}])]
        # Act
        referenced = referenced_call_ids([axes])
        # Assert
        assert referenced == {"contour_1", "contour_2"}


class TestModuleHygiene:
    def test_the_module_stays_dependency_free(self):
        # Arrange
        module = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "figrecipe"
            / "_recorder"
            / "_artists.py"
        )
        # Act
        text = module.read_text(encoding="utf-8")
        # Assert -- it must run under the repo's expression tests.
        assert "import matplotlib" not in text and "from figrecipe" not in text


class TestTheSavePathRepairsTheHeadlineCase:
    """The card's own case, driven through a REAL fr.save."""

    @staticmethod
    def _headline_text_removed(tmp_path, name):
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        drawn = ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        drawn.remove()
        return _save(fig, tmp_path / name)

    @staticmethod
    def _headline_text_kept(tmp_path, name):
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        return _save(fig, tmp_path / name)

    def test_the_removed_text_is_no_longer_claimed_by_the_recipe(self, tmp_path):
        # Arrange
        name = "a.png"
        # Act
        _, yml = self._headline_text_removed(tmp_path, name)
        # Assert -- the decoration that the PNG does not show is gone.
        assert _recipe(yml)["r0c0"] == (["plot"], [])

    def test_the_save_reports_the_repair_rather_than_doing_it_silently(self, tmp_path):
        # Arrange
        name = "b.png"
        # Act
        lifecycle, _ = self._headline_text_removed(tmp_path, name)
        # Assert -- exactly one warning, and it is the repair's own message.
        assert len(lifecycle) == 1 and "dropped 1 recorded call" in str(
            lifecycle[0].message
        )

    def test_the_saved_figure_now_validates(self, tmp_path):
        # Arrange -- the whole point: a CORRECT figure was being rejected.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        drawn = ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        drawn.remove()
        png, yml, _ = fr.save(fig, tmp_path / "c.png", validate=False, verbose=False)
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert -- was MSE 353.09 and invalid before the repair.
        assert result.mse == 0.0 and result.valid

    def test_a_still_shown_text_keeps_its_record_and_stays_quiet(self, tmp_path):
        # Arrange
        name = "d.png"
        # Act
        lifecycle, yml = self._headline_text_kept(tmp_path, name)
        # Assert -- the false-positive control: no warning, record untouched.
        assert lifecycle == [] and _recipe(yml)["r0c0"] == (["plot"], ["text"])


class TestTheSavePathRepairsOtherPlotters:
    def test_a_removed_vlines_collection_is_dropped_and_the_save_validates(
        self, tmp_path
    ):
        # Arrange -- the sub-threshold case: base measured MSE 48.72, VALID, so
        # the pixel validator never caught it.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        ruled = ax.vlines([1, 2], 0, 1, color="red")
        ax.plot([1, 2, 3], [3, 2, 1], id="m")
        fig.canvas.draw()
        ruled.remove()
        png, yml, _ = fr.save(fig, tmp_path / "e.png", validate=False, verbose=False)
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert
        assert result.mse == 0.0 and _recipe(yml)["r0c0"] == (["plot", "plot"], [])

    def test_a_removed_line_leaves_no_sidecar_data_behind(self, tmp_path):
        # Arrange -- a half-save (image without its data) is its own defect class.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 2, 3], id="keep")
        (doomed,) = ax.plot([1, 2, 3], [3, 2, 1], id="drop")
        doomed.remove()
        # Act
        _save(fig, tmp_path / "f.png")
        # Assert
        assert sorted(p.name for p in (tmp_path / "f_data").glob("*.csv")) == [
            "keep_x.csv",
            "keep_y.csv",
        ]


class TestNothingElseMoves:
    """The controls that make the repair safe to ship."""

    def test_an_invisible_artist_keeps_its_record(self, tmp_path):
        # Arrange -- the divergence is real but it is NOT a removal; dropping the
        # call would delete a series the user may toggle back on.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="a")
        (hidden,) = ax.plot([1, 2, 3], [2, 3, 4], id="b")
        fig.canvas.draw()
        hidden.set_visible(False)
        # Act
        lifecycle, yml = _save(fig, tmp_path / "g.png")
        # Assert
        assert _recipe(yml)["r0c0"] == (["plot", "plot"], []) and lifecycle == []

    def test_a_call_that_kept_one_artist_keeps_its_record(self, tmp_path):
        # Arrange -- two artists from one call, one removed: expressible in the
        # record only as "both", so the record must stay as it is.
        fig, ax = fr.subplots()
        lines = ax.plot([1, 2, 3], [1, 4, 9], [2, 3, 4], id="a")
        fig.canvas.draw()
        lines[0].remove()
        # Act
        _, yml = _save(fig, tmp_path / "h.png")
        # Assert
        assert _recipe(yml)["r0c0"] == (["plot"], [])

    def test_a_faithful_figure_keeps_every_call_it_recorded(self, tmp_path):
        # Arrange -- the no-removal control, over a figure using both halves.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="a")
        ax.axhline(2, color="grey")
        ax.text(0.5, 0.75, "fine", transform=ax.transAxes)
        ax.vlines([1, 2], 0, 1)
        before = _record_functions(fig)
        # Act
        lifecycle, yml = _save(fig, tmp_path / "i.png")
        # Assert
        assert _recipe(yml) == before and lifecycle == []


# What the repair cannot reach (ax.bar() and the other paths that record outside
# the artist funnel) is covered by the count check's own wiring test in
# test__lifecycle.py::TestSavePathWiring: the two layers are complementary, and
# each is asserted where it lives.
