"""Smoke import mirror for figrecipe._diagram._diagram._io.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import logging

import pytest

from figrecipe import Diagram


def test_import__diagram__diagram__io_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._diagram._diagram._io'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _save(tmp_path, x_mm):
    diagram = Diagram(width_mm=110, height_mm=45)
    diagram.add_box("input", "Input", shape="box", x_mm=x_mm, y_mm=22,
                    width_mm=35, height_mm=18)
    return diagram.save(tmp_path / "flow.png", save_debug=False)


def test_rejected_diagram_logs_error_with_offending_id(tmp_path, caplog):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 0)
    errors = [record.getMessage() for record in caplog.records
              if record.name.endswith("._diagram._io") and record.levelno >= logging.ERROR]
    # Assert
    assert any("input" in message and "validation failed" in message for message in errors)


def test_rejected_diagram_does_not_log_success(tmp_path, caplog):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 0)
    messages = [record.getMessage() for record in caplog.records
                if record.name.endswith("._diagram._io")]
    # Assert
    assert not any(message.startswith("diagram saved:") for message in messages)


def test_rejected_diagram_preserves_failed_diagnostic(tmp_path):
    # Arrange
    expected = tmp_path / "flow_FAILED.png"
    # Act
    path = _save(tmp_path, 0)
    # Assert
    assert path == expected and path.is_file()


def test_valid_diagram_logs_success(tmp_path, caplog):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 25)
    messages = [record.getMessage() for record in caplog.records
                if record.name.endswith("._diagram._io")]
    # Assert
    assert any(message.startswith("diagram saved:") for message in messages)


def test_valid_diagram_preserves_requested_path(tmp_path):
    # Arrange
    expected = tmp_path / "flow.png"
    # Act
    path = _save(tmp_path, 25)
    # Assert
    assert path == expected and path.is_file()
