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
    module_path = "figrecipe._diagram._diagram._io"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _save(tmp_path, x_mm, suffix=".png"):
    diagram = Diagram(width_mm=110, height_mm=45)
    diagram.add_box(
        "input", "Input", shape="box", x_mm=x_mm, y_mm=22, width_mm=35, height_mm=18
    )
    return diagram.save(tmp_path / ("flow" + suffix), save_debug=False)


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_rejected_diagram_logs_error_with_offending_id(tmp_path, caplog, suffix):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 0, suffix)
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.name.endswith("._diagram._io") and record.levelno >= logging.ERROR
    ]
    # Assert
    assert any(
        "input" in message and "validation failed" in message for message in errors
    )


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_rejected_diagram_does_not_log_success(tmp_path, caplog, suffix):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 0, suffix)
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name.endswith("._diagram._io")
    ]
    # Assert
    assert not any(message.startswith("diagram saved:") for message in messages)


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_rejected_diagram_preserves_failed_diagnostic(tmp_path, suffix):
    # Arrange
    expected = tmp_path / ("flow_FAILED" + suffix)
    # Act
    path = _save(tmp_path, 0, suffix)
    # Assert
    assert path == expected and path.is_file()


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_valid_diagram_logs_success(tmp_path, caplog, suffix):
    # Arrange
    caplog.set_level(logging.DEBUG)
    # Act
    _save(tmp_path, 25, suffix)
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name.endswith("._diagram._io")
    ]
    # Assert
    assert any(message.startswith("diagram saved:") for message in messages)


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_valid_diagram_preserves_requested_path(tmp_path, suffix):
    # Arrange
    expected = tmp_path / ("flow" + suffix)
    # Act
    path = _save(tmp_path, 25, suffix)
    # Assert
    assert path == expected and path.is_file()


_GEOMETRY_FIELDS = (
    "id",
    "source_dx",
    "source_dy",
    "target_dx",
    "target_dy",
    "label_offset_mm",
    "margin_mm",
)


def _positioned_arrow_diagram():
    from figrecipe import Diagram

    diagram = Diagram(width_mm=110, height_mm=50)
    diagram.add_box(
        "input", "Input", shape="box", x_mm=25, y_mm=22, width_mm=30, height_mm=20
    )
    diagram.add_box(
        "output", "Output", shape="box", x_mm=85, y_mm=22, width_mm=30, height_mm=20
    )
    diagram.add_arrow(
        "input",
        "output",
        label="Convert",
        source_dx=1,
        source_dy=2,
        target_dx=-3,
        target_dy=-2,
        label_offset_mm=(0, 6),
        margin_mm=2,
    )
    return diagram


@pytest.mark.parametrize("field", _GEOMETRY_FIELDS)
def test_arrow_geometry_survives_yaml_recipe(field):
    # Arrange
    import yaml

    from figrecipe import Diagram

    diagram = _positioned_arrow_diagram()
    expected = getattr(diagram._arrows[0], field)
    # Act
    data = yaml.safe_load(yaml.safe_dump(diagram.to_dict()))
    restored = Diagram.from_dict(data)
    # Assert
    assert getattr(restored._arrows[0], field) == expected


def test_legacy_arrow_recipe_uses_original_geometry_defaults():
    # Arrange
    from figrecipe import Diagram

    data = _positioned_arrow_diagram().to_dict()
    for field in _GEOMETRY_FIELDS:
        data["arrows"][0].pop(field, None)
    # Act
    arrow = Diagram.from_dict(data)._arrows[0]
    actual = {field: getattr(arrow, field) for field in _GEOMETRY_FIELDS}
    # Assert
    assert actual == {
        "id": None,
        "source_dx": 0.0,
        "source_dy": 0.0,
        "target_dx": 0.0,
        "target_dy": 0.0,
        "label_offset_mm": None,
        "margin_mm": None,
    }


def test_label_offset_recipe_remains_valid_when_rendered():
    # Arrange
    import matplotlib.pyplot as plt

    from figrecipe import Diagram

    diagram = _positioned_arrow_diagram()
    # Act
    original, _ = diagram.render()
    replayed, _ = Diagram.from_dict(diagram.to_dict()).render()
    failures = (original._figrecipe_diagram_failed, replayed._figrecipe_diagram_failed)
    plt.close(original)
    plt.close(replayed)
    # Assert
    assert failures == (False, False)


@pytest.fixture(params=["png", "svg", "pdf"])
def default_save_format(request):
    import matplotlib as mpl

    with mpl.rc_context({"savefig.format": request.param}):
        yield request.param


@pytest.fixture(params=["save", "render_to_file"])
def diagram_save_method(request):
    return request.param


@pytest.fixture(params=[False, True])
def valid_diagram(request):
    diagram = Diagram(width_mm=110, height_mm=45)
    diagram.add_box(
        "input",
        "Input",
        shape="box",
        x_mm=25 if request.param else 0,
        y_mm=22,
        width_mm=35,
        height_mm=18,
    )
    return diagram, request.param


def test_extensionless_save_returns_existing_image(
    tmp_path, default_save_format, diagram_save_method, valid_diagram
):
    # Arrange
    diagram, _ = valid_diagram
    # Act
    path = getattr(diagram, diagram_save_method)(tmp_path / "flow", save_debug=False)
    # Assert
    assert path.is_file()


def test_extensionless_save_returns_default_format_path(
    tmp_path, default_save_format, diagram_save_method, valid_diagram
):
    # Arrange
    diagram, valid = valid_diagram
    stem = "flow" if valid else "flow_FAILED"
    expected = tmp_path / f"{stem}.{default_save_format}"
    # Act
    path = getattr(diagram, diagram_save_method)(tmp_path / "flow", save_debug=False)
    # Assert
    assert path == expected


def test_extensionless_png_receives_same_crop_as_explicit_png(
    tmp_path, diagram_save_method, valid_diagram
):
    # Arrange
    import matplotlib as mpl
    from PIL import Image

    diagram, valid = valid_diagram
    suffix = "" if valid else "_FAILED"
    # Act
    with mpl.rc_context({"savefig.format": "png"}):
        getattr(diagram, diagram_save_method)(tmp_path / "implicit", save_debug=False)
        getattr(diagram, diagram_save_method)(
            tmp_path / "explicit.png", save_debug=False
        )
    with Image.open(tmp_path / f"implicit{suffix}.png") as implicit:
        implicit_size = implicit.size
    with Image.open(tmp_path / f"explicit{suffix}.png") as explicit:
        explicit_size = explicit.size
    # Assert
    assert implicit_size == explicit_size
