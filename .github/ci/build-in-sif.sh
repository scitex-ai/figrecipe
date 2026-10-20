#!/usr/bin/env bash
# Build and qualify the actual candidate inside the digest-verified image.
# The outer wrapper binds fresh runner scratch over container /tmp. All build,
# dependency and installed-artifact gates are mandatory before publication.
set -euo pipefail
V="${1:-3.12}"
VENV="/opt/venv-$V"
PY="$VENV/bin/python"
[ -x "$PY" ] || { echo "::error::baked Python missing: $PY"; exit 1; }
export LC_ALL=C.UTF-8 LANG=C.UTF-8
TMPDIR="${TMPDIR:?verified wrapper must supply owned scratch}/build-figrecipe-$V-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-$$}"
export TMPDIR
trap 'rm -rf "$TMPDIR" 2>/dev/null || true' EXIT
rm -rf "${TMPDIR:?FigRecipe build scratch is empty}"
mkdir -p "$TMPDIR/uv-cache" "$TMPDIR/pip-cache" "$TMPDIR/scitex" "$TMPDIR/pycache" "$TMPDIR/mpl" "$TMPDIR/config"
export UV_CACHE_DIR="$TMPDIR/uv-cache" PIP_CACHE_DIR="$TMPDIR/pip-cache"
export SCITEX_DIR="$TMPDIR/scitex" PYTHONPYCACHEPREFIX="$TMPDIR/pycache"
export XDG_CACHE_HOME="$TMPDIR" XDG_CONFIG_HOME="$TMPDIR/config"
export MPLBACKEND=Agg MPLCONFIGDIR="$TMPDIR/mpl"
unset VIRTUAL_ENV PYTHONPATH || true
"$PY" -m venv "$TMPDIR/venv"
PY="$TMPDIR/venv/bin/python"
export PATH="$TMPDIR/venv/bin:$VENV/bin:$PATH"
uv pip install --python "$PY" build "scitex-dev>=0.62.1"
rm -rf dist
"$PY" -m build --outdir dist
WHEEL="$(find dist -maxdepth 1 -name '*.whl' -print -quit)"
SDIST="$(find dist -maxdepth 1 -name '*.tar.gz' -print -quit)"
[ -n "$WHEEL" ] && [ -n "$SDIST" ] || { echo "::error::wheel and sdist are both required"; exit 1; }
# Resolve the complete owning dependency graph against the built wheel.
uv pip install --python "$PY" "$WHEEL[all]"
"$PY" -m pip check
"$PY" - "$WHEEL" "${2:-}" <<'PYGATE'
from email.parser import BytesParser
from importlib.metadata import version
from packaging.version import Version
from pathlib import Path
import sys
import tomllib
import zipfile
from scitex_dev._release.entrypoint_imports import audit_wheel_entry_point_imports
assert Version(version("scitex-dev")) >= Version("0.62.1")
expected = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
with zipfile.ZipFile(sys.argv[1]) as archive:
    name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
    metadata = BytesParser().parsebytes(archive.read(name))
assert metadata["Name"] == "figrecipe" and metadata["Version"] == expected
if sys.argv[2]:
    assert sys.argv[2] == "v" + expected, "release tag/source version mismatch"
report = audit_wheel_entry_point_imports(Path(sys.argv[1]), "figrecipe")
print(report.report())
if not report.is_clean:
    raise SystemExit(1)
PYGATE
