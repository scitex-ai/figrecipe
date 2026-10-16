#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""An artist HIDDEN after being drawn must not be re-drawn by the recipe.

Card figrecipe-hidden-artist-set-visible-false-not-recorded-20260927, split out of
figrecipe-recipe-keeps-artists-removed-before-save-20260906 (sweep root cause 2:
state mutated on the handle after the call).

A figure that draws a series and then hides it saved a recipe that draws it: the
record holds the call as it was made, so the replay shows an artist the PNG does
not, and the DEFAULT save path RAISES (measured 406.02, 1.8% of pixels changed).
The repair writes the artist's FINAL visibility into the recorded call instead of
dropping it -- a hidden artist still carries the user's data and can be shown
again, so the call must stay and only its paint state is written down.

Two properties matter equally and both are asserted below:
  * the failing cases become faithful (MSE 0.00 from a REAL save, including the
    sub-threshold ones the pixel validator never caught), and
  * NOTHING ELSE MOVES -- a figure with nothing hidden comes out of the save with
    exactly the recipe it had, and a REMOVED artist is still dropped rather than
    hidden, because that is the sibling repair's job and not this one's.

Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import warnings
from pathlib import Path
from weakref import ref as weak_ref

import matplotlib

matplotlib.use("Agg")  # before figrecipe: the save path renders

import yaml  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._quality._validator import validate_on_save  # noqa: E402
from figrecipe._recorder._lifecycle import ARTIST_METHODS  # noqa: E402
from figrecipe._recorder._visibility import (  # noqa: E402
    annotate_hidden,
    call_is_hidden,
    module_level_imports,
    replay_accepts_visible,
)


class FakeRecord:
    """The only things the annotate reads from a CallRecord."""

    def __init__(self, call_id: str, function: str, kwargs=None):
        self.id = call_id
        self.function = function
        self.kwargs = dict(kwargs or {})


class _Unreadable:
    """An object that claims to be an artist but cannot answer get_visible()."""

    def __init__(self):
        self.children: list = []

    def get_children(self):
        return self.children


def _fig_with_line(visible: bool = True):
    """A one-line figure whose line is hidden or shown, plus that line."""
    fig, ax = fr.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9], id="l")
    fig.canvas.draw()
    line.set_visible(visible)
    return fig, line


def _save(fig, path):
    """Save without validation and return the written recipe's (png, yaml)."""
    png, yml, _ = fr.save(fig, path, validate=False, verbose=False)
    return png, Path(yml)


def _visible_kwargs(yml):
    """Every ``visible`` value the written recipe carries, calls + decorations."""
    data = yaml.safe_load(Path(yml).read_text())
    out = []
    for axrec in (data.get("axes") or {}).values():
        for entry in list(axrec.get("calls") or []) + list(axrec.get("decorations") or []):
            if "visible" in (entry.get("kwargs") or {}):
                out.append(entry["kwargs"]["visible"])
    return out


def _functions(yml):
    """Function names per axes, from the written recipe."""
    data = yaml.safe_load(Path(yml).read_text())
    return {
        key: (
            [c["function"] for c in (axrec.get("calls") or [])],
            [d["function"] for d in (axrec.get("decorations") or [])],
        )
        for key, axrec in (data.get("axes") or {}).items()
    }


