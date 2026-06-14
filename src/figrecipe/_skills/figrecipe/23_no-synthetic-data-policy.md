---
description: |
  [TOPIC] No-Synthetic-Data Policy (figrecipe rendering-side guard)
  [DETAILS] figrecipe-side restatement of the ecosystem-wide no-synthetic-data-in-publication-figures policy. The canonical home is `scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md`; this leaf is the figrecipe-specific rendering rule: refuse to render with placeholder data, fail loud on missing inputs, and keep synthetic examples in clearly-marked test fixtures.
tags: [figrecipe-no-synthetic-data-policy, figrecipe]
---


# No-Synthetic-Data Policy (figrecipe view)

> **Canonical home**:
> `scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md`.
> That leaf is the ecosystem-policy SSoT. This leaf is the
> figrecipe-specific rendering rule, kept here so that a figrecipe
> consumer who never loads the scientific umbrella still encounters
> the policy.

## The rule (figrecipe view)

A figrecipe figure that will appear in a paper / poster / talk /
representative-of-a-result asset MUST be backed by real data. If the
data file is missing at render time, the figure script must **fail
loud** — raise an exception, exit non-zero, refuse to write the
output — rather than silently substitute `np.random.*`, column
means, or any placeholder.

Synthetic data is acceptable in:

- `tests/fixtures/synthetic_*` test inputs
- `examples/synthetic_demo_*.py` API-exercise demos
- Any path whose name contains `synthetic` / `fixture` / `demo`

It is NOT acceptable in:

- `examples/representative_*.py` (rename to `synthetic_*` if
  it isn't real)
- Anything imported by a paper / report pipeline
- A docstring example labelled "this is what figure X looks like"

## DO

- **Fail loud on missing data**. Let `FileNotFoundError` propagate;
  let `assert df.shape[0] > 0` raise; exit non-zero from CLI.

  ```python
  data_path = Path(CONFIG.PATH.RAW_SIGNAL)
  if not data_path.exists():
      raise FileNotFoundError(
          f"Real data missing at {data_path}; refusing to render "
          f"a publication figure without source data."
      )
  ```

- **Name fixtures clearly**: `tests/fixtures/synthetic_signal.npz`,
  `examples/04_synthetic_demo_scatter.py`. The substring
  `synthetic` / `fixture` / `demo` must appear in the filename.

- **Mark provisional panels visibly**. If you are drafting a figure
  with a placeholder panel pending real data:

  ```python
  ax.text(0.5, 0.5, "PLACEHOLDER\nreal data pending",
          ha="center", va="center", fontsize=24,
          transform=ax.transAxes, color="red",
          bbox=dict(boxstyle="round", facecolor="yellow"))
  ```

  This is not a "polite" placeholder — it must be visually
  unmistakable so it cannot ship by accident.

## DON'T

- **Don't `np.random.*` into a representative figure** to "show the
  shape". That figure travels into slides and Slack and stops being
  flagged as fake.
- **Don't write a `make_example_figure()` helper that swallows
  `FileNotFoundError`** and renders synthetic data as a fallback.
- **Don't fill missing real data with column means / zeros** for a
  publication panel. Decide on a NaN-handling rule (see
  `22_nan-sentinel-on-read.md` and `21_figure-prep-playbook.md`
  rule 2) and apply it consistently.
- **Don't ship `examples/representative_figure.py` that secretly
  uses `np.random.randn`**. Either back it with real data or
  rename it to `synthetic_demo_figure.py`.

## Cross-references

- `scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md`
  — canonical ecosystem-policy authority.
- `21_figure-prep-playbook.md` — the six-rule figure-prep playbook
  (this leaf is rule 1).
- `22_nan-sentinel-on-read.md` — handling real-but-missing data
  values without resorting to synthetic placeholders.
- `scitex-dev/_skills/scientific/01_figures_02_provenance-and-verification.md`
  — Source→Figure DAG (a verified DAG over synthetic data certifies
  a fake; the policy and provenance rules compose).
