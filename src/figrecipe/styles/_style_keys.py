#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make a style key that cannot be honored DETECTABLE instead of silent.

Card figrecipe-three-style-key-vocabularies-disagree-20260907. The measured
shape (2026-09-17): ``SCITEX_STYLE`` advertises 33 keys; ``apply_style_mm`` never
looks up 15 of them by name; 9 of those 15 belong to the layout/plot path; 6 are
referenced nowhere outside the presets. Three vocabularies, and no single place
declares which one a consumer honors — so a MISSPELLED key matches nothing
anywhere, the merge ``{**(base or {}), **style}`` in ``_api/_subplots.py`` simply
carries it, and the styling it was supposed to change never happens. Nothing is
raised, nothing is logged, and the figure looks almost right.

This module does NOT unify the vocabularies — that is a design change, and the
vocabulary a user may legitimately pass is the UNION of what the loaded style
provides and what ``SCITEX_STYLE`` advertises, which is exactly what the merge
site can compute without a hand-maintained list. What it fixes is the silence: a
key in neither is reported, and a near-miss of a known key is named, so a typo
costs one word to fix instead of a debugging session.

Stdlib only (``difflib``), no imports from the package, so it is exercised by
the repo's expression tests.
"""

import warnings
from difflib import get_close_matches
from typing import Any, Dict, Iterable, List, Mapping


class UnknownStyleKeyWarning(UserWarning):
    """A user-supplied style key that no consumer can honor.

    A warning rather than an error on purpose: styles are merged from several
    sources (the loaded style, a preset, a caller's dict), and a key this module
    does not recognise may be honored by a consumer it cannot see. Failing the
    call would break working figures; saying which key was ignored does not.
    """


def unknown_style_keys(
    style: Mapping[str, Any],
    known: Iterable[str],
) -> List[str]:
    """The keys of ``style`` that the ``known`` vocabulary does not contain."""
    known_set = set(known)
    return sorted(key for key in style if key not in known_set)


def style_key_suggestions(
    style: Mapping[str, Any],
    known: Iterable[str],
    cutoff: float = 0.75,
) -> Dict[str, str]:
    """Nearest known key for each unknown one — the "did you mean" a typo needs.

    Only keys close enough to a known key are returned; a genuinely new key gets
    no suggestion rather than a misleading one.
    """
    known_list = sorted(set(known))
    suggestions: Dict[str, str] = {}
    for key in unknown_style_keys(style, known):
        matches = get_close_matches(key, known_list, n=1, cutoff=cutoff)
        if matches:
            suggestions[key] = matches[0]
    return suggestions


def warn_unknown_style_keys(
    style: Mapping[str, Any],
    known: Iterable[str],
) -> List[str]:
    """Warn about each unknown style key; return them.

    Returns the list so a caller (or a test) can act on it without having to
    capture warnings, and so the contract is checkable without mocks.
    """
    unknown = unknown_style_keys(style, known)
    suggestions = style_key_suggestions(style, known)
    for key in unknown:
        near = suggestions.get(key)
        hint = f" Did you mean {near!r}?" if near else ""
        warnings.warn(
            f"figrecipe: style key {key!r} is not a key of the loaded style or "
            f"of SCITEX_STYLE, so nothing honors it and it is ignored.{hint} "
            f"The value you passed for it has no effect on the figure.",
            UnknownStyleKeyWarning,
            stacklevel=3,
        )
    return unknown


__all__ = [
    "UnknownStyleKeyWarning",
    "style_key_suggestions",
    "unknown_style_keys",
    "warn_unknown_style_keys",
]

# EOF
