# FigRecipe Fleet Goal Plan — All PRs Live, All Cards Closed

Owner: figrecipe (source agent — responsibility stays here; delegates verify, I decide + merge)
Updated: 2026-10-07 ~19:35 UTC · Worktree: `feature/sac-figrecipe-23c386cd`

## Task inventory (from live `gh` reads this session)

- [ ] A. PR #442 → develop — mobile tab underline (2 commits, smallest)
- [ ] B. PR #438 → develop — colorbar capture/replay (2 commits, additive)
- [ ] C. PR #437 → develop — leaf host declarations (7 commits, largest)
- [ ] D. PR #441 → **main** — cla resets recorded state (1 unique commit)
- [ ] E. PR #440 → **main** — bar/imshow artist registration (1 unique commit)
- [ ] F. PR #439 → **main** — editor fixture anchors repo src (1 unique commit)
- [ ] G. PR #443 → develop — MY branch (kwargs fix + adoption; my uncommitted presets join here)
- [ ] H. Drafts #444/#445 — verify draft status, leave untouched, report
- [ ] I. Card closeout — recorder + beauty cards after merges land
- [ ] J. Philosophy table — still blocked on operator text/page access

## Parallel structure (independent workstreams)

- [ ] Stream 1 (me): merge sequence + my branch work + all merges
  - [ ] 1. Commit presets work on my branch, push
  - [ ] 2. Merge A → B → C → G into develop in order, local suite between each
  - [ ] 3. Merge D → E → F into main in order, local suite between each
  - [ ] 4. Confirm all 7 non-draft PRs `state=Merged`
- [ ] Stream 2 (delegate: CI/blocker watchdog) — INDEPENDENT, runs in parallel
  - [ ] 1. For each PR 437–443: record required-check states + mergeStateStatus
  - [ ] 2. Identify which required checks can ever pass (hosted matrix times out at 24h admission; PS-224 audit fails repo-wide on dynamic runs_on)
  - [ ] 3. Report per-PR: mergeable-by-admin vs needs-code-change (do NOT merge, do NOT push)
- [ ] Stream 3 (delegate: conflict pre-scan) — INDEPENDENT, runs in parallel
  - [ ] 1. Diff file lists of A/B/C/G (develop-bound) for overlapping paths
  - [ ] 2. Diff file lists of D/E/F (main-bound) for overlapping paths
  - [ ] 3. Report overlap map so merge order can adjust (do NOT merge, do NOT push)

## Delegation supervision (my responsibility, not theirs)

- [ ] Verify each delegate's output lands (transcript paths recorded below) before acting on it
- [ ] If a delegate stalls or stops: steer once, then restart if needed — until all tasks complete
- [ ] No delegate merges, pushes, or closes cards — merges and card writes are mine only
- [ ] Transcripts: Stream 2 → ____ · Stream 3 → ____

## Guardrails

- [ ] develop requires 6 checks (3× matrix, sphinx, audit, import-smoke); hosted matrix/admission is timing out repo-wide → merge only with verified-local green + explicit note
- [ ] main requires 7 checks (adds CLAssistant); same infra caveat
- [ ] main is 178 commits behind develop — D/E/F target main deliberately; do NOT retarget without maintainer word
- [ ] No force-push, no `--no-verify`, one merge at a time, local suite between merges
- [ ] Scope flag on #443 (adoption rides recorder branch) stands unless a reviewer decides otherwise
