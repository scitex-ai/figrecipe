#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every CSS custom property figrecipe's stylesheets read must resolve.

``color: var(--accent-color)`` where nothing declares ``--accent-color`` is not
an error anywhere. CSS treats the declaration as invalid at computed-value time
and falls back to the inherited value, so the rule silently does nothing: no
console warning, no build failure, no red test. The element just renders with
the wrong colour, and only in whichever theme makes that wrong colour visible.

That is exactly what the Template Gallery shipped. ``--accent-color``,
``--accent-bg`` and ``--bg-hover`` are declared by NOTHING -- not
app-variables.css, not scitex-ui's primitives -- so the gallery's hover
highlight and its active category tab had no colour at all, in both themes, for
as long as the panel has existed.

Why this scans the source instead of testing a rendered page: the fix for those
three was found by reading one stylesheet, and reading one stylesheet is how
four more references in two SIBLING files were missed on the same pass. "Did we
get them all?" is not a question to answer by eye over 18 stylesheets. Ask the
parser.

Lives in tests/develop/ next to test_audit.py and test_no_null_formatter_traps
because it is the same species: a conformance gate over the whole source tree,
mirroring no single src file.

A reference WITH a fallback -- ``var(--panel-color, #2b2b2b)`` -- is fine by
construction and is not checked; the fallback is the author saying the token may
be absent.
"""

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STYLES = _REPO_ROOT / "src" / "figrecipe" / "_django" / "frontend" / "src" / "styles"

# `var(--name` with no comma before the closing paren -- i.e. no fallback.
_REF = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(,)?")
_DECL = re.compile(r"(?m)^\s*(--[A-Za-z0-9_-]+)\s*:")

# Tokens figrecipe deliberately does NOT declare because the scitex-ui shell
# does. figrecipe renders inside that shell, so these resolve at runtime even
# though nothing in this repo defines them. Adding a name here is a claim that
# scitex-ui declares it -- `test_shell_provided_token_exists_in_scitex_ui`
# checks the claim wherever scitex-ui is importable.
_SHELL_PROVIDED = {
    "--app-accent-figrecipe",
    "--bg-primary",
    "--bg-secondary",
    "--border-color",
    "--status-error",
    "--status-success",
    "--status-warning",
    "--text-inverse",
    "--text-muted",
    "--text-primary",
    "--text-secondary",
    "--workspace-bg-elevated",
    "--workspace-bg-hover",
    "--workspace-bg-primary",
    "--workspace-bg-secondary",
    "--workspace-bg-tertiary",
    "--workspace-border-default",
    "--workspace-border-hover",
    "--workspace-border-subtle",
    "--workspace-icon-hover",
}

# Known-dead references that predate this gate. They are real defects -- the
# rules using them render with no colour -- but they sit in stylesheets untouched
# by the change that introduced this file, and silently rewriting unrelated UI
# to make a new test green is how a fix becomes a regression.
#
# This is a RATCHET, not an allow-list. It may only shrink:
# `test_known_dead_list_has_no_stale_entries` fails if a name here is no longer
# referenced, so fixing one forces its removal, and nothing new can be added
# without an explicit edit to this file.
_KNOWN_DEAD = {
    "--accent-bg": "export-dialog.css",
    "--accent-color": "export-dialog.css",
    "--bg-hover": "export-dialog.css",
    "--element-color": "canvas.css",
}


def _stylesheets() -> list[Path]:
    sheets = sorted(_STYLES.rglob("*.css"))
    if not sheets:
        # Hard failure, not a skip. A gate that quietly passes when it cannot
        # find the thing it guards is worse than no gate: it reports green for
        # a tree it never opened.
        pytest.fail(f"no stylesheets found under {_STYLES}")
    return sheets


@pytest.fixture(scope="module")
def declared() -> set[str]:
    """Every custom property figrecipe's own stylesheets declare."""
    names: set[str] = set()
    for sheet in _stylesheets():
        names |= set(_DECL.findall(sheet.read_text(encoding="utf-8")))
    return names


@pytest.fixture(scope="module")
def unresolved(declared) -> dict[str, set[str]]:
    """``{token: {stylesheets reading it}}`` for tokens nothing provides.

    A token is unresolved when it is read WITHOUT a fallback and is declared
    neither here nor (by the `_SHELL_PROVIDED` claim) by the shell.
    """
    refs: dict[str, set[str]] = {}
    for sheet in _stylesheets():
        for match in _REF.finditer(sheet.read_text(encoding="utf-8")):
            token = match.group(1)
            if match.group(2):  # has a fallback -- author allowed for absence
                continue
            if token in declared or token in _SHELL_PROVIDED:
                continue
            refs.setdefault(token, set()).add(sheet.name)
    return refs


@pytest.fixture(scope="module")
def scitex_ui_tokens() -> set[str]:
    """Custom properties the scitex-ui shell declares.

    scitex-ui is not a figrecipe dependency (figrecipe's editor is mounted BY
    the shell, not the other way round), so this only resolves where it happens
    to be installed. It strengthens the gate; it is not what makes the gate able
    to fail -- `test_no_stylesheet_reads_an_undeclared_token` needs nothing
    external.
    """
    scitex_ui = pytest.importorskip(
        "scitex_ui",
        reason="scitex-ui not installed; shell-provided tokens unverifiable here",
    )
    css_root = Path(scitex_ui.get_static_dir()) / "css"
    if not css_root.is_dir():
        pytest.skip(f"scitex-ui ships no stylesheets at {css_root}")
    names: set[str] = set()
    for sheet in css_root.rglob("*.css"):
        names |= set(_DECL.findall(sheet.read_text(encoding="utf-8")))
    return names


def test_no_stylesheet_reads_an_undeclared_token(unresolved):
    """No NEW dead token. The four in `_KNOWN_DEAD` are the standing debt."""
    # Arrange
    ratchet = set(_KNOWN_DEAD)
    # Act
    offenders = {t: s for t, s in unresolved.items() if t not in ratchet}
    # Assert
    assert not offenders, (
        "these CSS custom properties are read with no fallback and are declared "
        "neither by figrecipe nor (per _SHELL_PROVIDED) by the scitex-ui shell. "
        "The rules using them render with no colour, in both themes, with no "
        "error anywhere:\n"
        + "\n".join(
            f"  {token}  <- {', '.join(sorted(sheets))}"
            for token, sheets in sorted(offenders.items())
        )
        + "\nDeclare the token in app-variables.css, switch to one that exists, "
        "or give the reference a fallback."
    )


def test_known_dead_list_has_no_stale_entries(unresolved):
    """Fixing a known-dead token must delete it from the ratchet."""
    # Arrange
    ratchet = set(_KNOWN_DEAD)
    # Act
    stale = sorted(ratchet - set(unresolved))
    # Assert
    assert not stale, (
        "these tokens are listed in _KNOWN_DEAD but are no longer unresolved "
        f"references: {stale}. Remove them -- a ratchet that keeps fixed entries "
        "stops being able to tell debt from history."
    )


def test_gallery_stylesheet_is_free_of_dead_tokens(unresolved):
    """The gallery -- modal and empty-canvas start grid -- resolves everything.

    Called out separately from the tree-wide gate so a regression in the gallery
    names the gallery, rather than arriving as one line inside a list of
    unrelated stylesheets. The gallery is now the editor's FIRST screen, so a
    colour that resolves to nothing there is the whole product looking broken.
    """
    # Arrange
    sheet_name = "gallery.css"
    # Act
    dead_here = sorted(t for t, s in unresolved.items() if sheet_name in s)
    # Assert
    assert not dead_here, f"{sheet_name} reads undeclared CSS tokens: {dead_here}"


def test_figure_plate_token_is_declared(declared):
    """The constant plate behind a thumbnail is a named token.

    The gallery thumbnails are opaque white matplotlib PNGs, so the plate behind
    them is intentionally constant rather than theme-following -- a themed plate
    leaves the image as a lit rectangle torn out of a dark pane. That intent
    belongs in one named token.
    """
    # Arrange
    token = "--figure-plate"
    # Act
    is_declared = token in declared
    # Assert
    assert is_declared, f"{token} is undeclared; app-variables.css should own it"


def test_thumbnail_rules_use_the_plate_token_not_a_literal():
    """No thumbnail rule hard-codes its background colour.

    A bare `#ffffff` in a rule is indistinguishable from a theme colour someone
    forgot to tokenise, which is how a stylesheet stops surviving a theme
    switch. Comments may discuss colours; declarations may not spell them.
    """
    # Arrange
    gallery = (_STYLES / "gallery.css").read_text(encoding="utf-8")
    blocks = [b for b in gallery.split("}") if "-thumb {" in b]
    # Act
    literal_colour = [b.strip() for b in blocks if "#" in b.split("*/")[-1]]
    # Assert
    assert not literal_colour, (
        "a thumbnail rule sets a literal colour; use var(--figure-plate):\n"
        + "\n".join(literal_colour)
    )


@pytest.mark.parametrize("token", sorted(_SHELL_PROVIDED))
def test_shell_provided_token_exists_in_scitex_ui(token, scitex_ui_tokens):
    """Each `_SHELL_PROVIDED` claim is checked against the real scitex-ui.

    Listing a name there says "figrecipe relies on the shell to declare this".
    An unchecked claim is how a typo, or a token the shell quietly dropped,
    turns into a rule rendering with no value.
    """
    # Arrange
    shell_css_declares = scitex_ui_tokens
    # Act
    is_provided = token in shell_css_declares
    # Assert
    assert is_provided, (
        f"{token} is listed in _SHELL_PROVIDED but scitex-ui declares no such "
        "token. Either the name is a typo or the shell dropped it; either way "
        "figrecipe renders that rule with no value."
    )
