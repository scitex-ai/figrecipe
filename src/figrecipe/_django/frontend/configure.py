#!/usr/bin/env python3
"""Configure figrecipe frontend build environment.

Creates a symlink from ./scitex-ui-types → scitex_ui's static directory, so
TypeScript (tsconfig paths) can find a pip-installed scitex-ui for a bare
`scitex-ui/...` specifier.

NOTE (dependency alignment): the frontend no longer imports that way. Every
`@scitex/ui` import uses the deep source path the vite alias and tsconfig
`paths` resolve against the sibling OWNER CHECKOUT, so neither this symlink nor
its tsconfig mapping is part of the build; `tests/scitexUiContract.test.ts`
fails if a bare `scitex-ui/...` specifier comes back. This script is kept for a
manual, pip-only workflow and is not run by CI.

Run once after install:
    python configure.py
"""

import os
import sys
from pathlib import Path

import scitex_logging as slogging

log = slogging.getLogger(__name__)
console = slogging.getConsole(f"{__name__}.console")

FRONTEND_DIR = Path(__file__).parent
LINK_NAME = FRONTEND_DIR / "scitex-ui-types"


def main() -> int:
    try:
        import scitex_ui

        static_dir = scitex_ui.get_static_dir()
    except ImportError:
        log.error("ERROR: scitex-ui is not installed.")
        log.error("  pip install scitex-ui")
        return 1

    if not static_dir.is_dir():
        log.error(f"ERROR: static dir not found: {static_dir}")
        return 1

    # Remove stale symlink
    if LINK_NAME.is_symlink() or LINK_NAME.exists():
        LINK_NAME.unlink()

    os.symlink(str(static_dir), str(LINK_NAME))
    console.info(f"OK: {LINK_NAME.name} -> {static_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
