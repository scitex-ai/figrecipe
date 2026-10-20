#!/usr/bin/env bash
# Configure the invoking checkout/worktree against its installed SDK owner.
# No sibling links or changes to a different checkout are needed.
set -euo pipefail
TASK_REPO_ROOT="$(git rev-parse --show-toplevel)"
TASK_FRONTEND_DIR="$TASK_REPO_ROOT/src/figrecipe/_django/frontend"
python "$TASK_FRONTEND_DIR/configure.py"
printf '%s\n' "Next: cd $TASK_FRONTEND_DIR && npm install && npm run build"