class TestTheHiddenDecision:
    """Anything short of "every artist, live, hidden" must not write to a record."""

    def test_a_hidden_artist_that_is_on_the_figure_is_hidden(self):
        # Arrange
        fig, line = _fig_with_line(visible=False)
        from figrecipe._recorder._artists import live_artist_ids

        # Act
        hidden = call_is_hidden([weak_ref(line)], live_artist_ids(fig))
        # Assert
        assert hidden is True

    def test_a_shown_artist_is_not_hidden(self):
        # Arrange
        fig, line = _fig_with_line(visible=True)
        from figrecipe._recorder._artists import live_artist_ids

        # Act
        hidden = call_is_hidden([weak_ref(line)], live_artist_ids(fig))
        # Assert
        assert hidden is False

    def test_an_artist_not_on_the_figure_is_not_hidden(self):
        # Arrange -- this is the REMOVAL case: the sibling repair drops that call,
        # and a ``visible: false`` here would hide what was already gone.
        fig, line = _fig_with_line(visible=False)
        from figrecipe._recorder._artists import live_artist_ids

        line.remove()
        live = live_artist_ids(fig)
        # Act
        hidden = call_is_hidden([weak_ref(line)], live)
        # Assert
        assert hidden is False

    def test_a_released_artist_is_not_hidden(self):
        # Arrange -- a weakref that has died is evidence the artist left, not
        # that it is invisible.
        odd = Line2D([], [])
        dead = weak_ref(odd)
        del odd
        # Act
        hidden = call_is_hidden([dead], set())
        # Assert
        assert hidden is False

    def test_an_artist_that_cannot_report_visibility_is_not_hidden(self):
        # Arrange -- no evidence must never become "hidden", because the answer
        # is a write to the user's own recipe.
        unreadable = _Unreadable()
        # Act
        hidden = call_is_hidden([weak_ref(unreadable)], {id(unreadable)})
        # Assert
        assert hidden is False

    def test_a_call_with_nothing_registered_is_not_hidden(self):
        # Arrange -- an older record, or one whose artists were never attached.
        # Act
        hidden = call_is_hidden(None, set())
        # Assert
        assert hidden is False

    def test_a_partly_hidden_call_is_not_hidden(self):
        # Arrange -- one ``visible`` value cannot describe a call that left one
        # artist painted and hid another.
        fig, ax = fr.subplots()
        lines = ax.plot([1, 2, 3], [1, 4, 9], [2, 3, 4], id="both")
        fig.canvas.draw()
        lines[1].set_visible(False)
        from figrecipe._recorder._artists import live_artist_ids

        # Act
        hidden = call_is_hidden([weak_ref(x) for x in lines], live_artist_ids(fig))
        # Assert
        assert hidden is False


class TestWhichReplaysHonourVisibility:
    """The annotatable set is DERIVED, so it cannot drift from what replays."""

    def test_a_plain_plotter_is_annotatable(self):
        # Arrange -- the reproducer replays it as getattr(ax, "plot")(**kwargs).
        # Act
        accepted = replay_accepts_visible("plot")
        # Assert
        assert accepted is True

    def test_a_decorating_plotter_is_annotatable(self):
        # Arrange -- ax.text() is a DECORATION that creates its own artist, so a
        # hidden text is the same divergence as a hidden line.
        # Act
        accepted = replay_accepts_visible("text")
        # Assert
        assert accepted is True

    def test_a_method_with_a_closed_signature_is_refused(self):
        # Arrange -- measured: matplotlib's Axes.pie() takes no **kwargs, so a
        # visible kwarg would make the recipe unreplayable.
        # Act
        accepted = replay_accepts_visible("pie")
        # Assert
        assert accepted is False

    def test_a_special_handled_method_is_refused(self):
        # Arrange -- measured: boxplot/graph/stem/violinplot are replayed by the
        # dispatcher's own handler, on a kwargs path this slice does not own.
        # Act
        accepted = replay_accepts_visible("boxplot")
        # Assert
        assert accepted is False

    def test_every_registered_method_is_still_classified(self):
        # Arrange -- the derived guard must not shrink the vocabulary silently:
        # pie and streamplot are the closed signatures, these four are handled.
        # Act
        refused = sorted(n for n in ARTIST_METHODS if not replay_accepts_visible(n))
        # Assert
        assert refused == ["boxplot", "graph", "pie", "stem", "streamplot", "violinplot"]


