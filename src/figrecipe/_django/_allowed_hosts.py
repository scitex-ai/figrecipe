#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What a ``--host`` bind contributes to ALLOWED_HOSTS. Pure functions.

VERBATIM COPY of scitex-scholar's ``_django/_server.py`` (PR #137, commit
ad439af, 2026-09-02), by scitex-hub's ruling as coordinator: three apps need
the same rule, so they carry the same function -- not three implementations
that drift -- until it lands in scitex-app's ``_allowed_hosts`` and this file
becomes a one-line import. Keep it byte-for-byte with scholar's; fix bugs
there first.

Why this exists at all: ``figrecipe gui serve --host 0.0.0.0`` binds every
interface, and a request then arrives with the REAL interface address in its
Host header. ``"0.0.0.0"`` in ALLOWED_HOSTS never matches that, so every
non-loopback caller got 400 (measured 2026-09-02 against 0.34.6). Binding to
an address is the statement that you intend to be reached on it, so the bind
contributes what it implies.
"""

_LOOPBACK = ("127.0.0.1", "localhost")
_BIND_ALL = "0.0.0.0"


def _interface_ipv4_addresses() -> list[str]:
    """Every IPv4 address assigned to a network interface on this machine.

    Read from the INTERFACES (SIOCGIFADDR per `socket.if_nameindex()` entry),
    not from name resolution. `getaddrinfo(gethostname())` was the first
    attempt and it FAILED THE LIVE CHECK while passing the unit test: inside a
    container the hostname resolves to an address that is not the LAN
    interface, so `--host 0.0.0.0` still answered 400 to the real address.
    The unit test had only asserted the hostname was present -- it could not
    fail for the case that mattered. Interfaces cannot lie about which
    addresses they hold. Linux/macOS ioctl; returns [] where unavailable.
    """
    import socket

    try:
        import fcntl
        import struct
    except ImportError:  # not a POSIX platform
        return []

    _SIOCGIFADDR = 0x8915
    found: list[str] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for _, name in socket.if_nameindex():
            try:
                packed = fcntl.ioctl(
                    s.fileno(),
                    _SIOCGIFADDR,
                    struct.pack("256s", name[:15].encode()),
                )
            except OSError:
                continue  # interface with no IPv4 address
            addr = socket.inet_ntoa(packed[20:24])
            if not addr.startswith("127.") and addr not in found:
                found.append(addr)
    return found


def _local_addresses() -> list[str]:
    """This machine's hostname plus every IPv4 address its interfaces hold.

    Used only for the 0.0.0.0 bind. Loopback is excluded because settings.py
    already lists it.
    """
    import socket

    found: list[str] = []
    hostname = socket.gethostname()
    if hostname:
        found.append(hostname)
    found.extend(a for a in _interface_ipv4_addresses() if a not in found)
    return found


def _hosts_to_allow(host: str) -> list[str]:
    """What a given ``--host`` bind implies for ALLOWED_HOSTS. Pure function.

    Binding to an address IS the statement that you intend to be reached on
    it, so contribute it rather than making the caller set an env var to
    permit what they already asked for:

        127.0.0.1 / localhost   -> []            settings.py lists loopback
        0.0.0.0                 -> hostname + this machine's interface addresses
        anything else           -> [host]

    The 0.0.0.0 rule is what makes DEBUG=False the safe default WITHOUT
    reintroducing the bug #126 fixed: a bind-all server receives requests whose
    Host header is the real interface address, and "0.0.0.0" in ALLOWED_HOSTS
    never matches that. Measured 2026-09-02 on the published 1.9.0 wheel:
    `--host 0.0.0.0` with DJANGO_DEBUG=false answered 400 to every real
    address while loopback answered 200.
    """
    if host in _LOOPBACK:
        return []
    if host == _BIND_ALL:
        return _local_addresses()
    return [host]


# ── figrecipe's wiring (NOT part of the verbatim copy above) ─────────────────

ENV_VAR = "SCITEX_ALLOWED_HOSTS"
"""The env var settings.py appends to ALLOWED_HOSTS.

Named after scitex-app's, not after this package: figrecipe's launcher already
routes through scitex-app's run_standalone, whose _allowed_hosts reads
exactly this variable. When the enumeration above lands there, figrecipe drops
its copy and nothing changes for users.
"""


def apply_bound_host(host: str, environ) -> list[str]:
    """Merge what host contributes into environ[ENV_VAR]. Returns the list.

    Pure over environ (any mutable mapping), so the tests hand it a dict
    and production hands it os.environ. Existing entries survive -- a
    proxy or tunnel name the operator configured stays alongside the bind
    address -- and nothing is duplicated. Must run BEFORE django.setup(),
    because settings.py reads the variable once, at import.
    """
    contributed = _hosts_to_allow(host)
    hosts = [h.strip() for h in environ.get(ENV_VAR, "").split(",") if h.strip()]
    for h in contributed:
        if h not in hosts:
            hosts.append(h)
    if hosts:
        environ[ENV_VAR] = ",".join(hosts)
    return hosts


__all__ = ["ENV_VAR", "_hosts_to_allow", "apply_bound_host"]

# EOF
