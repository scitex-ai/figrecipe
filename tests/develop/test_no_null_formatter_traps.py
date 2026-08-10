#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe's own source must never call ``set_[xy]ticklabels([])``.

That call pins a ``NullFormatter`` on the *axis*. Every tick set afterwards then
renders blank -- through the wrapper, through the raw axes, through an explicit
``set_ticklabels``, forever. There is no caller-side workaround: the author's
only recourse is to not have called it. ``set_[xy]ticks([])`` clears ticks AND
labels just as well, and is reversible.

Why this test scans the AST instead of testing a behaviour: the same two lines
have been fixed four times, in four modules, by reading code and grepping. Each
sweep was believed complete and each one missed a site -- most recently the pie
wrapper, which kept blanking labels for two releases after its twin in styles/
stopped. The recurring defect is not the pie chart; it is that "did we get them
all?" was being answered by hand. Ask the parser instead.

Only the EMPTY-list form is a trap. ``set_xticklabels(labels)`` with real labels
is legitimate and common -- categorical heatmap axes need exactly that.

Lives in tests/develop/ next to test_audit.py because it is the same species: a
conformance gate over the whole source tree, not a unit test of one module. It
mirrors no src file, so tests/figrecipe/ (which audit PS-204 requires to mirror
src/figrecipe/ file-for-file) is the wrong home for it.
"""

import ast
from pathlib import Path

import figrecipe

_TRAPS = {"set_xticklabels", "set_yticklabels"}
_SRC = Path(figrecipe.__file__).parent


def _is_trap(node):
    """A ``*.set_[xy]ticklabels([])`` call -- empty list literal, sole argument."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in _TRAPS:
        return False
    return (
        len(node.args) == 1
        and isinstance(node.args[0], ast.List)
        and not node.args[0].elts
    )


def _trap_sites():
    sites = []
    for py in sorted(_SRC.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if _is_trap(node):
                sites.append(f"{py.relative_to(_SRC)}:{node.lineno}")
    return sites


def test_no_source_file_pins_a_null_formatter():
    # Arrange: every .py figrecipe ships, parsed -- not grepped, not sampled.
    # Act
    sites = _trap_sites()
    # Assert
    assert sites == [], (
        "set_[xy]ticklabels([]) pins a NullFormatter that blanks every tick set "
        "afterwards, irreversibly. Use set_[xy]ticks([]) -- it clears ticks and "
        f"labels, and can be undone. Trap sites: {sites}"
    )


def test_the_scanner_actually_recognises_a_trap():
    # Arrange: a guard that cannot fail would pass an empty codebase and prove
    # nothing -- so hand it the exact line this test exists to forbid.
    tree = ast.parse("ax.set_xticklabels([])")
    # Act
    found = [n for n in ast.walk(tree) if _is_trap(n)]
    # Assert
    assert len(found) == 1


def test_the_scanner_allows_real_labels():
    # Arrange: categorical axes legitimately set labels; only the empty form is
    # the trap, and a guard that banned both would be unusable.
    tree = ast.parse("ax.set_xticklabels(['a', 'b'])")
    # Act
    found = [n for n in ast.walk(tree) if _is_trap(n)]
    # Assert
    assert found == []


# EOF
