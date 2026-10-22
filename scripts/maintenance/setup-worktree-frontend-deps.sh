#!/usr/bin/env bash
# Configure the invoking checkout/worktree against its installed SDK owner.
# No sibling links or changes to a different checkout are needed.
set -euo pipefail
TASK_REPO_ROOT="$(git rev-parse --show-toplevel)"
TASK_FRONTEND_DIR="$TASK_REPO_ROOT/src/figrecipe/_django/frontend"
python "$TASK_FRONTEND_DIR/configure.py"
# NOTE (reproducibility, evidenced 2026-10-22): with a pre-existing
# node_modules + lock, bare `npm install` keeps packing the LOCK's file: URL
# and never re-resolves a rewritten `file:` spec — the SDK pack goes stale
# silently (owner/version drift caught only by the scitexSdkContract gate).
# After configure.py rewrites the owner, force re-resolution explicitly:
#   npm install --save "file://<absolute SDK package dir>" && npm run build
printf '%s\n' "Next: cd $TASK_FRONTEND_DIR && npm install && npm run build"