class TestTheAnnotationDecision:
    def test_a_hidden_call_gains_the_visible_kwarg(self):
        # Arrange
        record = FakeRecord("l", "plot", {"color": "red"})
        registry: dict = {}
        line = Line2D([1], [1])
        line.set_visible(False)
        registry[id(record)] = (record, [weak_ref(line)])
        # Act
        annotate_hidden([record], registry, {id(line)}, "r0c0", "calls")
        # Assert
        assert record.kwargs["visible"] is False and record.kwargs["color"] == "red"

    def test_a_hidden_call_is_reported_by_name(self):
        # Arrange -- the caller gets back what changed, not only that something did.
        record = FakeRecord("l", "plot")
        registry: dict = {}
        line = Line2D([1], [1])
        line.set_visible(False)
        registry[id(record)] = (record, [weak_ref(line)])
        # Act
        annotated = annotate_hidden([record], registry, {id(line)}, "r0c0", "calls")
        # Assert
        assert str(annotated[0]) == "plot(l)" and annotated[0].half == "calls"

    def test_a_record_that_already_says_hidden_is_not_rewritten(self):
        # Arrange -- the user passed visible=False themselves; rewriting it would
        # report a change that did not happen.
        record = FakeRecord("l", "plot", {"visible": False})
        registry: dict = {}
        line = Line2D([1], [1])
        line.set_visible(False)
        registry[id(record)] = (record, [weak_ref(line)])
        # Act
        annotated = annotate_hidden([record], registry, {id(line)}, "r0c0", "calls")
        # Assert
        assert annotated == []

    def test_a_shown_call_keeps_its_kwargs(self):
        # Arrange -- the false-positive control: an ordinary figure is untouched.
        record = FakeRecord("l", "plot", {"color": "red"})
        registry: dict = {}
        line = Line2D([1], [1])
        registry[id(record)] = (record, [weak_ref(line)])
        # Act
        annotate_hidden([record], registry, {id(line)}, "r0c0", "calls")
        # Assert
        assert record.kwargs == {"color": "red"}

    def test_a_call_with_no_registry_entry_is_not_annotated(self):
        # Arrange -- nothing is written on a guess.
        record = FakeRecord("l", "plot")
        # Act
        annotated = annotate_hidden([record], {}, {0}, "r0c0", "calls")
        # Assert
        assert annotated == []

    def test_a_method_whose_replay_would_reject_the_kwarg_is_not_annotated(self):
        # Arrange -- a recipe that no longer replays is worse than one that draws
        # a hidden artist, so an unrepresentable call keeps its record as it is.
        record = FakeRecord("p", "pie")
        registry: dict = {}
        wedge = Line2D([1], [1])
        wedge.set_visible(False)
        registry[id(record)] = (record, [weak_ref(wedge)])
        # Act
        annotate_hidden([record], registry, {id(wedge)}, "r0c0", "calls")
        # Assert
        assert record.kwargs == {}


