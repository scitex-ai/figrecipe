"""Exact content rendering uses the installed owning logger primitives."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def _run(tmp_path: Path, body: str):
    source = Path(__file__).resolve().parents[3] / "src"
    env = {
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.defpath,
        "PYTHONPATH": str(source),
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(tmp_path / "matplotlib"),
        "SCITEX_DIR": str(tmp_path / "state"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "NO_COLOR": "1",
    }
    script = (
        "import sys,io,json,contextlib\n"
        "def offline(event,args):\n"
        "    if event in {'socket.bind','socket.connect','socket.getaddrinfo'}:\n"
        "        raise RuntimeError('content controls must remain offline')\n"
        "sys.addaudithook(offline)\n"
        "import scitex_logging as slog\n"
        # Cold matplotlib initialization can emit legitimate font-cache
        # diagnostics. Measure the content call after that initialization;
        # each verbosity test explicitly selects its own level below.
        "slog.configure(level='critical',enable_file=False,capture_prints=False)\n"
        "from figrecipe._utils._console import render_content\n" + body
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result


@pytest.mark.parametrize("capture", [False, True])
@pytest.mark.parametrize("level", ["info", "critical"])
def test_content_is_exact_at_all_verbosity_and_capture_levels(tmp_path, capture, level):
    content = ['{"label":"Δ","ok":true}', "first\nsecond\n", ""]
    result = _run(
        tmp_path,
        f"slog.configure(level={level!r},enable_file=False,capture_prints={capture!r})\n"
        f"for value in {content!r}:\n"
        "    assert render_content(value) is None",
    )
    assert (result.stdout, result.stderr) == (
        "".join(value + "\n" for value in content),
        "",
    )


def test_legacy_alias_and_signature_are_preserved(tmp_path):
    result = _run(
        tmp_path,
        "import inspect\n"
        "from figrecipe._logging import render_content as legacy\n"
        "assert legacy is render_content\n"
        "assert list(inspect.signature(render_content).parameters)==['content']\n"
        "assert legacy('LEGACY') is None",
    )
    assert (result.stdout, result.stderr) == ("LEGACY\n", "")


@pytest.mark.parametrize("capture", [False, True])
def test_content_respects_nested_stdout_redirects(tmp_path, capture):
    result = _run(
        tmp_path,
        f"slog.configure(enable_file=False,capture_prints={capture!r})\n"
        "original=sys.stdout\na=io.StringIO(); b=io.StringIO()\n"
        "with contextlib.redirect_stdout(a):\n"
        "    render_content('A')\n"
        "    with contextlib.redirect_stdout(b):\n"
        "        render_content('B')\n"
        "    render_content('C')\n"
        "assert sys.stdout is original\n"
        "render_content(json.dumps([a.getvalue(),b.getvalue()]))",
    )
    assert (json.loads(result.stdout), result.stderr) == (["A\nC\n", "B\n"], "")


def test_content_preserves_foreign_wrapper_and_does_not_force_flush(tmp_path):
    result = _run(
        tmp_path,
        "class Foreign:\n"
        "    def __init__(self):\n"
        "        self.original_stdout=io.StringIO()\n"
        "        self.destination=io.StringIO()\n"
        "    def write(self,text): return self.destination.write(text)\n"
        "    def flush(self): raise AssertionError('content forced a flush')\n"
        "stream=Foreign()\n"
        "with contextlib.redirect_stdout(stream):\n"
        "    render_content('FOREIGN')\n"
        "render_content(json.dumps([stream.destination.getvalue(),"
        "stream.original_stdout.getvalue()]))",
    )
    assert (json.loads(result.stdout), result.stderr) == (["FOREIGN\n", ""], "")


def test_content_bypasses_nested_owned_capture_without_disabling_it(tmp_path):
    result = _run(
        tmp_path,
        "from scitex_logging._print_capture import PrintCapture\n"
        "slog.configure(enable_file=False,capture_prints=False)\n"
        "original=sys.stdout\n"
        "with PrintCapture('outer') as outer:\n"
        "    with PrintCapture('inner') as inner:\n"
        "        render_content('FRAME')\n"
        "        assert sys.stdout is inner and inner.capturing and outer.capturing\n"
        "    assert sys.stdout is outer and outer.capturing\n"
        "assert sys.stdout is original",
    )
    assert (result.stdout, result.stderr) == ("FRAME\n", "")


def test_content_write_error_propagates(tmp_path):
    result = _run(
        tmp_path,
        "class Broken:\n"
        "    def write(self,text): raise OSError('owned write failure')\n"
        "    def flush(self): raise AssertionError('unexpected flush')\n"
        "with contextlib.redirect_stdout(Broken()):\n"
        "    try:\n"
        "        render_content('FRAME')\n"
        "    except OSError as exc:\n"
        "        assert str(exc)=='owned write failure'\n"
        "    else:\n"
        "        raise AssertionError('write error was swallowed')",
    )
    assert (result.stdout, result.stderr) == ("", "")


def test_missing_logging_at_render_time_retains_owning_extra_hint(tmp_path):
    expected = (
        "scitex-logging is required for this capability but is not installed. "
        "Install it with: pip install 'figrecipe[scitex]'"
    )
    result = _run(
        tmp_path,
        "import importlib.abc\n"
        "class Unavailable(importlib.abc.MetaPathFinder):\n"
        "    def find_spec(self,fullname,path=None,target=None):\n"
        "        if fullname.split('.',1)[0]=='scitex_logging':\n"
        "            raise ModuleNotFoundError('deliberately absent',"
        "name='scitex_logging')\n"
        "for name in tuple(sys.modules):\n"
        "    if name.split('.',1)[0]=='scitex_logging':\n"
        "        del sys.modules[name]\n"
        "sys.meta_path.insert(0,Unavailable())\n"
        "try:\n"
        "    render_content('FRAME')\n"
        "except ImportError as exc:\n"
        f"    assert str(exc)=={expected!r}\n"
        "else:\n"
        "    raise AssertionError('missing logger did not fail')",
    )
    assert (result.stdout, result.stderr) == ("", "")
