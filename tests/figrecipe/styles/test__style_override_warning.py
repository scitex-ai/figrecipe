#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Warning when a caller kwarg overrides a SCITEX_STYLE default."""

from __future__ import annotations

import textwrap
import warnings

import matplotlib
import pytest

matplotlib.use("Agg")

import figrecipe as fr  # noqa: E402
import figrecipe.styles._style_override_warning  # noqa: E402,F401
from figrecipe.styles._style_override_warning import (  # noqa: E402
    NO_WARN_ENV,
    StyleOverrideWarning,
    warn_style_overrides,
)


@pytest.fixture
def ax():
    _fig, axis = fr.subplots()
    return axis


def _caught(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn()
    return [w for w in caught if issubclass(w.category, StyleOverrideWarning)]


# --- warns ------------------------------------------------------------------


def test_overriding_title_fontsize_warns(ax):
    caught = _caught(lambda: ax.set_title("t", fontsize=14))

    assert len(caught) == 1
    message = str(caught[0].message)
    assert "SCITEX_STYLE default overridden" in message
    assert "fontsize = 8.0" in message  # the default
    assert "fontsize = 14.0" in message  # the override
    assert "SCITEX_STYLE.fonts.title_pt" in message  # its source path


def test_warning_names_the_callers_file_line_and_function(ax):
    def build_fig_02():
        ax.set_title("t", fontsize=14)

    caught = _caught(build_fig_02)

    message = str(caught[0].message)
    assert "in build_fig_02()" in message

    # The reported frame must be THIS test file...
    import os

    assert os.path.basename(__file__) in message
    # ...and must NOT be anywhere inside the installed package. (Checked as a
    # path prefix rather than a filename: this test module's own name contains
    # "_style_override_warning.py", so a basename check would be vacuous.)
    package_dir = os.path.dirname(fr.styles._style_override_warning.__file__)
    assert package_dir not in message


@pytest.mark.parametrize(
    ("call", "style_path"),
    [
        (lambda a: a.set_title("t", fontsize=14), "fonts.title_pt"),
        (lambda a: a.set_xlabel("x", fontsize=14), "fonts.axis_label_pt"),
        (lambda a: a.set_ylabel("y", fontsize=14), "fonts.axis_label_pt"),
        (lambda a: a.tick_params(labelsize=14), "fonts.tick_label_pt"),
    ],
)
def test_tracked_kwargs_across_setters(ax, call, style_path):
    caught = _caught(lambda: call(ax))

    assert len(caught) == 1
    assert style_path in str(caught[0].message)


def test_size_is_tracked_as_an_alias_of_fontsize(ax):
    caught = _caught(lambda: ax.set_title("t", size=14))

    assert len(caught) == 1
    assert "size = 14.0" in str(caught[0].message)


# --- stays quiet ------------------------------------------------------------


def test_no_warning_when_no_kwarg_is_passed(ax):
    assert _caught(lambda: ax.set_title("t")) == []


def test_no_warning_when_the_value_equals_the_default(ax):
    """Passing the themed value explicitly is not drift."""
    assert _caught(lambda: ax.set_title("t", fontsize=8)) == []


def test_no_warn_style_silences_the_call(ax):
    assert _caught(lambda: ax.set_title("t", fontsize=14, no_warn_style=True)) == []


def test_no_warn_style_is_not_forwarded_to_matplotlib(ax):
    """It must be consumed, or matplotlib raises on the unexpected keyword."""
    ax.set_title("t", fontsize=14, no_warn_style=True)
    assert ax.get_title() == "t"

    kwargs = warn_style_overrides("set_title", {"fontsize": 14, "no_warn_style": True})
    assert "no_warn_style" not in kwargs
    assert kwargs["fontsize"] == 14  # the override itself is untouched


def test_env_var_silences_the_whole_script(ax, monkeypatch):
    monkeypatch.setenv(NO_WARN_ENV, "1")
    assert _caught(lambda: ax.set_title("t", fontsize=14)) == []


def test_env_var_set_to_zero_does_not_silence(ax, monkeypatch):
    monkeypatch.setenv(NO_WARN_ENV, "0")
    assert len(_caught(lambda: ax.set_title("t", fontsize=14))) == 1


def test_named_font_sizes_are_not_compared(ax):
    """Matplotlib accepts 'large'/'x-small'; mapping those to points needs
    matplotlib's own scaling table, so guessing would emit false warnings."""
    assert _caught(lambda: ax.set_title("t", fontsize="large")) == []


def test_untracked_kwargs_and_methods_are_ignored(ax):
    assert _caught(lambda: ax.set_title("t", loc="left")) == []
    assert _caught(lambda: ax.plot([0, 1], [0, 1], linewidth=99)) == []


# --- the override still applies --------------------------------------------


def test_the_override_is_not_suppressed(ax):
    """Feedback, not enforcement: the caller's value must still win."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", StyleOverrideWarning)
        ax.set_title("t", fontsize=14)

    assert ax.title.get_fontsize() == 14


# --- unit-level -------------------------------------------------------------


def test_warning_is_filterable_on_its_own_subclass(ax):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warnings.simplefilter("ignore", StyleOverrideWarning)
        ax.set_title("t", fontsize=14)

    assert [w for w in caught if issubclass(w.category, StyleOverrideWarning)] == []


def test_call_site_skips_figrecipe_frames_for_a_script_on_disk(tmp_path):
    """End-to-end through a real file, so the reported path is a real caller."""
    script = tmp_path / "user_script.py"
    script.write_text(
        textwrap.dedent(
            """
            import warnings
            import matplotlib
            matplotlib.use("Agg")
            import figrecipe as fr

            def build_fig_02():
                _fig, ax = fr.subplots()
                ax.set_title("drift", fontsize=14)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                build_fig_02()
                print([str(w.message) for w in caught if "overridden" in str(w.message)][0])
            """
        ),
        encoding="utf-8",
    )

    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=True
    )
    assert "user_script.py:9" in result.stdout
    assert "in build_fig_02()" in result.stdout
