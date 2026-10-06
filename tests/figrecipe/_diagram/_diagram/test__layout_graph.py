"""Smoke import mirror for figrecipe._diagram._diagram._layout_graph.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest

from figrecipe._diagram._diagram._layout_graph import _circular_layout


def test_import__diagram__diagram__layout_graph_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._diagram._diagram._layout_graph'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


class TestCircularLayoutContract:
    """Pin the ellipse-mapping contract before deduplicating onto radial_positions."""

    def test_four_nodes_land_on_cardinal_points_of_the_ellipse(self):
        # Arrange
        # Act
        pos = _circular_layout(["n", "e", "s", "w"], 0.0, 10.0, 0.0, 20.0)
        # Assert -- cx=5, cy=10, r=min(10,20)/2*0.8=4.0 on BOTH axes;
        # angles start at top (-pi/2), counter-clockwise in math convention.
        assert pos["n"] == pytest.approx((5.0, 6.0))
        assert pos["e"] == pytest.approx((9.0, 10.0))
        assert pos["s"] == pytest.approx((5.0, 14.0))
        assert pos["w"] == pytest.approx((1.0, 10.0))
