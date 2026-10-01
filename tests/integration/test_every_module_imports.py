"""Every module under src/figrecipe must import, or be allowlisted WITH A REASON.

WHY THIS EXISTS. 333 of figrecipe's test files are auto-generated mirror
placeholders whose entire body is::

    mod = pytest.importorskip(module_path)
    assert mod.__name__ == module_path

``pytest.importorskip`` SKIPS when the import fails. So for those 333 modules,
"cannot be imported at all" reports as a skip and the suite stays green. Measured
2026-08-09: that is how a dangling top-level import
(``_csv_formatters/_export_as_csv.py`` importing a ``._export_as_csv_formatters``
aggregator that does not exist) and a dead public export
(``figrecipe._utils.compare_modes``) both survived with 2738 tests passing.

This test is the gate those placeholders only appear to be: it FAILS.

THE ALLOWLIST MATCHES ON REASON, NOT JUST MODULE — which is the whole point.
``_export_as_csv`` fails with "No module named 'scitex_pd'" when that optional
extra is absent, and its dangling relative import hides behind that. Allowlisting
the module alone would re-hide the real defect the moment the extra is installed.
So each entry names the dependency it is allowed to be missing, and a DIFFERENT
failure reason for the same module is still a hard failure.

Entries are individual and carry a written reason, per the project rule that
exemptions are granted one at a time in a reviewable place rather than by a
blanket flag.

ENVIRONMENT-ROBUST BY DESIGN. Allowlisted modules MAY import successfully -- CI
installs the extras, the agent container does not (its venv is built with
``uv pip install -e .``, base dependencies only). So a successful import is never
a failure here; only an unexpected FAILURE is.
"""

from __future__ import annotations

import importlib
import pathlib
import warnings

import pytest

import figrecipe

#: module prefix -> (allowed missing dependency, why it is allowed to be missing)
#:
#: The first element is matched against the exception text. A failure whose text
#: does not contain it is reported even for an allowlisted module.
ALLOWED_MISSING = {
    # MOST SPECIFIC FIRST -- _allowance() returns the first matching prefix, and
    # this module sits under the _csv_formatters entry below.
    "figrecipe._scitex_compat._csv_formatters._export_as_csv": (
        ("_export_as_csv_formatters", "scitex_pd"),
        "KNOWN DEAD MODULE, not an environment gap. It imports 65 formatter names "
        "from a `._export_as_csv_formatters` aggregator that does not exist; the "
        "formatters were split into per-formatter sibling modules and 50 of the 65 "
        "are present, but 15 (_format_plot_conf_mat, _format_plot_ecdf, "
        "_format_plot_fillv, _format_plot_heatmap, _format_plot_image, "
        "_format_plot_joyplot, _format_plot_line, _format_plot_mean_ci, +7) exist "
        "NOWHERE under src/ -- never migrated. So it cannot be repaired by "
        "repointing the import. Found by THIS gate on its first CI run, 2026-08-09; "
        "invisible locally because a missing scitex_pd extra fails earlier. "
        "Exempted per-module with this reason rather than weakening the gate, and "
        "tracked on figrecipe-dimension-viewer-is-dead-public-api-20260809.",
    ),
    "figrecipe._scitex_compat._csv_formatters": (
        "scitex_pd",
        "Declared as an OPTIONAL extra in pyproject, not a base dependency. The "
        "container venv installs base deps only, so these modules cannot import "
        "here. Present in CI.",
    ),
    "figrecipe._mcp.server": (
        "fastmcp",
        "MCP server entry point; fastmcp is an optional extra and is not needed "
        "to use figrecipe as a library.",
    ),
    "figrecipe._django": (
        "settings are not configured",
        "Django modules require an initialised settings module. Importing them "
        "bare is expected to raise ImproperlyConfigured; the Django test suite "
        "exercises them with settings loaded.",
    ),
}


def _all_module_names() -> list[str]:
    """Every importable module path under the installed figrecipe package."""
    root = pathlib.Path(figrecipe.__file__).parent
    names = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in str(path):
            continue
        rel = path.relative_to(root).with_suffix("")
        parts = list(rel.parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(["figrecipe", *parts]))
    return names


def _reason_matches(allowed, text: str) -> bool:
    """Whether an actual failure text is one this module is allowed to fail with.

    ``allowed`` is a single substring or a tuple of them. A tuple is for a module
    whose legitimate failure DIFFERS BY ENVIRONMENT -- _export_as_csv fails on the
    absent scitex_pd extra locally, and on its dead aggregator in CI where the
    extra is installed. Both are documented; which one you see is not a property
    of the code.
    """
    if isinstance(allowed, str):
        allowed = (allowed,)
    return any(a in text for a in allowed)


def _allowance(module_name: str):
    """The (dependency, reason) this module may fail on, or None."""
    for prefix, entry in ALLOWED_MISSING.items():
        if module_name == prefix or module_name.startswith(prefix + "."):
            return entry
    return None


def test_the_package_has_modules_to_check():
    # Arrange: guard against the collection itself silently finding nothing --
    # a sweep over an empty list passes and proves nothing.
    names = _all_module_names()
    # Act
    count = len(names)
    # Assert
    assert count > 100


def test_every_module_imports_or_is_allowlisted_with_a_reason():
    # Arrange
    unexpected = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name in _all_module_names():
            allowance = _allowance(name)
            try:
                importlib.import_module(name)
            except Exception as exc:  # noqa: BLE001 - any failure is the finding
                text = f"{type(exc).__name__}: {exc}"
                if allowance is not None and _reason_matches(allowance[0], text):
                    continue  # the documented reason, in a documented place
                unexpected.append(f"{name}\n      {text[:160]}")
    # Act
    report = "\n  ".join(unexpected)
    # Assert
    assert not unexpected, (
        f"{len(unexpected)} module(s) failed to import for a reason that is NOT "
        f"allowlisted.\n  {report}\n\n"
        "If the failure is legitimate (an optional extra absent in this "
        "environment), add an entry to ALLOWED_MISSING naming the dependency and "
        "why. If it is a broken import, fix it -- the mirror placeholders will "
        "not catch it, they skip."
    )


@pytest.mark.parametrize("prefix", sorted(ALLOWED_MISSING))
def test_each_allowlist_entry_states_a_dependency_and_a_reason(prefix):
    # Arrange: an exemption with no stated reason is the thing this file exists
    # to prevent, so the allowlist is itself checked.
    dependency, reason = ALLOWED_MISSING[prefix]
    deps = (dependency,) if isinstance(dependency, str) else dependency
    # Act
    well_formed = (
        bool(deps) and all(d.strip() for d in deps) and len(reason.strip()) > 40
    )
    # Assert
    assert well_formed
