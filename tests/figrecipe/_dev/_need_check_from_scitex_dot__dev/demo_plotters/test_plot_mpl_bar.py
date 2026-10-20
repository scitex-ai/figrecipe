"""Smoke control for FigRecipe's owning demo-plotter package."""

from figrecipe._dev import demo_plotters


def test_demo_plotters_module_loads():
    # Arrange
    package = demo_plotters
    # Act
    package_path = getattr(package, "__path__", None)
    # Assert
    assert package_path is not None
