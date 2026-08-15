"""Tests for the disk scan that finds recipe/figure disagreements.

Real files on tmp_path with real mtimes, no mocks — the whole check is about
timestamps, so faking them would test the fake. One assertion per test, AAA
markers.
"""

from __future__ import annotations

import os

import pytest

from figrecipe._manuscript_hints._scan import (
    STALE_TOLERANCE_S,
    claim_id_for,
    scan_project,
)

RECIPE_BODY = "figrecipe: 0.1\ncalls: []\n"


def _touch(path, contents="x", age_s=0.0):
    """Create ``path`` and set its mtime ``age_s`` seconds into the past."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    if age_s:
        stamp = path.stat().st_mtime - age_s
        os.utime(path, (stamp, stamp))
    return path


@pytest.fixture
def project(tmp_path):
    """An empty project root."""
    return tmp_path


def _kinds(hints):
    return [hint.kind for hint in hints]


def test_matched_pair_written_together_yields_no_hint(project):
    # Arrange
    _touch(project / "figures" / "fig01.png")
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY)
    # Act
    hints = scan_project(project)
    # Assert
    assert hints == []


def test_image_newer_than_recipe_is_reported_stale(project):
    # Arrange
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY, age_s=600)
    _touch(project / "figures" / "fig01.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert _kinds(hints) == ["stale-recipe"]


def test_stale_message_says_which_side_is_newer(project):
    # Arrange
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY, age_s=600)
    _touch(project / "figures" / "fig01.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert "image is" in hints[0].message


def test_recipe_newer_than_image_is_reported_stale(project):
    # Arrange
    _touch(project / "figures" / "fig01.png", age_s=600)
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY)
    # Act
    hints = scan_project(project)
    # Assert
    assert _kinds(hints) == ["stale-recipe"]


def test_recipe_newer_message_tells_you_to_regenerate(project):
    # Arrange
    _touch(project / "figures" / "fig01.png", age_s=600)
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY)
    # Act
    hints = scan_project(project)
    # Assert
    assert "regenerate the figure" in hints[0].message


def test_drift_inside_the_tolerance_is_not_reported(project):
    # Arrange
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY, age_s=STALE_TOLERANCE_S / 2)
    _touch(project / "figures" / "fig01.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert hints == []


def test_image_without_recipe_is_reported_missing_recipe(project):
    # Arrange
    _touch(project / "figures" / "orphan.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert _kinds(hints) == ["missing-recipe"]


def test_missing_recipe_message_names_the_remedy(project):
    # Arrange
    _touch(project / "figures" / "orphan.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert "through figrecipe" in hints[0].message


def test_recipe_without_image_is_reported_missing_figure(project):
    # Arrange
    _touch(project / "figures" / "ghost.yaml", RECIPE_BODY)
    # Act
    hints = scan_project(project)
    # Assert
    assert _kinds(hints) == ["missing-figure"]


def test_ordinary_yaml_config_is_not_reported_as_a_missing_figure(project):
    # Arrange
    _touch(project / "config" / "settings.yaml", "database:\n  host: localhost\n")
    # Act
    hints = scan_project(project)
    # Assert
    assert hints == []


def test_skipped_directories_are_not_scanned(project):
    # Arrange
    _touch(project / "node_modules" / "pkg" / "logo.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert hints == []


def test_pdf_figures_are_scanned_too(project):
    # Arrange
    _touch(project / "figures" / "plot.pdf")
    # Act
    hints = scan_project(project)
    # Assert
    assert _kinds(hints) == ["missing-recipe"]


def test_hints_are_sorted_by_location(project):
    # Arrange
    _touch(project / "figures" / "b.png")
    _touch(project / "figures" / "a.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert [hint.location for hint in hints] == ["figures/a.png", "figures/b.png"]


def test_scan_is_stable_across_runs(project):
    # Arrange
    _touch(project / "figures" / "b.png")
    _touch(project / "figures" / "a.png")
    first = scan_project(project)
    # Act
    second = scan_project(project)
    # Assert
    assert [h.to_dict() for h in first] == [h.to_dict() for h in second]


def test_claim_id_strips_the_extension(project):
    # Arrange
    figure = project / "figures" / "fig01.png"
    # Act
    claim = claim_id_for(figure, project)
    # Assert
    assert claim == "figures/fig01"


def test_image_and_recipe_share_one_claim_id(project):
    # Arrange
    figure = project / "figures" / "fig01.png"
    recipe = project / "figures" / "fig01.yaml"
    # Act
    same = claim_id_for(figure, project) == claim_id_for(recipe, project)
    # Assert
    assert same is True


def test_stale_hint_is_bound_to_the_figures_claim(project):
    # Arrange
    _touch(project / "figures" / "fig01.yaml", RECIPE_BODY, age_s=600)
    _touch(project / "figures" / "fig01.png")
    # Act
    hints = scan_project(project)
    # Assert
    assert hints[0].claim_id == "figures/fig01"


# EOF
