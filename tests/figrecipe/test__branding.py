#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for branding module.

Real-collaborator tests: each test mutates ``os.environ`` directly and
restores it via a ``yield``-based fixture (no ``unittest.mock.patch``).
The branding module reads ``FIGRECIPE_BRAND`` / ``FIGRECIPE_ALIAS`` at
import time, so the fixture also ``importlib.reload``s it under the
chosen env, then reloads it again under defaults on teardown.
"""

import importlib
import os

import pytest

import figrecipe._branding as branding


def _apply_brand(brand: str, alias: str) -> None:
    os.environ["FIGRECIPE_BRAND"] = brand
    os.environ["FIGRECIPE_ALIAS"] = alias
    importlib.reload(branding)


@pytest.fixture
def _branding_env():
    """Snapshot + restore FIGRECIPE_BRAND/ALIAS and reload module."""
    saved_brand = os.environ.get("FIGRECIPE_BRAND")
    saved_alias = os.environ.get("FIGRECIPE_ALIAS")
    try:
        yield _apply_brand
    finally:
        if saved_brand is None:
            os.environ.pop("FIGRECIPE_BRAND", None)
        else:
            os.environ["FIGRECIPE_BRAND"] = saved_brand
        if saved_alias is None:
            os.environ.pop("FIGRECIPE_ALIAS", None)
        else:
            os.environ["FIGRECIPE_ALIAS"] = saved_alias
        importlib.reload(branding)


class TestRebrandText:
    """Tests for ``figrecipe._branding.rebrand_text``."""

    def test_default_brand_returns_text_unchanged(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("figrecipe", "fr")
        text = "import figrecipe as fr"
        # Act
        result = branding.rebrand_text(text)
        # Assert
        assert result == text

    def test_scitex_plt_rebrands_import_statement(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        text = "import figrecipe as fr"
        # Act
        result = branding.rebrand_text(text)
        # Assert
        assert result == "import scitex.plt as plt"

    def test_scitex_plt_rebrands_variable_usage_in_examples(
        self, _branding_env
    ):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        text = ">>> fr.subplots()"
        # Act
        result = branding.rebrand_text(text)
        # Assert
        assert result == ">>> plt.subplots()"

    def test_scitex_plt_rebrands_from_import_statement(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        text = "from figrecipe import utils"
        # Act
        result = branding.rebrand_text(text)
        # Assert
        assert result == "from scitex.plt import utils"

    def test_none_input_returns_none(self):
        # Arrange
        # Arrange
        # Act
        # Assert
        from figrecipe._branding import rebrand_text
        # Act
        result = rebrand_text(None)
        # Assert
        assert result is None

    def test_preserves_url_domain_when_rebranding(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        text = "https://github.com/user/figrecipe"
        # Act
        result = branding.rebrand_text(text)
        # Assert
        assert "github.com" in result


class TestGetBrandedImportExample:
    """Tests for ``figrecipe._branding.get_branded_import_example``."""

    def test_default_brand_returns_import_figrecipe_as_fr(
        self, _branding_env
    ):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("figrecipe", "fr")
        # Act
        result = branding.get_branded_import_example()
        # Assert
        assert result == "import figrecipe as fr"

    def test_submodule_brand_returns_from_scitex_import_plt(
        self, _branding_env
    ):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        # Act
        result = branding.get_branded_import_example()
        # Assert
        assert result == "from scitex import plt as plt"


class TestGetMcpServerName:
    """Tests for ``figrecipe._branding.get_mcp_server_name``."""

    def test_default_brand_returns_figrecipe_server_name(
        self, _branding_env
    ):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("figrecipe", "fr")
        # Act
        result = branding.get_mcp_server_name()
        # Assert
        assert result == "figrecipe"

    def test_dotted_brand_converts_dots_to_dashes(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        # Act
        result = branding.get_mcp_server_name()
        # Assert
        assert result == "scitex-plt"


class TestGetMcpInstructions:
    """Tests for ``figrecipe._branding.get_mcp_instructions``."""

    def test_instructions_contain_configured_brand_name(
        self, _branding_env
    ):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        # Act
        result = branding.get_mcp_instructions()
        # Assert
        assert "scitex.plt" in result

    def test_instructions_mention_mcp_server(self, _branding_env):
        # Arrange
        # Arrange
        # Act
        # Assert
        _branding_env("scitex.plt", "plt")
        # Act
        result = branding.get_mcp_instructions()
        # Assert
        assert "MCP server" in result


# EOF
