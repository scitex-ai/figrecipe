# Wave 2 CI-dedup: branch-protection update plan (hub / dev / cards)

READ-ONLY survey, 2026-10-10. No protection changed, no files deleted, no PRs opened.
Canonical reference: figrecipe-#453 pattern — required contexts are the shared-workflow
contexts (verified passing on a PR before the protection flip):

- `pytest-matrix / pytest-matrix-on-ubuntu-py3.11`
- `pytest-matrix / pytest-matrix-on-ubuntu-py3.12`
- `pytest-matrix / pytest-matrix-on-ubuntu-py3.13`
- `import-smoke / import-smoke-on-ubuntu-py3-12`
- `quality-audit / audit`
- `rtd-sphinx-build / docs-sphinx` (context name depends on the CALLER job id;
  cards uses `rtd-sphinx-build-central`, so its context is
  `rtd-sphinx-build-central / docs-sphinx`)
- figrecipe main additionally requires `call / CLAssistant` (CLA, out of dedup scope)

Enforcement note (all three repos): 0 required reviews, `enforce_admins: false` —
protection is advisory; owners merged red/missing checks (hub #1067, dev #861).

## 1. scitex-ai/scitex-hub — nothing shared except import-smoke

Current protection:
- main: `pytest-matrix-on-ubuntu-py3.11/3.12/3.13` (bare, local `test` job)
- develop: same 3 bare + `cli-import-smoke-on-ubuntu-latest` (local) + `audit` (local)

Verified on recent PRs (#1066, #1067, develop-target, merged 2026-10-10):
- PASS: `import-smoke / import-smoke-on-ubuntu-py3-12` (caller already in place)
- Bare `pytest-matrix-*` and bare `audit`: FAILING on #1067 yet merged (owner bypass)

Plan:
- main: `pytest-matrix-on-ubuntu-py3.11` → `pytest-matrix / pytest-matrix-on-ubuntu-py3.11`
  (same for 3.12, 3.13). BLOCKED: no shared pytest caller exists in hub yet —
  land caller (figrecipe `ci.yml` shape, job id `pytest-matrix`), verify green on a PR, then flip.
- develop: same 3 pytest moves + `audit` → `quality-audit / audit` (BLOCKED likewise).
  KEEP `cli-import-smoke-on-ubuntu-latest` (hub-specific console-script gate, no shared
  equivalent; optionally fold into shared import-smoke via its `console_script` input
  per figrecipe precedent — execution-time decision).
  RECOMMENDED ADD: `import-smoke / import-smoke-on-ubuntu-py3-12` (already passing).

## 2. scitex-ai/scitex-dev — no shared callers at all, nothing verified

Current protection:
- main: `pytest-matrix-on-ubuntu-py3.11/3.12/3.13` (bare, via `test` propagator job
  needing `[immutable-matrix, matrix-evidence]`)
- develop: same 3 bare + `audit` (bare, local `audit` job alongside `workspace-audit`)

Verified on recent PRs (#860 open, #861 merged 2026-10-06, #862 open):
- NO shared-style context has ever reported on dev. Only local checks appear
  (`audit`, `workspace-audit`, `full-original-import / import-smoke-on-ubuntu-py3-12`,
  bare `install-check`); pytest legs are ABSENT entirely (workflow not reporting).
- #862 currently RED (audit, workspace-audit, both import-smoke jobs failing).

Plan (all BLOCKED on landing callers + a green PR, figrecipe-#452 style):
- main: 3× bare pytest → `pytest-matrix / pytest-matrix-on-ubuntu-py3.11/3.12/3.13`.
- develop: same 3 moves + `audit` → `quality-audit / audit`.
  Dev extras (`workspace-audit`, `full-original-import`, `immutable-matrix` /
  `matrix-evidence` propagator) are NOT in protection — out of scope for the flip.
- RECOMMENDED ADD once passing: `import-smoke / import-smoke-on-ubuntu-py3-12`
  (replaces bare `install-check` context, currently not required).

## 3. scitex-ai/scitex-cards (pilot) — almost done, one move left

Cards files are already thin callers (pinned `8c64608…`; rtd caller job id is
`rtd-sphinx-build-central`, NOT figrecipe's `rtd-sphinx-build`).
Current protection:
- develop: `pytest-matrix / pytest-matrix-on-ubuntu-py3.11/3.12/3.13`
  + `import-smoke / import-smoke-on-ubuntu-py3-12` + bare `audit`
  + `rtd-sphinx-build-central / docs-sphinx`
- main: `pytest-matrix / pytest-matrix-on-ubuntu-py3.11/3.12/3.13` (names already
  shared-style; `app_id: null` vs develop's `15368` — re-save normalizes this)

Verified on recent PRs (#1077 develop-target, #1078 develop→main, merged 2026-10-10):
- ALL PASS: 3× shared pytest legs, `import-smoke / …`, `rtd-sphinx-build-central /
  docs-sphinx`, bare `audit`, `pytest-matrix / pytest aggregate gate`.

Plan:
- develop: single move `audit` → `quality-audit / audit`. BLOCKED: quality file still
  runs local `audit` job — convert to caller job `quality-audit`, verify green, then flip.
- main: no rename needed. OPTIONAL parity adds (flagged, not required — repo comment
  states audit is deliberately non-required on main): `import-smoke / …`,
  `quality-audit / audit`, `rtd-sphinx-build-central / docs-sphinx`.

## Flip order

1. cards develop (`audit` → shared) — one caller conversion away.
2. hub (pytest + audit callers) — import-smoke already proven there.
3. dev (all callers missing + develop RED) — needs most work; fix red gates first
   so the new shared contexts can go green on the verification PR.
