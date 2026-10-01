#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``figrecipe.from_stats_plot_spec`` (neutral stats plot spec -> recipe).

The fixture specs are hand-written JSON-shaped dicts: figrecipe must accept the
spec without importing its producer (scitex-stats).
"""

import copy

import pytest

import figrecipe as fr
from figrecipe._integrations._stats_plot_spec import validate_stats_plot_spec


def _group(name, pos, values):
    n = len(values)
    mean = sum(values) / n
    return {
        "name": name, "position": pos, "values": values,
        "jitter": [((i * 37) % 11 - 5) / 50 for i in range(n)],
        "n_text": r"$\mathit{n}$ = %d" % n,
        "summary": {"n": n, "mean": mean, "ci_lower": mean - 0.3, "ci_upper": mean + 0.3,
                    "median": sorted(values)[n // 2], "q1": min(values), "q3": max(values)},
    }


@pytest.fixture
def groups_spec():
    return {
        "schema": "scitex-stats.plot-spec", "version": 1, "kind": "groups",
        "test": {"key": "anova", "method": "One-way ANOVA"},
        "groups": [
            _group("A", 0, [5.1, 4.9, 5.6, 5.8, 6.0]),
            _group("B", 1, [6.3, 6.8, 6.1, 7.0, 6.6]),
            _group("C", 2, [5.5, 6.0, 5.9, 6.2, 5.8]),
        ],
        "layers": [{"type": "box"}, {"type": "points"}, {"type": "center", "estimator": "mean_ci"}],
        "annotations": {
            "brackets": [
                {"group1": 0, "group2": 1, "p_value": 0.0004, "text": r"$\mathit{p}$ < .001", "tier": 0},
                {"group1": 1, "group2": 2, "p_value": 0.002, "text": r"$\mathit{p}$ = .002", "tier": 1},
                {"group1": 0, "group2": 2, "p_value": 0.03, "text": r"$\mathit{p}$ = .030", "tier": 2},
            ],
            "statistic": r"$\mathit{F}$(2, 12) = 20.10, $\mathit{p}$ < .001", "effect_size": "η² = .77",
            "n_labels": True, "show_stars": False,
        },
        "axes": {"x": {"label": ""}, "y": {"label": "Value"}},
        "style": {"width_mm": 85, "height_mm": 68, "font_size_pt": 7, "jitter_seed": 42,
                  "palette": ["#0072B2", "#D55E00", "#009E73"]},
    }


def _stat_annotations(recipe_text):
    return recipe_text.count("function: stat_annotation")


def test_recipe_records_one_native_stat_annotation_per_bracket(groups_spec, tmp_path):
    # Arrange
    fig, _ax = fr.from_stats_plot_spec(groups_spec)
    # Act
    fr.save(fig, tmp_path / "anova.png", validate=False, verbose=False)
    # Assert
    assert _stat_annotations((tmp_path / "anova.yaml").read_text()) == 3


def test_recipe_replays_after_save(groups_spec, tmp_path):
    # Arrange
    fig, _ax = fr.from_stats_plot_spec(groups_spec)
    fr.save(fig, tmp_path / "anova.png", validate=False, verbose=False)
    # Act
    replayed, _ = fr.reproduce(tmp_path / "anova.yaml")
    # Assert
    assert replayed is not None


def test_stacked_brackets_sit_on_distinct_heights(groups_spec, tmp_path):
    # Arrange
    fig, _ax = fr.from_stats_plot_spec(groups_spec)
    fr.save(fig, tmp_path / "anova.png", validate=False, verbose=False)
    import yaml

    recipe = yaml.safe_load((tmp_path / "anova.yaml").read_text())
    decorations = next(iter(recipe["axes"].values()))["decorations"]
    # Act
    ys = [d["kwargs"]["y"] for d in decorations if d["function"] == "stat_annotation"]
    # Assert
    assert len(set(ys)) == 3


def test_correlation_spec_builds(tmp_path):
    # Arrange
    spec = {
        "schema": "scitex-stats.plot-spec", "version": 1, "kind": "correlation",
        "test": {"key": "pearson", "method": "Pearson correlation"},
        "xy": {"x": [1, 2, 3, 4], "y": [1.2, 1.9, 3.2, 3.9]},
        "layers": [{"type": "scatter"}, {"type": "regression", "x": [1, 4], "y": [1.1, 4.0],
                                         "lower": [0.8, 3.7], "upper": [1.4, 4.3]}],
        "annotations": {"brackets": []}, "axes": {"x": {"label": "x"}, "y": {"label": "y"}},
        "style": {"width_mm": 85, "height_mm": 68},
    }
    fig, _ax = fr.from_stats_plot_spec(spec)
    # Act
    fr.save(fig, tmp_path / "r.png", validate=False, verbose=False)
    # Assert
    assert (tmp_path / "r.yaml").exists()


def test_unknown_version_is_rejected(groups_spec):
    # Arrange
    spec = copy.deepcopy(groups_spec)
    spec["version"] = 99
    # Act
    def call():
        return validate_stats_plot_spec(spec)
    # Assert
    with pytest.raises(ValueError, match="version"):
        call()


def test_foreign_document_is_rejected():
    # Arrange
    spec = {"schema": "something-else", "version": 1}
    # Act
    def call():
        return validate_stats_plot_spec(spec)
    # Assert
    with pytest.raises(ValueError, match="scitex-stats.plot-spec"):
        call()


def test_import_endpoint_writes_recipe_into_working_dir(groups_spec, tmp_path):
    # Arrange
    django = pytest.importorskip("django")
    import json
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()
    from django.test import RequestFactory

    from figrecipe._django.handlers import HANDLERS

    request = RequestFactory().post(
        f"/api/import/stats-plot-spec?working_dir={tmp_path}",
        data=json.dumps({"spec": groups_spec}), content_type="application/json",
    )
    # Act
    payload = json.loads(HANDLERS["api/import/stats-plot-spec"](request, None).content)
    # Assert
    assert (tmp_path / payload["file"]).exists()


# EOF
