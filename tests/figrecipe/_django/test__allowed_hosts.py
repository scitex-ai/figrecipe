#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_hosts_to_allow: what a --host bind contributes to ALLOWED_HOSTS.

VERBATIM from scitex-scholar's ``tests/scitex_scholar/_django/test__server.py``
(PR #137, commit ad439af), import path adjusted. The 0.0.0.0 case is the one
that makes DEBUG=False a safe DEFAULT: measured 2026-09-02, ``--host 0.0.0.0``
under DJANGO_DEBUG=false answered 400 to every real interface address, because
"0.0.0.0" in ALLOWED_HOSTS never matches a Host header.
"""


def test_hosts_to_allow_loopback_contributes_nothing():
    # Arrange
    from figrecipe._django._allowed_hosts import _hosts_to_allow

    # Act
    contributed = _hosts_to_allow("127.0.0.1")
    # Assert
    assert contributed == []


def test_hosts_to_allow_specific_address_contributes_itself():
    # Arrange
    from figrecipe._django._allowed_hosts import _hosts_to_allow

    # Act
    contributed = _hosts_to_allow("100.64.0.4")
    # Assert
    assert contributed == ["100.64.0.4"]


def test_hosts_to_allow_bind_all_contributes_this_machines_hostname():
    # Arrange
    import socket

    from figrecipe._django._allowed_hosts import _hosts_to_allow

    # Act
    contributed = _hosts_to_allow("0.0.0.0")
    # Assert
    assert socket.gethostname() in contributed


def test_hosts_to_allow_bind_all_never_contributes_the_literal_wildcard():
    """Control: bind-all must widen to THIS machine, never to everything."""
    # Arrange
    from figrecipe._django._allowed_hosts import _hosts_to_allow

    # Act
    contributed = _hosts_to_allow("0.0.0.0")
    # Assert
    assert "*" not in contributed and "0.0.0.0" not in contributed


def test_hosts_to_allow_bind_all_contributes_a_real_interface_address():
    """The test that the first implementation could NOT fail.

    It used getaddrinfo(gethostname()), passed the hostname assertion above,
    and still answered 400 to the real LAN address in a live check. Derive the
    expected address by an INDEPENDENT method -- the UDP-connect trick reads
    the kernel's chosen source address without sending a packet -- so the
    assertion is not the implementation checking itself.
    """
    # Arrange
    import socket

    from figrecipe._django._allowed_hosts import _hosts_to_allow

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("10.255.255.255", 1))  # no packet is sent for UDP connect
        expected = s.getsockname()[0]
    # Act
    contributed = _hosts_to_allow("0.0.0.0")
    # Assert
    assert expected in contributed, f"{expected!r} not in {contributed!r}"


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
