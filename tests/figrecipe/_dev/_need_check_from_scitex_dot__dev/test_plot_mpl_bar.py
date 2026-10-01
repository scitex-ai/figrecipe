"""Plotting-package smoke controls ported from the retired umbrella namespace."""

import figrecipe


def test_plt_module_has_dunder_path():
    # Arrange
    package = figrecipe
    # Act
    package_path = getattr(package, "__path__", None)
    # Assert
    assert package_path is not None


def test_plt_subpackages_importable():
    # Arrange
    from figrecipe import pyplot
    from figrecipe._dev import demo_plotters

    # Act
    imports = (pyplot.subplots is figrecipe.subplots, "bar" in demo_plotters.REGISTRY)
    # Assert
    assert imports == (True, True)
