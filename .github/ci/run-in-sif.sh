#!/usr/bin/env bash
# FigRecipe's real owning suite runs in the digest-verified reused image.
# The outer wrapper binds fresh RUNNER_TEMP scratch over container /tmp.
set -euo pipefail
V="${1:?python version arg required (3.11/3.12/3.13)}"
VENV="${SIF_VENV:-/opt/venv-$V}"
PY="$VENV/bin/python"
[ -x "$PY" ] || { echo "::error::baked Python missing: $PY"; exit 1; }
export LC_ALL=C.UTF-8 LANG=C.UTF-8
RUN_TAG="${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-$$}"
TMPDIR="${TMPDIR:?verified wrapper or owning test must supply scratch}/ci-figrecipe-$V-$RUN_TAG"
export TMPDIR
trap 'rm -rf "$TMPDIR" 2>/dev/null || true' EXIT
rm -rf "${TMPDIR:?FigRecipe scratch is empty}"
mkdir -p "$TMPDIR/uv-cache" "$TMPDIR/pip-cache" "$TMPDIR/scitex" \
    "$TMPDIR/pycache" "$TMPDIR/mpl" "$TMPDIR/config"
export SCITEX_DIR="$TMPDIR/scitex" PYTHONPYCACHEPREFIX="$TMPDIR/pycache"
export UV_CACHE_DIR="$TMPDIR/uv-cache" PIP_CACHE_DIR="$TMPDIR/pip-cache"
export XDG_CACHE_HOME="$TMPDIR" XDG_CONFIG_HOME="$TMPDIR/config"
export MPLBACKEND=Agg MPLCONFIGDIR="$TMPDIR/mpl" RUN_E2E=1
unset VIRTUAL_ENV || true
# The candidate must stay installed for fixtures that deliberately drop
# PYTHONPATH; an overlay would expose the older baked distribution instead.
"$PY" -m venv "$TMPDIR/venv"
PY="$TMPDIR/venv/bin/python"
export PATH="$TMPDIR/venv/bin:$VENV/bin:$PATH"
uv pip install --python "$PY" -e ".[all,dev]"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
# Warm the real font cache once before independent plotting workers start.
"$PY" -c "import matplotlib; matplotlib.use('Agg'); from matplotlib import font_manager; font_manager.fontManager; import matplotlib.pyplot as plt; f=plt.figure(); f.canvas.draw(); plt.close(f); print('mpl font cache warmed at', matplotlib.get_cachedir())"
WORKERS="${FIGRECIPE_CI_WORKERS:-}"
if [ -z "$WORKERS" ]; then
    WORKERS="$("$PY" - <<'PYWORKERS'
import math, os
from pathlib import Path
limits = [os.cpu_count() or 1]
if hasattr(os, 'sched_getaffinity'):
    limits.append(len(os.sched_getaffinity(0)))
try:
    quota, period = Path('/sys/fs/cgroup/cpu.max').read_text().split()
    if quota != 'max':
        limits.append(max(1, math.floor(int(quota) / int(period))))
except (FileNotFoundError, PermissionError, ValueError, ZeroDivisionError):
    pass
print(max(1, min(limits)))
PYWORKERS
)"
fi
case "$WORKERS" in
    ''|*[!0-9]*|0) echo "::error::invalid FigRecipe worker count"; exit 1 ;;
esac
echo "FigRecipe owning xdist workers=$WORKERS"
# Keep the shell alive: EXIT removes this job's scratch for success or failure.
# Forward cancellation to the real test process before waiting and cleaning up.
nice -n 19 ionice -c 3 "$PY" -m pytest tests/ -n "$WORKERS" --dist load -q \
    --cov=src/figrecipe --cov-report=xml --cov-report=term \
    -p no:cacheprovider &
PYTEST_PID=$!
forward_signal() { kill -TERM "$PYTEST_PID" 2>/dev/null || true; }
trap forward_signal TERM INT
status=0
wait "$PYTEST_PID" || status=$?
exit "$status"
