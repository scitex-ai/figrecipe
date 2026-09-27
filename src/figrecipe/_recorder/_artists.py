#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which of a call's artists is the figure still showing? (save-time reconcile)

Card figrecipe-recipe-keeps-artists-removed-before-save-20260906, REPAIR slice.

The defect: a call is recorded, then its artist is removed from the figure
before save. The record keeps the call, so a replay draws what the saved PNG
does not show -- and reproducibility validation then rejects a figure that is
CORRECT (measured MSE 353.09 for the card's own headline case). The detection
slice (`_lifecycle.py`, merged) reports the divergence at save time; this module
is the part that removes the CAUSE: at save time the record is reconciled to the
artists the live figure actually holds.

What is dropped, and why it is safe to drop only that:

* A record is dropped only when EVERY artist the call created is provably off
  the figure -- ``Artist.remove()`` or ``ax.cla()``. A call that made several
  artists and lost only some of them is KEPT: the record cannot express "half of
  this call", and a wrong drop would delete data from the recipe.
* A record is dropped only when its call id is not referenced by a surviving
  record (``{"__ref__": ...}``, the ``contour`` -> ``clabel`` path): dropping a
  referenced call would turn a faithful recipe into an unreplayable one.
* Only methods in :data:`ARTIST_METHODS` are watched. Those are the calls whose
  artist the axes is expected to still hold -- the assertion being honoured.
  Outside that vocabulary a later call legitimately replaces the earlier artist
  (``set_title`` twice, ``legend`` then a new ``legend``), and dropping the
  superseded record is neither needed nor wanted.
* An artist is recorded only while it is ATTACHED to a figure at call time
  (``get_figure() is not None``), so a wrapper returning something the axes
  never took cannot make its own call look removable.

Both "is it gone?" signals were MEASURED on matplotlib 3.11.1 rather than
assumed (probe in the session scratchpad; results in the PR body):

    event                    in ax.get_children()   artist.get_figure()
    untouched                yes                    not None
    .remove()                no                     None
    ax.cla()                 no                     None
    set_visible(False)       yes                    not None   <- NOT a removal

``set_visible(False)`` is deliberately not a removal: the artist is still on the
figure, the user asked only that it not be painted, and deleting the call would
delete the DATA behind a series a user may toggle back on. That divergence (the
PNG hides an artist the recipe still draws) is the count-based detector's
separate, still-open gap.

No matplotlib import: the artist test is duck-typed and the caller passes plain
counts/identity sets, so this module still runs under the repo's expression
tests, like its sibling :mod:`figrecipe._recorder._lifecycle`.
"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)
from weakref import ref as _weakref

from ._lifecycle import ARTIST_METHODS

#: How deep :func:`flatten_artists` walks a nested result. ``errorbar`` returns
#: (line, caplines, barlinecols), ``hist`` a (counts, bins, patches) tuple whose
#: patches are a BarContainer -- three levels is generous, and the bound keeps a
#: pathological result from costing a save.
_MAX_DEPTH = 3


def _is_artist(obj: Any) -> bool:
    """Duck-typed ``matplotlib.artist.Artist`` test -- no matplotlib import.

    Measured on 3.11.1: every Artist (Line2D, Text, Patch, Collection,
    AxesImage, Axes, and the BarContainer/ErrorbarContainer tuple subclasses)
    has ``get_children``; a numpy array or scalar does not. That is exactly the
    discrimination needed -- a data array must never enter the registry, or the
    reconcile would read it as an artist that has left the figure.
    """
    return hasattr(obj, "get_children")


def flatten_artists(result: Any, _depth: int = 0) -> List[Any]:
    """Every Artist a recording call's return value accounts for.

    Recurses into ``list``/``tuple``/``set`` ONLY -- matplotlib's containers
    (``BarContainer``, ``ErrorbarContainer``) are tuple subclasses, while a
    numpy array is data, and iterating one would register thousands of numbers.
    """
    if result is None or _depth > _MAX_DEPTH:
        return []
    if isinstance(result, (list, tuple, set, frozenset)):
        out: List[Any] = []
        for item in result:
            out.extend(flatten_artists(item, _depth + 1))
        return out
    return [result] if _is_artist(result) else []


def _attached(artist: Any) -> bool:
    """True when the artist is on a figure right now (best-effort)."""
    try:
        return artist.get_figure() is not None
    except Exception:
        return False


def note_call_artists(
    registry: Optional[Dict[int, tuple]],
    method_name: str,
    record: Any,
    result: Any,
) -> None:
    """Remember, weakly, which artists a recorded call created.

    Called from ``_wrappers/_axes_helpers.py::record_call_with_color_capture`` --
    the one funnel every recorded method passes through with its live result, and
    the same site that already stores ``result_refs``.

    The artists are held WEAKLY: a registry entry must never be the reason an
    artist outlives its figure, and a released artist is itself evidence that
    nothing on the figure holds it any more.

    Keyed by the RECORD's identity, not by ``record.id``: a recorded id is the
    user's own ``id=`` kwarg whenever they pass one, so two calls can share it
    and a later call's entry would OVERWRITE the earlier call's -- silently
    disabling the drop for exactly the "remove it, then re-plot under the same
    id" case this repair exists for (measured: the removed call stayed in the
    recipe). The record itself is held in the entry, so its address cannot be
    reused while the entry lives.
    """
    if registry is None or method_name not in ARTIST_METHODS:
        return
    refs: List[Any] = []
    for artist in flatten_artists(result):
        if not _attached(artist):
            continue  # never on a figure: its call is not ours to drop
        try:
            refs.append(_weakref(artist))
        except TypeError:
            continue  # not weak-referenceable -> unrepresentable, so KEEP the call
    if refs:
        registry[id(record)] = (record, refs)


def noted_artists(registry: Optional[Dict[int, tuple]], record: Any) -> Optional[list]:
    """The artist weakrefs noted for ``record``, or None when it was not noted."""
    if not registry:
        return None
    entry = registry.get(id(record))
    return entry[1] if entry else None


def call_is_gone(refs: Optional[Sequence[Any]], live_ids: Set[int]) -> bool:
    """True when NO artist this call created is still on the figure.

    ``live_ids`` is the identity set from :func:`live_artist_ids`. An alive
    artist is compared by identity WHILE the strong reference is held, so a
    reused ``id()`` can never be mistaken for the artist itself -- the hazard
    that rules out a plain ``id() -> artist`` map.

    ``refs`` may be None or empty -- nothing was noted for this call. With no
    evidence the answer is False: nothing is dropped on a guess.
    """
    if not refs:
        return False
    for ref in refs:
        artist = ref()
        if artist is None:
            continue  # released: it was attached when noted, so it left
        if id(artist) in live_ids:
            return False  # still on the figure: keep the call
        if _attached(artist):
            return False  # on ANOTHER figure: not this save's business
    return True


def live_artist_ids(fig: Any) -> Set[int]:
    """Identity set of every artist the figure currently holds.

    ``Axes.get_children()`` is the axes' own complete bookkeeping and was
    measured to cover lines, texts, collections, patches and images alike, so
    one call per axes beats maintaining a container list that could drift.
    """
    ids: Set[int] = set()
    raw = getattr(fig, "fig", fig)
    holders: List[Any] = [raw]
    get_axes = getattr(raw, "get_axes", None)
    if callable(get_axes):
        try:
            holders.extend(list(cast(Iterable[Any], get_axes())))
        except Exception:
            pass
    for holder in holders:
        try:
            children = holder.get_children()
        except Exception:
            continue
        ids.update(id(child) for child in children)
    return ids


def referenced_call_ids(axes_records: Iterable[Any]) -> Set[str]:
    """Call ids that a surviving record refers to (``{"__ref__": <call_id>}``)."""
    referenced: Set[str] = set()
    for ax_record in axes_records:
        for record in list(getattr(ax_record, "calls", []) or []) + list(
            getattr(ax_record, "decorations", []) or []
        ):
            for arg in getattr(record, "args", None) or []:
                if isinstance(arg, dict):
                    ref = arg.get("__ref__")
                    if isinstance(ref, str):
                        referenced.add(ref)
    return referenced


@dataclass(frozen=True)
class DroppedCall:
    """A recorded call the reconcile removed from the recipe."""

    axes_key: str
    call_id: str
    function: str
    half: str  # "calls" or "decorations"

    def __str__(self) -> str:
        return f"{self.function}({self.call_id})"


def prune(
    records: Sequence[Any],
    registry: Dict[int, tuple],
    live_ids: Set[int],
    referenced_ids: Set[str],
    axes_key: str,
    half: str,
) -> Tuple[List[Any], List[DroppedCall]]:
    """``(kept, dropped)`` for one half of an axes record.

    Pure apart from reading the registry: the caller decides what to do with the
    two lists, so the rule can be tested without a figure.
    """
    kept: List[Any] = []
    dropped: List[DroppedCall] = []
    for record in records:
        call_id = getattr(record, "id", None)
        refs = noted_artists(registry, record)
        if (
            refs
            and call_id not in referenced_ids
            and call_is_gone(refs, live_ids)
        ):
            dropped.append(
                DroppedCall(
                    axes_key=axes_key,
                    call_id=str(call_id),
                    function=str(getattr(record, "function", "?")),
                    half=half,
                )
            )
            continue
        kept.append(record)
    return kept, dropped


__all__ = [
    "DroppedCall",
    "call_is_gone",
    "flatten_artists",
    "live_artist_ids",
    "noted_artists",
    "note_call_artists",
    "prune",
    "referenced_call_ids",
]

# EOF
