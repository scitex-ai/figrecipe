# FigRecipe Goal Tracker — PRs live, cards closed out

Branch: `feature/sac-figrecipe-23c386cd` · Updated 2026-10-07 ~19:30 UTC

## Key finding (verified, not assumed)

- [x] Diagnose why all PRs show `mergeState=BLOCKED` despite `mergeable=MERGEABLE`
  - [x] CI is red repo-wide from **infra causes on PR branches**: PS-224 runner-destination audit on dynamic `runs_on` stanzas + 24h self-hosted admission timeouts (runs `CANCELLED` after 24h queued). Same failure shape on PRs 437–443.
  - [x] Local suite is green where it counts: presets+kwargs 12 passed, audit gate passed, ruff clean (verified this session)
  - [ ] Merging must therefore be **sequenced and verified locally**, not gated on hosted CI alone

## Merge sequence (all target `develop` unless noted; PR 443 = my branch)

- [ ] 1. PR #442 — mobile tab underline (4-line, lowest risk) → merge → verify develop head still green locally
- [ ] 2. PR #438 — colorbar presentation capture/replay (+133, additive) → merge → verify
- [ ] 3. PR #437 — leaf host declarations refactor (+1031/−236, largest blast radius) → merge → run full local suite before next
- [ ] 4. PR #441 — cla resets recorded state (artist-lifecycle family) → merge → verify recorder suite
- [ ] 5. PR #440 — bar/imshow artist registration (sibling of #441, same family) → merge → verify
- [ ] 6. PR #443 — MY branch: recorder kwargs fix + adoption 4/4 + presets
  - [ ] Commit the uncommitted presets work first (exports in `__init__.py` + `_presets.py` + tests, all verified)
  - [ ] Push, watch CI admission, merge
- [ ] 7. PRs #439/#441-base-`main` — confirm correct base (they target `main`, not `develop`); merge or retarget per maintainer rule
- [ ] 8. Drafts #444/#445 — leave alone (not mine, still drafts)

## Card closeout (parallel with merges)

- [ ] `figrecipe-recorder-str-fallback…` → close after #443 merged + behavior observed
- [ ] `figrecipe-bioinformatics-figure-beauty…` → close after adoption merged; philosophy table still needs operator text/page access (blocked, noted on card)
- [ ] Deferred backlog (frontend peer-checkout, recipe-artists, JA lang, unrecorded-methods, handle-mutation, taxonomy) → leave deferred per dispositions; re-triage only if a merge changes their measured state

## Do-not-merge guardrails

- [ ] Never merge a PR whose **local** verification I haven't run (hosted CI is timing out, not testing)
- [ ] One merge at a time; re-verify the local suite between merges
- [ ] No force-push, no `--no-verify`, no merging my own restructure unasked (scope flag on #443 stands until a reviewer decides)
