#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What a ``--host`` bind contributes to ALLOWED_HOSTS -- figrecipe's wiring.

The derivation (``_hosts_to_allow``) is scitex-app's, imported below; this
module only carries what is figrecipe-specific: the env var settings.py reads,
and the merge that writes it before Django configures.

Why this exists at all: ``figrecipe gui serve --host 0.0.0.0`` binds every
interface, and a request then arrives with the REAL interface address in its
Host header. ``"0.0.0.0"`` in ALLOWED_HOSTS never matches that, so every
non-loopback caller got 400 (measured 2026-09-02 against 0.34.6). Binding to
an address is the statement that you intend to be reached on it, so the bind
contributes what it implies.
"""

# The derivation itself lives in scitex-app since 0.10.1 (scitex-app #105,
# released 2026-09-02): loopback -> nothing, a concrete address -> itself,
# 0.0.0.0 -> hostname + every interface's IPv4 read from the interfaces, never
# from name resolution. Until that release this file carried scholar's block
# verbatim; the copy is gone, this import is what runs. ``_standalone`` is a
# PRIVATE module -- scitex-app has offered a public re-export in their next
# minor; switch this line to it when it exists.
from scitex_app._standalone import _hosts_to_allow

# ── figrecipe's wiring ────────────────────────────────────────────────────────

ENV_VAR = "SCITEX_ALLOWED_HOSTS"
"""The env var settings.py appends to ALLOWED_HOSTS.

Named after scitex-app's, not after this package: figrecipe's launcher already
routes through scitex-app's run_standalone, whose _allowed_hosts reads
exactly this variable, and the derivation now comes from there too -- one
name for one thing, whichever layer ends up reading it.
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