class TestTheSavePathWritesTheFinalVisibility:
    """The card's own case, driven through a REAL fr.save."""

    def test_the_hidden_line_is_no_longer_drawn_by_the_recipe(self, tmp_path):
        # Arrange
        fig, _ = _fig_with_line(visible=False)
        # Act
        _, yml = _save(fig, tmp_path / "a.png")
        # Assert
        assert _visible_kwargs(yml) == [False]

    def test_the_saved_figure_now_validates(self, tmp_path):
        # Arrange -- the whole point: a CORRECT figure was being rejected.
        fig, _ = _fig_with_line(visible=False)
        png, yml = _save(fig, tmp_path / "b.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert -- was MSE 406.02 and invalid before the repair.
        assert result.mse == 0.0 and result.valid

    def test_the_hidden_line_still_exists_in_the_replay(self, tmp_path):
        # Arrange -- the data behind the series must survive: hiding asks not to
        # PAINT an artist, not to forget it, and it can be toggled back on.
        fig, _ = _fig_with_line(visible=False)
        png, _ = _save(fig, tmp_path / "c.png")
        # Act
        _, ax = fr.reproduce(png)
        # Assert
        assert len(ax.lines) == 1 and ax.lines[0].get_visible() is False

    def test_a_sub_threshold_hidden_collection_now_validates(self, tmp_path):
        # Arrange -- the case the pixel validator could never catch: base
        # measured MSE 48.72 and VALID while the recipe still drew the collection.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        ruled = ax.vlines([1, 2], 0, 1, color="red")
        fig.canvas.draw()
        ruled.set_visible(False)
        png, yml = _save(fig, tmp_path / "d.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert
        assert result.mse == 0.0 and _visible_kwargs(yml) == [False]

    def test_a_hidden_decoration_is_annotated_too(self, tmp_path):
        # Arrange -- ax.text() is recorded in the OTHER half of the axes record.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        drawn = ax.text(0.5, 0.75, "PROBE", transform=ax.transAxes, fontsize=14)
        fig.canvas.draw()
        drawn.set_visible(False)
        png, yml = _save(fig, tmp_path / "e.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert -- was MSE 353.09 and invalid.
        assert result.mse == 0.0 and _visible_kwargs(yml) == [False]

    def test_a_hidden_fill_between_now_validates(self, tmp_path):
        # Arrange -- a filled region is a Collection, still the same divergence.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="l")
        filled = ax.fill_between([1, 2, 3], [1, 4, 9], [0, 0, 0], id="f")
        fig.canvas.draw()
        filled.set_visible(False)
        png, yml = _save(fig, tmp_path / "l.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert -- was MSE 2362.62 and invalid.
        assert result.mse == 0.0 and _visible_kwargs(yml) == [False]

    def test_a_call_that_hid_only_one_of_its_artists_is_left_alone(self, tmp_path):
        # Arrange -- an errorbar's line hidden while its cap lines stay visible:
        # one ``visible`` value cannot describe that, so the record stays as it
        # is (measured MSE 387.38, unchanged, and unchanged is the honest answer).
        fig, ax = fr.subplots()
        erred = ax.errorbar([1, 2, 3], [1, 4, 9], yerr=[0.1, 0.2, 0.1], id="e")
        fig.canvas.draw()
        erred.lines[0].set_visible(False)
        # Act
        _, yml = _save(fig, tmp_path / "m.png")
        # Assert
        assert _visible_kwargs(yml) == []

    def test_the_default_save_path_no_longer_raises(self, tmp_path):
        # Arrange -- the card's headline symptom was an ERROR on a correct figure.
        fig, _ = _fig_with_line(visible=False)
        # Act
        png, yml, _ = fr.save(fig, tmp_path / "f.png", verbose=False)
        # Assert
        assert Path(png).exists() and Path(yml).exists()


class TestCallsRecordedOutsideTheArtistFunnel:
    """bar/imshow record outside the funnel, so they must note their own artists.

    Card figrecipe-hidden-bar-imshow-not-registered-in-artist-funnel-20260927:
    ``bar_plot`` / ``imshow_plot`` call ``recorder.record_call`` directly instead
    of ``record_call_with_color_capture``, so the one funnel that calls
    ``note_call_artists`` never saw their BarContainer/AxesImage -- no registry
    entry, so ``call_is_hidden`` was never reached and a hidden bar/imshow
    replayed drawn (measured 9129.84 / 23248.60). Each case below fails before
    the repair and passes after it, driven through a REAL fr.save.
    """

    def test_a_hidden_bar_now_validates(self, tmp_path):
        # Arrange -- the card's own bar case (was MSE 9129.84, invalid).
        fig, ax = fr.subplots()
        bars = ax.bar([1, 2, 3], [1, 4, 9], id="b")
        fig.canvas.draw()
        for patch in bars:
            patch.set_visible(False)
        png, yml = _save(fig, tmp_path / "bar.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert
        assert result.mse == 0.0 and result.valid

    def test_a_hidden_imshow_now_validates(self, tmp_path):
        # Arrange -- the card's own imshow case (was MSE 23248.60, invalid).
        import numpy as np

        fig, ax = fr.subplots()
        image = ax.imshow(np.arange(16).reshape(4, 4), id="i")
        fig.canvas.draw()
        image.set_visible(False)
        png, yml = _save(fig, tmp_path / "imshow.png")
        # Act
        result = validate_on_save(fig, yml, mse_threshold=100.0, image_path=png)
        # Assert
        assert result.mse == 0.0 and result.valid

    def test_a_hidden_bar_writes_visible_false(self, tmp_path):
        # Arrange
        fig, ax = fr.subplots()
        bars = ax.bar([1, 2, 3], [1, 4, 9], id="b")
        fig.canvas.draw()
        for patch in bars:
            patch.set_visible(False)
        # Act
        _, yml = _save(fig, tmp_path / "bar2.png")
        # Assert
        assert _visible_kwargs(yml) == [False]

    def test_a_hidden_imshow_writes_visible_false(self, tmp_path):
        # Arrange
        import numpy as np

        fig, ax = fr.subplots()
        image = ax.imshow(np.arange(16).reshape(4, 4), id="i")
        fig.canvas.draw()
        image.set_visible(False)
        # Act
        _, yml = _save(fig, tmp_path / "imshow2.png")
        # Assert
        assert _visible_kwargs(yml) == [False]

    def test_the_hidden_bar_patches_still_exist_in_the_replay(self, tmp_path):
        # Arrange -- the data must survive: hiding asks not to PAINT, not to forget.
        fig, ax = fr.subplots()
        bars = ax.bar([1, 2, 3], [1, 4, 9], id="b")
        fig.canvas.draw()
        for patch in bars:
            patch.set_visible(False)
        png, _ = _save(fig, tmp_path / "bar3.png")
        # Act
        _, ax2 = fr.reproduce(png)
        # Assert
        assert len(ax2.patches) == 3 and all(not p.get_visible() for p in ax2.patches)

    def test_the_hidden_imshow_image_still_exists_in_the_replay(self, tmp_path):
        # Arrange
        import numpy as np

        fig, ax = fr.subplots()
        image = ax.imshow(np.arange(16).reshape(4, 4), id="i")
        fig.canvas.draw()
        image.set_visible(False)
        png, _ = _save(fig, tmp_path / "imshow3.png")
        # Act
        _, ax2 = fr.reproduce(png)
        images = [c for c in ax2.get_children() if type(c).__name__ == "AxesImage"]
        # Assert
        assert len(images) == 1 and images[0].get_visible() is False

    def test_a_shown_bar_gains_no_visible_kwarg(self, tmp_path):
        # Arrange -- the control: a drawn-and-shown bar must be untouched.
        fig, ax = fr.subplots()
        ax.bar([1, 2, 3], [1, 4, 9], id="b")
        # Act
        _, yml = _save(fig, tmp_path / "bar4.png")
        # Assert
        assert _visible_kwargs(yml) == []

    def test_a_shown_imshow_gains_no_visible_kwarg(self, tmp_path):
        # Arrange -- the control: a drawn-and-shown imshow must be untouched.
        import numpy as np

        fig, ax = fr.subplots()
        ax.imshow(np.arange(16).reshape(4, 4), id="i")
        # Act
        _, yml = _save(fig, tmp_path / "imshow4.png")
        # Assert
        assert _visible_kwargs(yml) == []

    def test_a_shown_bar_keeps_its_recorded_call(self, tmp_path):
        # Arrange -- nothing is dropped for the outside-funnel methods either.
        fig, ax = fr.subplots()
        ax.bar([1, 2, 3], [1, 4, 9], id="b")
        before = {
            key: ([c.function for c in rec.calls], [d.function for d in rec.decorations])
            for key, rec in fig.record.axes.items()
        }
        # Act
        _, yml = _save(fig, tmp_path / "bar5.png")
        # Assert
        assert _functions(yml) == before


class TestNothingElseMoves:
    """The controls that make the annotation safe to ship."""

    def test_a_shown_figure_gains_no_visible_kwarg(self, tmp_path):
        # Arrange
        fig, _ = _fig_with_line(visible=True)
        # Act
        _, yml = _save(fig, tmp_path / "g.png")
        # Assert
        assert _visible_kwargs(yml) == []

    def test_a_shown_figure_keeps_every_call_it_recorded(self, tmp_path):
        # Arrange -- the no-op control, over a figure using both halves.
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], id="a")
        ax.axhline(2, color="grey")
        ax.text(0.5, 0.75, "fine", transform=ax.transAxes)
        ax.vlines([1, 2], 0, 1)
        before = {
            key: ([c.function for c in rec.calls], [d.function for d in rec.decorations])
            for key, rec in fig.record.axes.items()
        }
        # Act
        _, yml = _save(fig, tmp_path / "h.png")
        # Assert
        assert _functions(yml) == before and _visible_kwargs(yml) == []

    def test_hiding_then_showing_leaves_the_record_alone(self, tmp_path):
        # Arrange -- the net live state is what the recipe describes, so a series
        # that is visible again must not be written down as hidden.
        fig, line = _fig_with_line(visible=True)
        line.set_visible(False)
        line.set_visible(True)
        # Act
        _, yml = _save(fig, tmp_path / "i.png")
        # Assert
        assert _visible_kwargs(yml) == []

    def test_a_removed_artist_is_still_dropped_rather_than_hidden(self, tmp_path):
        # Arrange -- the sibling repair's case: the artist is off the figure, so
        # its call goes; hiding it instead would leave the recipe drawing it.
        fig, _ = _fig_with_line(visible=True)
        # Act
        _, yml = _save(fig, tmp_path / "j.png")
        # Assert -- one call, and no visibility was invented for it.
        assert _functions(yml) == {"r0c0": (["plot"], [])} and _visible_kwargs(yml) == []

    def test_the_annotation_keeps_the_save_free_of_extra_warnings(self, tmp_path):
        # Arrange -- hiding a series is deliberate, so the repair reports nothing;
        # a warning per hidden artist would train users to ignore the one the
        # removal repair raises for a recipe that LOST data.
        fig, _ = _fig_with_line(visible=False)
        fig.canvas.draw()
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _save(fig, tmp_path / "k.png")
        # Assert
        assert [w for w in caught if "figrecipe:" in str(w.message)] == []


class TestModuleHygiene:
    def test_the_module_imports_no_matplotlib_at_module_level(self):
        # Arrange
        module = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "figrecipe"
            / "_recorder"
            / "_visibility.py"
        )
        # Act
        names = module_level_imports(module.read_text(encoding="utf-8"))
        # Assert -- the decision functions must run under the expression tests.
        assert "matplotlib" not in names
