#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_bound_host: figrecipe's wiring around scitex-app's hosts_to_allow.

The derivation's own tests (loopback -> nothing, concrete -> itself, 0.0.0.0 ->
this machine's interface addresses by an independent route, never "*") live
with the function in scitex-app since 0.10.1. What is tested here is only what
figrecipe adds: the merge into the env var settings.py reads.
"""


# ── figrecipe's wiring: apply_bound_host merges into a mapping, pure ──────────


def test_apply_bound_host_bind_all_writes_the_env_var():
    # Arrange
    from figrecipe._django._allowed_hosts import ENV_VAR, apply_bound_host

    environ = {}
    # Act
    apply_bound_host("0.0.0.0", environ)
    # Assert
    assert ENV_VAR in environ


def test_apply_bound_host_keeps_operator_configured_names():
    """A proxy/tunnel name already in the env survives the merge."""
    # Arrange
    from figrecipe._django._allowed_hosts import ENV_VAR, apply_bound_host

    environ = {ENV_VAR: "figs.example.org"}
    # Act
    hosts = apply_bound_host("100.64.0.4", environ)
    # Assert
    assert hosts == ["figs.example.org", "100.64.0.4"]


def test_apply_bound_host_does_not_duplicate_an_existing_entry():
    # Arrange
    from figrecipe._django._allowed_hosts import ENV_VAR, apply_bound_host

    environ = {ENV_VAR: "100.64.0.4"}
    # Act
    hosts = apply_bound_host("100.64.0.4", environ)
    # Assert
    assert hosts == ["100.64.0.4"]


def test_apply_bound_host_loopback_leaves_the_env_untouched():
    """Control: a loopback bind contributes nothing and writes nothing."""
    # Arrange
    from figrecipe._django._allowed_hosts import ENV_VAR, apply_bound_host

    environ = {}
    # Act
    apply_bound_host("127.0.0.1", environ)
    # Assert
    assert ENV_VAR not in environ


# EOF
