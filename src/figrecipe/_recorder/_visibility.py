#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which of a call's artists the figure is still SHOWING? (save-time annotation)

Card figrecipe-hidden-artist-set-visible-false-not-recorded-20260927, split out of
figrecipe-recipe-keeps-artists-removed-before-save-20260906 (sweep root cause 2:
state mutated on the handle after the call).

The defect: a call is recorded, then its artist is HIDDEN before save
(``line.set_visible(False)``). The record still holds the call as it was made, so
a replay DRAWS an artist the saved PNG does not show -- the same divergence as the
removal case, with the record on the wrong side of it. Measured on the card's own
case (matplotlib 3.11.1, a real save and the real validator): MSE 406.02, 1.8% of
pixels changed, and the DEFAULT ``fr.save(fig, path)`` path RAISES.

Why this is an ANNOTATION and not a drop: the artist is still on the figure and
still holds the user's data. Hiding a series asks not to PAINT it, not to forget
it, and matplotlib keeps a hidden artist in ``ax.lines`` -- so dropping the call
would delete a series the user may toggle back on, which is the opposite of what
was asked. The repair writes the artist's FINAL visibility into the recorded
call's kwargs instead (``visible: false``), and the replay then constructs the
artist unpainted, exactly as the saved figure holds it. Measured: a recipe
hand-annotated this way replays with ``line_visible=False`` and validates at 0.00.
No record-format change and no new field -- ``visible`` is a matplotlib Artist
property every plotter already forwards.

The rule is the conservatism the removal repair uses, for the same reason -- a
wrong edit changes the user's own recipe:

* a call is annotated only when EVERY artist it created is STILL ON THE FIGURE and
  ALL of them are hidden. One artist still showing makes the call half-hidden,
  which no single ``visible`` value can express, so the record is left as it is;
* a released or detached artist puts the call in the removal repair's territory
  (or in nobody's), never in this one's;
* only methods whose REPLAY honours ``visible`` are annotated, and that set is
  DERIVED rather than hand-copied -- :func:`replay_accepts_visible` asks the
  reproducer's own dispatch table whether a special handler owns the call, then
  asks matplotlib's own ``Axes`` class whether the resolved method takes
  ``visible``. A hand-written vocabulary is exactly what made the first shipped
  slice of the removed-artist check blind to 26 of the 49 plotters.

No matplotlib import at module level: the decision functions read ``weakref``s,
identities and one attribute, so they run under the repo's expression tests.
"""

import ast
from dataclasses import dataclass
from functools import lru_cache
from inspect import Parameter, signature
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from ._artists import noted_artists


def _visible(artist: Any) -> Optional[bool]:
    """The artist's own ``get_visible()``, or None when it cannot be read.

    None is "no evidence", never "hidden": an unreadable artist must not make a
    call look hidden, because the annotation is a write to the user's recipe.
    """
    get = getattr(artist, "get_visible", None)
    if not callable(get):
        return None
    try:
        return bool(get())
    except Exception:
        return None


def call_is_hidden(refs: Optional[Sequence[Any]], live_ids: Set[int]) -> bool:
    """True when every artist this call created is on the figure and hidden.

    ``live_ids`` is the identity set from
    :func:`figrecipe._recorder._artists.live_artist_ids`. Each weakref is
    dereferenced while the strong reference is held, so a recycled ``id()`` can
    never stand in for the artist itself.

    Anything short of "all of them, live, hidden" is False:

    * no refs (nothing was registered for this call) -- nothing is written on a
      guess;
    * an artist that was released, or that is not on this figure (removed, or
      owned by another figure) -- that is the removal repair's business;
    * an artist that is visible -- a partially hidden call is not expressible as
      one ``visible`` value, so its record stays untouched.
    """
    if not refs:
        return False
    hidden: List[bool] = []
    for ref in refs:
        artist = ref()
        if artist is None:
            return False  # released: it left the figure, so this is a removal
        if id(artist) not in live_ids:
            return False  # not this figure's artist: not this module's call
        shown = _visible(artist)
        if shown is None:
            return False  # unreadable: no evidence, so no edit
        hidden.append(not shown)
    return bool(hidden) and all(hidden)


@lru_cache(maxsize=None)
def replay_accepts_visible(method_name: str) -> bool:
    """True when a replay of ``method_name`` honours a ``visible`` kwarg.

    DERIVED from the two authorities that actually decide it, never from a list
    kept here:

    * the reproducer's own dispatch table -- a call with a special handler is
      replayed by that handler, on its own kwargs path, and those are out of this
      slice's scope (measured: ``boxplot``, ``graph``, ``stem``, ``violinplot``
      of the recorder's 58 artist methods);
    * matplotlib's own ``Axes`` -- the reproducer replays a generic call as
      ``getattr(ax, call.function)(**kwargs)`` on a raw axes, so the method body
      is what decides. A method with a closed signature (measured: ``pie``,
      ``streamplot``) would raise on an unexpected kwarg, and a recipe that no
      longer replays is worse than one that draws a hidden artist.

    Both imports are lazy: the module stays importable (and testable) without
    matplotlib, like its sibling ``_artists``.
    """
    from .._reproducer._replay_dispatch import find_special_handler

    if find_special_handler(method_name) is not None:
        return False
    from matplotlib.axes import Axes as _Axes

    method = getattr(_Axes, method_name, None)
    if method is None:
        return False
    try:
        parameters = dict(signature(method).parameters)
    except (TypeError, ValueError):
        return False
    if "visible" in parameters:
        return True
    return any(p.kind is Parameter.VAR_KEYWORD for p in parameters.values())


@dataclass(frozen=True)
class AnnotatedCall:
    """A recorded call whose kwargs gained the artist's final visibility."""

    axes_key: str
    call_id: str
    function: str
    half: str  # "calls" or "decorations"

    def __str__(self) -> str:
        return f"{self.function}({self.call_id})"


def annotate_hidden(
    records: Sequence[Any],
    registry: Dict[int, tuple],
    live_ids: Set[int],
    axes_key: str,
    half: str,
    accepts_visible: Callable[[str], bool] = replay_accepts_visible,
) -> List[AnnotatedCall]:
    """Write ``visible: False`` into every record whose artists are all hidden.

    Mutates ``record.kwargs`` in place -- the record object is what the save
    pipeline serializes -- and returns what changed, so the caller can report it.
    Returns ``[]`` for an ordinary figure, and for a record that already says
    ``visible: false``: nothing is rewritten, so the caller has nothing to
    announce either.
    """
    annotated: List[AnnotatedCall] = []
    for record in records:
        function = str(getattr(record, "function", ""))
        if not accepts_visible(function):
            continue
        if not call_is_hidden(noted_artists(registry, record), live_ids):
            continue
        kwargs = getattr(record, "kwargs", None)
        if not isinstance(kwargs, dict) or kwargs.get("visible") is False:
            continue
        kwargs["visible"] = False
        annotated.append(
            AnnotatedCall(
                axes_key=axes_key,
                call_id=str(getattr(record, "id", "?")),
                function=function,
                half=half,
            )
        )
    return annotated


def module_level_imports(text: str) -> Set[str]:
    """Names imported at module level, for the no-matplotlib-at-import assertion.

    Kept here rather than in the test so the test asserts a property of THIS
    module (its top-level imports) and not a property of the test's own parser.
    """
    names: Set[str] = set()
    for node in ast.parse(text).body:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    return names


__all__ = [
    "AnnotatedCall",
    "annotate_hidden",
    "call_is_hidden",
    "module_level_imports",
    "replay_accepts_visible",
]

# EOF
