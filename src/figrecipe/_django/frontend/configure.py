#!/usr/bin/env python3
"""Prepare normal npm installation against the installed SDK frontend package.

Run ``python configure.py`` before ``npm install`` for a pip-installed SDK.
The committed default dependency also supports the pinned sibling SDK checkout.
No Python static path discovery or Vite alias is needed at build time.
"""

import json
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent


def configure(frontend_dir: Path, package_dir: Path) -> None:
    """Validate the owning package before updating the local file dependency."""
    owner = json.loads((package_dir / "package.json").read_text())
    manifest = frontend_dir / "package.json"
    package = json.loads(manifest.read_text())
    required = package["scitexSdk"]["version"]
    if owner.get("name") != "@scitex/sdk" or owner.get("version") != required:
        raise ValueError(
            "Installed SDK frontend package does not match the declared owner"
        )
    if "./ui/react/app/bridge" not in owner.get("exports", {}):
        raise ValueError("Installed SDK lacks the public React bridge export")
    package["dependencies"]["@scitex/sdk"] = "file:" + str(package_dir.resolve())
    manifest.write_text(json.dumps(package, indent=2) + "\n")


def main() -> int:
    try:
        import scitex_logging as slogging
    except ImportError as exc:
        raise ImportError(
            "Frontend setup diagnostics require scitex-logging. "
            "Install it with: pip install 'figrecipe[scitex]'"
        ) from exc
    try:
        from scitex_sdk import get_frontend_package_dir

        configure(FRONTEND_DIR, get_frontend_package_dir())
    except (ImportError, OSError, ValueError, KeyError):
        slogging.getLogger(__name__).error(
            "Frontend setup failed: install the declared scitex-sdk GUI owner, then retry."
        )
        return 1
    slogging.getPlainConsole(__name__).emit(
        "Frontend SDK dependency configured. Run npm install, then npm run build."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
