"""Smoke import mirror for figrecipe._diagram._diagram._io.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


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


_GEOMETRY_FIELDS = ("id", "source_dx", "source_dy", "target_dx", "target_dy",
                    "label_offset_mm", "margin_mm")


def _positioned_arrow_diagram():
    from figrecipe import Diagram

    diagram = Diagram(width_mm=110, height_mm=50)
    diagram.add_box("input", "Input", shape="box", x_mm=25, y_mm=22,
                    width_mm=30, height_mm=20)
    diagram.add_box("output", "Output", shape="box", x_mm=85, y_mm=22,
                    width_mm=30, height_mm=20)
    diagram.add_arrow("input", "output", label="Convert", source_dx=1, source_dy=2,
                      target_dx=-3, target_dy=-2, label_offset_mm=(0, 6), margin_mm=2)
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
    assert actual == {"id": None, "source_dx": 0.0, "source_dy": 0.0,
                      "target_dx": 0.0, "target_dy": 0.0,
                      "label_offset_mm": None, "margin_mm": None}


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
