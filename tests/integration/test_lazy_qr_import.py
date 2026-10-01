"""Real interpreter and figure controls for the deferred public QR capability."""

import json
import os
import subprocess
import sys


def _probe(script, tmp_path):
    path = tmp_path / "qr_probe.py"
    path.write_text(script)
    result = subprocess.run(
        [sys.executable, str(path)],
        env=os.environ.copy(),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return json.loads(result.stdout)


def test_bare_import_keeps_optional_qr_and_plotting_modules_deferred(tmp_path):
    # Arrange
    script = """
import json, sys
import figrecipe
print(json.dumps([name for name in ('figrecipe._qr', 'scitex_logging', 'matplotlib') if name in sys.modules]))
"""
    # Act
    loaded = _probe(script, tmp_path)
    # Assert
    assert loaded == []


def test_public_qr_lookup_preserves_its_actual_function_and_export(tmp_path):
    # Arrange
    script = """
import json
import figrecipe
function = figrecipe.add_qr_to_figure
from figrecipe._qr import add_qr_to_figure
print(json.dumps({'actual_function': function is add_qr_to_figure, 'cached_function': figrecipe.add_qr_to_figure is function, 'original_export_once': figrecipe.__all__.count('add_qr_to_figure') == 1}))
"""
    # Act
    contract = _probe(script, tmp_path)
    # Assert
    assert all(contract.values()), contract


def test_deferred_qr_call_keeps_real_figure_and_metadata_behavior(tmp_path):
    # Arrange
    script = """
import importlib.util, json
from matplotlib.figure import Figure
import figrecipe
figure = Figure()
metadata = {'label': 'Owned synthetic QR control'}
before = metadata.copy()
result = figrecipe.add_qr_to_figure(figure, metadata)
expected_axes = 1 if importlib.util.find_spec('qrcode') is not None else 0
print(json.dumps({'same_real_figure': result is figure, 'caller_metadata_retained': metadata == before, 'real_capability_or_documented_missing_dependency': len(figure.axes) == expected_axes}))
"""
    # Act
    contract = _probe(script, tmp_path)
    # Assert
    assert all(contract.values()), contract
