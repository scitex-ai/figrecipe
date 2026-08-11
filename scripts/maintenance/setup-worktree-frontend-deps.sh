#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2026-08-11 06:58:00 (ywatanabe)"
# File: ./scripts/maintenance/setup-worktree-frontend-deps.sh

# Make the frontend build work from a LINKED WORKTREE.
#
# THE PROBLEM. frontend/package.json declares
#     "@scitex/ui": "file:../../../../../scitex-ui"
# a RELATIVE path five levels up from src/figrecipe/_django/frontend. That
# resolves correctly from the MAIN checkout:
#     <proj>/figrecipe/src/figrecipe/_django/frontend  ->  <proj>/scitex-ui
# but a linked worktree sits two levels deeper, so the same path lands on
#     <proj>/figrecipe/.worktrees/scitex-ui              (does not exist)
#
# And it fails SILENTLY: `npm ci` creates a DANGLING SYMLINK and exits 0. The
# breakage only surfaces at build time, so install looks fine.
#
# WHY NOT EDIT package.json. That relative path encodes a resolution contract
# shared with scitex-hub: "@scitex/ui" must resolve to the scitex-ui REPO ROOT,
# in figrecipe's vite.config.ts (which strips the /src/scitex_ui/static/scitex_ui
# suffix) AND in hub's (resolve(SCITEX_UI_STATIC, "../../../..")). CI enforces it
# in .github/workflows/frontend-build-on-ubuntu-latest.yml by checking scitex-ui
# out as a SIBLING of figrecipe. Changing the specifier would break the contract
# that gate exists to protect.
#
# WHAT THIS DOES. Gives every worktree the sibling it expects, mirroring CI:
#     <proj>/figrecipe/.worktrees/scitex-ui -> ../../scitex-ui
# .worktrees/ is gitignored, so the link is local state, not a committed file.
# Idempotent: safe to re-run, and re-run after every `git worktree add`.

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"

GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GRAY}INFO: $1${NC}"; }
echo_success() { echo -e "${GREEN}SUCC: $1${NC}"; }
echo_warning() { echo -e "${YELLOW}WARN: $1${NC}"; }
echo_error() { echo -e "${RED}ERRO: $1${NC}"; }

# Resolve the MAIN checkout, not the current worktree.
#
# `git rev-parse --show-toplevel` returns the WORKTREE root when run inside one,
# which would place the link in the wrong tree. --git-common-dir always points at
# the main checkout's .git, so its parent is the main working tree.
GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null)"
if [ -z "$GIT_COMMON_DIR" ]; then
    echo_error "not inside a git repository"
    exit 1
fi
MAIN_ROOT="$(cd "$(dirname "$(cd "$GIT_COMMON_DIR" && pwd)")" && pwd)"

PEER_NAME="scitex-ui"
PEER_REAL="$(cd "$MAIN_ROOT/.." && pwd)/$PEER_NAME"
LINK_DIR="$MAIN_ROOT/.worktrees"
LINK_PATH="$LINK_DIR/$PEER_NAME"

echo_info "main checkout : $MAIN_ROOT"
echo_info "peer checkout : $PEER_REAL"

if [ ! -d "$PEER_REAL" ]; then
    echo_error "peer checkout not found: $PEER_REAL"
    echo_error "clone it as a SIBLING of this repo, e.g."
    echo_error "  git -C $(cd "$MAIN_ROOT/.." && pwd) clone git@github.com:scitex-ai/$PEER_NAME.git"
    exit 1
fi

mkdir -p "$LINK_DIR"
ln -sfn "../../$PEER_NAME" "$LINK_PATH"

# Verify the LINK RESOLVES, not merely that ln succeeded. A dangling symlink is
# exactly the failure this script exists to prevent, so asserting the target is a
# real directory is the whole point.
if [ ! -d "$LINK_PATH" ]; then
    echo_error "link created but does not resolve: $LINK_PATH -> $(readlink "$LINK_PATH")"
    exit 1
fi

echo_success "$LINK_PATH -> $(readlink "$LINK_PATH") ($(cd "$LINK_PATH" && pwd))"
echo_info "worktree frontend builds can now resolve @scitex/ui"
echo_info "reproduce CI's build with:"
echo_info "  cd <worktree>/src/figrecipe/_django/frontend"
echo_info "  SCITEX_UI_STATIC=$PEER_REAL/src/scitex_ui/static/scitex_ui npx vite build"
echo_warning "use 'npx vite build', NOT 'npm run build' -- the latter is 'tsc && vite build'"
echo_warning "and tsc type-checks the peer's sources, which CI deliberately skips"

cd "$ORIG_DIR"
