"""SVG diagnostic errors must survive raster-only dimension inspection."""

import logging

import pytest
from scitex_logging import SUCCESS

import figrecipe as fr


LOGGER = "figrecipe._diagram._diagram._io"


@pytest.mark.parametrize("method", ["save", "render_to_file"])
@pytest.mark.parametrize("save_debug", [False, True])
@pytest.mark.parametrize("suffix", ["png", "svg"])
def test_invalid_diagram_logs_failure_reason_and_retains_diagnostic(
    tmp_path, caplog, method, save_debug, suffix
):
    # Arrange
    fr.load_style("SCITEX")
    diagram = fr.Diagram(width_mm=120, height_mm=60)
    diagram.add_box("first", "First", x_mm=40, y_mm=30, width_mm=30, height_mm=18)
    diagram.add_box("second", "Second", x_mm=40, y_mm=30, width_mm=30, height_mm=18)
    # Act
    with caplog.at_level(logging.INFO, logger=LOGGER):
        path = getattr(diagram, method)(tmp_path / f"overlap.{suffix}", save_debug=save_debug)
    records = [r for r in caplog.records if r.name == LOGGER]
    errors = "\n".join(r.getMessage() for r in records if r.levelno >= logging.ERROR)
    actual = (path.name, path.is_file(), path.with_suffix(".yaml").exists(),
              "R2" in errors, "first" in errors, "second" in errors,
              any(r.levelno == SUCCESS for r in records),
              path.with_stem(path.stem + "_debug").exists())
    # Assert
    assert actual == (f"overlap_FAILED.{suffix}", True, False, True, True, True, False, save_debug)


@pytest.mark.parametrize("method", ["save", "render_to_file"])
def test_valid_diagram_still_logs_success_and_writes_recipe(tmp_path, caplog, method):
    # Arrange
    fr.load_style("SCITEX")
    diagram = fr.Diagram(width_mm=120, height_mm=60)
    diagram.add_box("single", "Single", x_mm=60, y_mm=30, width_mm=30, height_mm=18)
    # Act
    with caplog.at_level(logging.INFO, logger=LOGGER):
        path = getattr(diagram, method)(tmp_path / "valid.png", save_debug=False)
    records = [r for r in caplog.records if r.name == LOGGER]
    actual = (path.name, path.is_file(), path.with_suffix(".yaml").is_file(),
              any(r.levelno == SUCCESS and "diagram saved" in r.getMessage()
                  for r in records), any(r.levelno >= logging.ERROR for r in records))
    # Assert
    assert actual == ("valid.png", True, True, True, False)


def test_failed_file_write_does_not_log_export_success(tmp_path, caplog):
    # Arrange
    fr.load_style("SCITEX")
    diagram = fr.Diagram(width_mm=120, height_mm=60)
    diagram.add_box("single", "Single", x_mm=60, y_mm=30, width_mm=30, height_mm=18)
    error = None
    # Act
    with caplog.at_level(logging.INFO, logger=LOGGER):
        try:
            diagram.save(tmp_path / "absent" / "image.png", save_debug=False)
        except FileNotFoundError as exc:
            error = type(exc)
    successes = [r for r in caplog.records if r.name == LOGGER and r.levelno == SUCCESS]
    # Assert
    assert (error, successes) == (FileNotFoundError, [])
