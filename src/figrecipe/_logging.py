#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loosely-coupled scitex-logging for figrecipe console output.

figrecipe emits its save / reproducibility-validation status through
scitex-logging WHEN it is installed, so those lines carry the same
``INFO:/SUCC:/WARN:`` prefixes and colours as the rest of the SciTeX
ecosystem (``scitex.io.save``, ``@stx.session`` scripts). This removes the
inconsistency where figrecipe's bare ``print("Saved: ...")`` lines appeared
uncoloured and unprefixed right next to scitex-logging output.

Loosely coupled, leaf-respecting -- the SAME policy as the scitex-clew
integration (see ``_serializer/_clew.py``): scitex-logging is reached via
scitex-dev's ``try_import_optional``. If scitex-logging (or scitex-dev) is
absent, figrecipe falls back to plain ``print`` so it stays dependency-light
and behaves exactly as before when used standalone.
"""

from __future__ import annotations

from typing import Any


class _PrintLogger:
    """Fallback logger used when scitex-logging is unavailable.

    Preserves figrecipe's historical standalone behaviour: save confirmations
    stay visible on stdout (``info``/``success`` unprefixed, as the old
    ``print`` calls were; ``warning``/``error`` get a short prefix) without
    requiring any stdlib logging handler configuration.
    """

    def info(self, msg: str, *a: Any, **k: Any) -> None:
        print(msg)

    def success(self, msg: str, *a: Any, **k: Any) -> None:
        print(msg)

    def warning(self, msg: str, *a: Any, **k: Any) -> None:
        print(f"WARN: {msg}")

    def error(self, msg: str, *a: Any, **k: Any) -> None:
        print(f"ERRO: {msg}")

    def debug(self, msg: str, *a: Any, **k: Any) -> None:
        pass


def get_logger(name: str = "figrecipe") -> Any:
    """Return scitex-logging's logger if available, else a print fallback.

    The returned object always supports ``info``/``success``/``warning``/
    ``error``/``debug`` so figrecipe call sites stay uniform across backends.

    Parameters
    ----------
    name : str
        Logger name (default ``"figrecipe"``).
    """
    try:
        from scitex_dev import try_import_optional

        slog = try_import_optional("scitex_logging")
        if slog is not None and hasattr(slog, "getLogger"):
            return slog.getLogger(name)
    except Exception:  # optional path: scitex-logging / scitex-dev unavailable
        pass
    return _PrintLogger()


__all__ = ["get_logger"]

# EOF
