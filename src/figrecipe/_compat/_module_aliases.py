"""sys.modules aliases for modules moved by #141.

The (a) layout option from lead msg b4e3dc7e: register transparent
aliases at the old import paths so legacy code keeps working AND gets
a single-fire ``DeprecationWarning`` directing it to the new path. No
flat shim files at the package root (the PS-108b threshold reason).
"""

from __future__ import annotations

import importlib
import sys
import warnings
from types import ModuleType
from typing import Mapping

# Old path → new path. Defined here so a single point of update covers
# any future moves of the same shape.
_MOVED: Mapping[str, str] = {
    "figrecipe._validator": "figrecipe._quality._validator",
    "figrecipe._linter_plugin": "figrecipe._quality._linter_plugin",
    "figrecipe._axis_alignment_checker": "figrecipe._quality._axis_alignment_checker",
    "figrecipe._axis_range_alignment": "figrecipe._quality._axis_range_alignment",
}


class _DeprecatedAliasModule(ModuleType):
    """A live ModuleType that proxies attribute access to the new module.

    Emits a single ``DeprecationWarning`` the first time anything is
    accessed via the old path. We use a real ``ModuleType`` subclass (not
    a bare proxy object) so ``from figrecipe._validator import X``,
    ``import figrecipe._validator as v``, and ``hasattr(v, ...)`` all
    behave like normal module access.
    """

    def __init__(self, old_name: str, new_name: str) -> None:
        super().__init__(old_name)
        # Don't use self.__dict__ for these so they don't pollute the
        # attribute lookup of the proxied module. Stash on the instance
        # via object-level slots-like attrs.
        object.__setattr__(self, "_alias_old_name", old_name)
        object.__setattr__(self, "_alias_new_name", new_name)
        object.__setattr__(self, "_alias_warned", False)
        object.__setattr__(self, "_alias_real", None)

    def _resolve(self) -> ModuleType:
        real = object.__getattribute__(self, "_alias_real")
        if real is None:
            real = importlib.import_module(
                object.__getattribute__(self, "_alias_new_name")
            )
            object.__setattr__(self, "_alias_real", real)
        return real

    def _warn_once(self) -> None:
        if object.__getattribute__(self, "_alias_warned"):
            return
        old = object.__getattribute__(self, "_alias_old_name")
        new = object.__getattribute__(self, "_alias_new_name")
        warnings.warn(
            f"figrecipe: {old} has moved to {new} (figrecipe #141 _quality "
            f"topical refactor). The old path is preserved for compatibility "
            f"and will be removed in figrecipe 1.0. Update your imports.",
            DeprecationWarning,
            stacklevel=3,
        )
        object.__setattr__(self, "_alias_warned", True)

    def __getattr__(self, name: str):
        # Module-level dunders (__name__, __doc__, __loader__, ...) are
        # handled by ModuleType already; __getattr__ only fires for
        # otherwise-missing attrs, which is exactly what we want to
        # forward to the new module.
        self._warn_once()
        return getattr(self._resolve(), name)


def install_module_aliases() -> None:
    """Register every old-path alias in ``sys.modules``.

    Idempotent: re-running is safe (existing aliases are skipped).
    No-op if the new module isn't importable yet (lets ``figrecipe``'s
    own bootstrap finish without circular-import surprises; the next
    explicit alias access will re-attempt resolution via ``_resolve``).
    """
    for old, new in _MOVED.items():
        if old in sys.modules:
            continue
        sys.modules[old] = _DeprecatedAliasModule(old, new)
