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

    def test_north_node_sits_at_top_center(self):
        # Arrange
        # Act
        pos = _circular_layout(["n", "e", "s", "w"], 0.0, 10.0, 0.0, 20.0)
        # Assert -- cx=5, cy=10, r=min(10,20)/2*0.8=4.0; start at top.
        assert pos["n"] == pytest.approx((5.0, 6.0))

    def test_east_node_sits_at_right_middle(self):
        # Arrange
        # Act
        pos = _circular_layout(["n", "e", "s", "w"], 0.0, 10.0, 0.0, 20.0)
        # Assert
        assert pos["e"] == pytest.approx((9.0, 10.0))

    def test_south_node_sits_at_bottom_center(self):
        # Arrange
        # Act
        pos = _circular_layout(["n", "e", "s", "w"], 0.0, 10.0, 0.0, 20.0)
        # Assert
        assert pos["s"] == pytest.approx((5.0, 14.0))

    def test_west_node_sits_at_left_middle(self):
        # Arrange
        # Act
        pos = _circular_layout(["n", "e", "s", "w"], 0.0, 10.0, 0.0, 20.0)
        # Assert
        assert pos["w"] == pytest.approx((1.0, 10.0))
