"""Tests for figrecipe's pyplot-substitution surface (figrecipe used AS `plt`)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

import figrecipe


# --------------------------------------------------------------------------
# The reported failure. neurovista's render_spatial_4x4_effect_grid.py died on
# `plt.rcParams` with a bare "module 'figrecipe' has no attribute 'rcParams'",
# which named neither the cause nor the remedy.
# --------------------------------------------------------------------------
def test_rcParams_names_the_style_system_instead_of_failing_bare():
    # Arrange
    name = "rcParams"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="load_style"):
        getattr(figrecipe, name)


def test_rcParams_says_why_it_is_not_proxied():
    # Arrange
    name = "rcParams"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="fights the style system"):
        getattr(figrecipe, name)


def test_figure_points_at_subplots():
    # Arrange
    name = "figure"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="figrecipe.subplots"):
        getattr(figrecipe, name)


def test_figure_explains_the_recorder_would_not_see_it():
    # Arrange
    name = "figure"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="invisible to the recorder"):
        getattr(figrecipe, name)


def test_savefig_points_at_figrecipe_save():
    # Arrange
    name = "savefig"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="figrecipe.save"):
        getattr(figrecipe, name)


def test_gca_explains_there_is_no_current_axes_state():
    # Arrange
    name = "gca"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="explicit-axes"):
        getattr(figrecipe, name)


def test_tight_layout_points_at_the_mm_layout_arguments():
    # Arrange
    name = "tight_layout"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="axes_width_mm"):
        getattr(figrecipe, name)


# --------------------------------------------------------------------------
# State-machine calls: the guidance must name the AXES method, and for the
# setter family that is `ax.set_<name>`, not `ax.<name>`.
# --------------------------------------------------------------------------
def test_xlabel_names_the_axes_setter_not_the_bare_name():
    # Arrange
    name = "xlabel"
    # Act
    # Assert
    with pytest.raises(AttributeError, match=r"ax\.set_xlabel"):
        getattr(figrecipe, name)


def test_xlabel_also_offers_the_combined_setter():
    # Arrange
    name = "xlabel"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="set_xyt"):
        getattr(figrecipe, name)


def test_plot_names_the_same_named_axes_method():
    # Arrange
    name = "plot"
    # Act
    # Assert
    with pytest.raises(AttributeError, match=r"ax\.plot"):
        getattr(figrecipe, name)


# --------------------------------------------------------------------------
# Proxied names: display/lifecycle only, so they cannot create an unrecorded
# artifact and are passed straight through.
# --------------------------------------------------------------------------
def test_close_is_proxied_to_pyplot():
    # Arrange
    expected = plt.close
    # Act
    actual = figrecipe.close
    # Assert
    assert actual is expected


def test_show_is_proxied_to_pyplot():
    # Arrange
    expected = plt.show
    # Act
    actual = figrecipe.show
    # Assert
    assert actual is expected


# --------------------------------------------------------------------------
# The catch-all, and its boundary: any OTHER pyplot name must still explain
# itself, while a genuine typo must NOT be dressed up as a pyplot question.
# --------------------------------------------------------------------------
def test_unlisted_pyplot_name_still_explains_the_partial_substitution():
    # Arrange: a real pyplot function with no entry in either table.
    name = "magnitude_spectrum"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="NOT a drop-in pyplot"):
        getattr(figrecipe, name)


def test_unknown_non_pyplot_name_keeps_the_plain_message():
    # Arrange
    name = "definitely_not_a_real_attribute_xyz"
    # Act
    # Assert
    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(figrecipe, name)


def test_unknown_non_pyplot_name_does_not_mention_pyplot():
    # Arrange
    name = "definitely_not_a_real_attribute_xyz"
    # Act
    try:
        getattr(figrecipe, name)
        message = ""
    except AttributeError as exc:
        message = str(exc)
    # Assert
    assert "pyplot" not in message


# --------------------------------------------------------------------------
# Regression: the surface that already worked must keep working, including the
# lazy-attribute path this change sits behind.
# --------------------------------------------------------------------------
def test_subplots_still_resolves():
    # Arrange
    name = "subplots"
    # Act
    resolved = getattr(figrecipe, name)
    # Assert
    assert callable(resolved)


def test_save_still_resolves():
    # Arrange
    name = "save"
    # Act
    resolved = getattr(figrecipe, name)
    # Assert
    assert callable(resolved)
