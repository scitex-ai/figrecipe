"""Unavailable optional logging produces the owning extra hint in a fresh interpreter."""

import json
import os
import subprocess
import sys

import pytest


_MODULES = [
    "figrecipe._api._save_helpers",
    "figrecipe._utils._crop",
    "figrecipe._dev._run_demos",
    "figrecipe._django.views",
    "figrecipe._editor",
    "figrecipe._editor._helpers",
    "figrecipe._diagram._diagram._io",
    "figrecipe._django.handlers.axis",
    "figrecipe._django.handlers.elements",
    "figrecipe._django.handlers.stats",
    "figrecipe._django.handlers.datatable",
    "figrecipe._django.handlers.files",
    "figrecipe._django.handlers.downloads",
    "figrecipe._django.handlers.annotation",
    "figrecipe._django.handlers.compose",
    "figrecipe._django.handlers.image",
]


@pytest.mark.parametrize("module_name", _MODULES)
def test_missing_logging_reports_scitex_extra(module_name):
    # Arrange
    code = """
import importlib
import importlib.abc
import json
import sys

class UnavailableOptionalLogging(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] == "scitex_logging":
            raise ModuleNotFoundError(
                "optional logging deliberately unavailable", name="scitex_logging"
            )

sys.meta_path.insert(0, UnavailableOptionalLogging())
try:
    importlib.import_module(sys.argv[1])
except Exception as exc:
    print(json.dumps({"type": type(exc).__name__, "message": str(exc)}))
else:
    print(json.dumps({"type": "no error", "message": ""}))
"""
    # Act
    result = subprocess.run(
        [sys.executable, "-c", code, module_name],
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    observed = json.loads(result.stdout.splitlines()[-1])
    expected = {
        "type": "ImportError",
        "message": (
            "scitex-logging is required for this capability but is not installed. "
            "Install it with: pip install 'figrecipe[scitex]'"
        ),
    }
    # Assert
    assert observed == expected, result.stderr
