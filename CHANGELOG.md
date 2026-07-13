# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.31.0] - 2026-07-13

### Added
- **`comma_format(ax, x=, y=)` / `CommaFormatter`** — thousands-separator tick
  formatter, mirroring the existing `OOMFormatter`/`sci_note` pattern. Exposed
  as `fr.styles.comma_format` and as an `ax.comma_format(...)` method.
- **`ax.stx_annotate_n(x, y, n, ...)`** — sample-size annotation helper. Font
  size comes from the active style, colour defaults to black, and placement
  reuses figrecipe's existing declutter ring-solver + ink-mask renderer for
  overlap avoidance (with a *warned*, never silent, fallback to a fixed offset
  when no clear spot is found).
- **Six-stat annotation doctrine** documented as a new skill leaf
  (`27_six-stat-annotation-doctrine.md`): every statistical annotation carries
  all six of n / CI / method / p / effect / statistic, statistical symbols
  render in italic, and N (subjects) stays distinct from n (windows/trials).
  Every 2D heatmap ships a colorbar with tick labels, a label, and units.
- **Two new soft lint rules** for the above: `STX-FM017` (stats annotation
  missing several of the six required fields) and `STX-FM018` (`imshow` with no
  colorbar in scope). Both are conservative (literal strings only) and honour
  the existing `# stx-allow: STX-<ID>` escape hatch.

### Fixed
- **`/api/files` no longer 500s when a listed file escapes the project root.**
  A symlinked `node_modules/@scitex/ui` made scitex-app's `FileSystemBackend`
  (correctly) raise `ValueError: Path traversal detected`, but the file-tree
  recipe-detection helpers only caught `(OSError, UnicodeDecodeError,
  FileNotFoundError)` — so that one unreadable entry propagated out and took
  down the entire recursive tree. A file the backend refuses to read is now
  simply "not a recipe" and is skipped.
- **`imshow` tick labels survive record → save → load → replay.** Two
  compounding bugs dropped `set_xticks`/`set_xticklabels` on a label-less
  imshow axis: the recorder serialized the caller's raw `range(...)` arg (which
  degraded to the literal string `"range(0, 19)"`), and `finalize_special_plots`
  wiped ticks on any label-less imshow axis with no guard. The recorder now
  reads tick positions back from the live axis, and the finalizer checks for a
  `FixedLocator` before clearing.
- Chat views are imported from scitex-app's **public** `scitex_app.chat` surface
  instead of the private `_chat` module (scitex-app floor raised to `>=0.3.0`).
- CI: the in-SIF scratch `TMPDIR` is now unique per workflow run, so a stale
  directory left by a killed worker can no longer fail the next run's cleanup.

## [0.30.0] - 2026-07-12

### Added
- **`auto_tile_layout(aspects, width_mm, height_mm=None, gap_mm=1.0)`** — bin-packs
  panels (keyed only by their true aspect ratio) into a tight row-list `layout`
  ready for `build_tiled_sources`/`fr.compose`. LPT-greedy shelf partition over
  candidate row-counts, scored against a target `height_mm` when given or to
  minimize wasted canvas area otherwise. Panels are never stretched/upscaled —
  `sizes_mm` always preserves each panel's exact input aspect ratio, by
  construction (shares the row-height formula with `build_tiled_sources`, not a
  separate implementation). Exported as `fr.auto_tile_layout`.
- **`gui` command group**: `open`/`serve`/`status`/`stop`, replacing the flat
  `start-gui` command (kept as a hidden deprecated alias for one cycle).
  `serve` runs the editor server in the foreground; `open` auto-serves a
  detached background instance when none is running, then opens the browser;
  `status`/`stop` work from a fresh shell via a tracked PID/port state file.
  `gui` is a DefaultGroup — a bare `figrecipe gui [SOURCE]` still resolves to
  `gui open`, matching the old flat command's ergonomic, alongside the
  explicit subcommands (required for `scitex-plt`, a console-script alias of
  this same CLI, which invokes `gui serve` directly).
- Consumer console-script branding: `scitex-plt`'s GUI now renders its own
  page title ("SciTeX Plot") and a navy favicon, auto-detected from the
  invoked program name (no fork needed for future aliased consumers).

### Fixed
- **`gui` default port changed 5050 → 31296** (figrecipe's reserved slot in
  the corrected scitex-dev per-package GUI port scheme; 5050 collided live
  with scitex-writer, both defaulting there). `gui serve` now binds the
  requested port or fails loud with an actionable message — it never
  silently drifts to the next free port — and refuses to start a second
  instance when one is already tracked running.

## [0.29.26] - 2026-07-11

### Fixed
- **Audit conformance for the 0.29.25 coverage-shim regression test.** The
  new `tests/integration/test_subprocess_coverage_shim_guard.py` used the
  `monkeypatch` fixture (forbidden as a mock by PA-306) and had a test
  with no explicit assertion / AAA markers, tripping PA-306/STX-TQ001/
  STX-TQ002 (3.11+ CI) and blocking the 0.29.25 release from publishing.
  Rewritten to avoid mocking entirely: the "coverage not installed"
  condition is now a REAL environment (a subprocess launched with `-S`,
  which skips `site` initialization so no site-packages end up on
  `sys.path`), not a monkeypatched import. (0.29.25's coverage-pth fix
  is included here — 0.29.25 never published.)

## [0.29.25] - 2026-07-11

### Fixed
- **Subprocess-coverage `.pth` shim crashed every CLI invocation in venvs without
  `coverage` installed.** `tests/conftest.py::_ensure_subprocess_coverage_shim()`
  writes a `.pth` file that starts coverage tracing in child interpreters. Its
  template had `import os, coverage` at the top level, executed unconditionally
  by `site.py` on *every* interpreter start in that venv — not just test runs.
  Any plain command (e.g. `figrecipe --help`) in a venv where `coverage` wasn't
  installed raised `ModuleNotFoundError` on every invocation, once a prior
  `pytest` run had dropped the shim into site-packages. `coverage` is now
  imported only inside the `COVERAGE_PROCESS_START` conditional. Regression
  test: `tests/integration/test_subprocess_coverage_shim_guard.py`.

## [0.29.24] - 2026-07-11

### Fixed
- **Audit conformance for the 0.29.23 regression-guard test.** The new
  `test_small_embedded_array_stays_inline_and_validates` had no explicit
  `assert` and combined `# Act / Assert` on one line, tripping the
  STX-TQ001/STX-TQ002 audit rules (3.11+ CI) and blocking the 0.29.23
  release from publishing. Split into separate `# Act` / `# Assert`
  markers with an explicit assertion (no `*-not-reproduced*` divergence
  artifact was written). (0.29.23's serializer fix is included here —
  0.29.23 never published.)

## [0.29.23] - 2026-07-11

### Fixed
- **Root-caused the flaky imshow nested/composed round-trip test.** `ax.embed()`
  materializes the source recipe's array data inline (`load_recipe()` sets
  `arg["data"] = arr.tolist()` plus `_source_file`), but the save pipeline
  (`_serializer/_save.py::_process_arrays_for_save` /
  `_process_arrays_with_symlinks`) only ever walked each axes' top-level
  `calls`/`decorations` — never the nested `subpanels` list that
  `ax.embed()`/`ax.inset_axes()` produce. So an embedded source's array data
  (e.g. a 512x512 RGBA `imshow` icon, ~1M scalars) was never re-filed to
  CSV/NPZ; it stayed inline on every save, turning `_convert_numpy_types` +
  `ruamel.yaml.dump` into an O(N) walk over ~1M Python-level scalar nodes —
  a multi-minute, deterministic hang that CI's per-job timeout (or a loaded
  runner) intermittently killed, misread as "flaky." Both serializer
  functions now recurse into `subpanels`; the loader (`_load.py`) resolves
  the same nested file references back into real array data. A missing
  source file now falls back to inline data with a loud warning (was
  previously silent). Re-filing only kicks in above a size floor
  (`_SUBPANEL_FILE_REF_MIN_ELEMENTS = 256`): a smaller sub-panel array stays
  inline, because the reproducer's inset/embed replay path
  (`_reproducer/_replay_insets.py`) resolves a sub-panel's `data` straight
  from the recipe dict rather than through the file-reference loader, so a
  filed reference there isn't (yet) something it understands — filing a
  below-threshold array broke the ordinary small-embed case (a save-time
  reproducibility-validation failure), caught by a regression test before
  shipping. Regression tests: `tests/integration/test_embed_subpanel_data_filing.py`.

## [0.29.21] - 2026-07-09

### Fixed
- **Audit conformance for the 0.29.20 panel-label-weight regression test.** The new
  `tests/integration/test_panel_label_weight_style.py` combined `# Arrange / Act`
  on one line, tripping the STX-TQ002 AAA-marker audit rule (which runs only on the
  3.13 CI SIF) and blocking the 0.29.20 release from publishing. Split into separate
  `# Arrange` / `# Act` / `# Assert` markers. (0.29.20's panel-label-weight change is
  included here — 0.29.20 never published.)

## [0.29.20] - 2026-07-09

### Changed
- **Panel-label font WEIGHT is now a style-owned field** (`fonts.panel_label_weight`
  in SCITEX, default `bold`), matching how panel-label size (`panel_label_pt`) and
  family are already style-owned — "the style owns the field, not a code default".
  `fig.add_panel_labels()` resolves `fontweight` from the active style when the
  caller passes none, with `'bold'` only the ultimate fallback for styles without
  the field. Rendered output is unchanged (labels already rendered bold); the
  weight is simply now driven by the style rather than a hardcoded literal.

## [0.29.19] - 2026-07-09

### Fixed
- **Serializing a figure record no longer destroys its in-memory data** (root
  cause of the flaky imshow nested / compose-of-composed round-trip failure).
  `CallRecord.to_dict()` returned its `args`/`kwargs` **by reference**, and the
  save pipeline (`_process_arrays_for_save`) pops `_array` and rewrites `data`
  on those dicts in place — so the first save mutated the *live* record,
  stripping each arg's `_array`. A second save/compose of the same live record
  then emitted a data reference with no CSV written behind it, and reproduce
  raised `FileNotFoundError: <name>_data/<id>_x.csv` (intermittently on py3.11
  in CI, deterministically for any double-serialize). `to_dict()` now returns a
  shallow-copied snapshot of `args`/`kwargs`, so the save pipeline mutates only
  the snapshot; the `_array` values are shared by reference (not deep-copied, so
  file-based storage is unaffected). Regression tests: `to_dict` non-aliasing
  (recorder) + save-same-figure-twice writes data files both times (serializer).

## [0.29.18] - 2026-07-09

### Added
- **Color-collision detection (save-time, always-on).** A new perceptual
  color check flags two data series a reader must tell apart (both carrying a
  real legend label) drawn in colors so close they are indistinguishable —
  even when the shapes never geometrically overlap. Per data axes, every pair
  of labelled series is compared in CIELAB space (`ΔE*76`); pairs below a
  conservative just-noticeable threshold (default `ΔE 5.0`) surface through the
  existing `run_overlap_check` save-time warning. Scope guards keep it quiet on
  legitimate figures: only labelled series are compared, same-label series (one
  logical series in parts) are exempt, colormapped scatters (intentional
  gradients) are skipped, and colors are only compared within a single axes
  (cross-panel color reuse is fine). Lives in `figrecipe._quality._color_collision`
  (`detect_color_collisions`, `delta_e76`); `Conflict` gains a `kind` field
  (`"overlap"` | `"color"`).

## [0.29.9] - 2026-06-28

### Fixed
- **Auto panel labels no longer overlap the axes title.** `fr.subplots(...,
  panel_labels=True)` adds the (A)/(B)/(C)/(D) labels at construction time —
  before titles exist — so a fixed `y=1.05` offset landed the label on a title
  set later via `set_xyt`. Labels are now lifted clear of the title at save
  time: a title-aware label sits just above the title (scaled by the title
  height), while an axes with no title keeps the default placement (back-compat),
  and an explicit user `offset` is honored verbatim.
- **`imshow` honors an explicitly-passed `aspect` (e.g. `"auto"`).** The imshow
  styler now distinguishes "caller passed no aspect" (defaults to the style's
  `"equal"`) from an explicit aspect, so `ax.imshow(..., aspect="auto")` is never
  silently coerced back to `"equal"` by the styler. (Note: for a square heatmap
  filling square mm axes, also use a dedicated colorbar axes — e.g.
  `make_axes_locatable(...).append_axes(...)` — so the colorbar doesn't shrink
  the host axes off-square.)
- **Recipe save no longer crashes on numpy-scalar labels/values.** A numpy
  scalar reaching the recipe serializer (most commonly `np.str_` from a
  DataFrame column, but also `np.complex*`, `np.datetime64`, etc.) was handed
  straight to the YAML representer and raised
  `RepresenterError: cannot represent np.str_('…')`. The numpy→native coercion
  now has an `np.generic` catch-all (`.item()`) so any numpy scalar normalises to
  its native Python type before serialization. (Previously only `np.ndarray`/
  `np.integer`/`np.floating`/`np.bool_` were handled.)

## [0.29.8] - 2026-06-28

### Fixed
- **Justified captions no longer stretch sparse lines into huge gaps.** With
  `align="justify"` (the default), a line is now only stretched edge-to-edge
  when its words already fill at least 60% of the available width; a sparser
  line (few words on a wide figure) is left-aligned instead of having its
  inter-word spaces blown up to several times normal. Full lines stay flush
  left-and-right (the caption body matches the panel width), only the sparse and
  last lines ragged-right. Adds test coverage for `align="center"`/`"left"` and
  `position="top"`.
- **Auto panel labels (A)/(B) now render at the correct size and font.**
  `fig.add_panel_labels()` (used by `fr.subplots(..., panel_labels=True)`) read
  the plot-title size (`title_pt`, 8pt) instead of the panel-label convention
  (`panel_label_pt`, 10pt), and inherited a generic `sans-serif` family rather
  than the style's explicitly-resolved family — so the labels came out the wrong
  size and in a different face from the axis labels/ticks. They now use
  `panel_label_pt` (10pt bold in SCITEX) and the same resolved family as the
  body (Arial, or its installed fallback), so labels match the rest of the
  figure.

## [0.29.7] - 2026-06-28

### Fixed
- **In-image captions never overlap the axes anymore.** `add_figure_caption`
  is now ADDITIVE: instead of reserving space by shrinking the axes (the old
  fixed `subplots_adjust(bottom=0.15)` + per-axes `set_position`, which let a
  multi-line caption grow into the x/ylabels on mm-precise figures), it GROWS
  the figure by a measured caption band and keeps the axes at their EXACT mm
  size and position. The band height is derived from the wrapped line count and
  font size; the axes are pinned across the figrecipe constrained-layout engine
  so they never move. Applies to single figures **and** composed figures
  (`fr.compose(caption=...)`), whose per-panel `(A)/(B)` labels are re-placed
  against the post-band panel positions.

### Added
- **Justified in-image captions.** `add_figure_caption(..., align=...)` accepts
  `"justify"` (default — full-width lines, last line left-aligned), `"center"`,
  and `"left"`, plus a `pad_mm` knob for the band gap. In-image captions are for
  casual researcher communication / reports / grant figures; the manuscript path
  is unchanged (the `.tex` caption sidecar / manuscript mode). The band and
  justified word fragments round-trip faithfully through `save`→`reproduce`.

## [0.29.6] - 2026-06-28

### Added
- **Machine-readable layout introspection** (`figrecipe.empty_cells`,
  `figrecipe.layout_report`) — the agent-facing foundation for tight,
  empty-cell-free page packing. `empty_cells(layout, sources)` returns the blank
  `(row, col)` positions of a grid (fast path); `layout_report(fig)` returns a
  native-float report `{mode, canvas_mm, panels[...mm/frac/aspect],
  empty_regions[maximal blank rectangles], coverage_frac}` with a top-left
  origin. Panels are reported at their measured millimetre sizes so a caller can
  re-plot at 1:1 — figrecipe never stretches a panel to fill space.
- **Compose-time under-fill warning** — composing an under-filled grid now emits
  a `UserWarning` naming the empty cells, so blank page space is caught at build
  time rather than discovered in the PDF.
- **Figure-making skill** (`_skills/figrecipe/26_tight-layout-and-page-filling.md`)
  capturing the tight-layout / page-filling know-how, indexed in `SKILL.md`.

## [0.29.5] - 2026-06-27

### Fixed
- **Tick record/replay faithfulness safeguards.** A pre-0.29.3 bug could
  serialize `set_xticks` POSITIONS with a different count than the labels (e.g.
  `[8,16,24]` written as `[0,1]`), so reproducing such a recipe raised
  "FixedLocator locations (N) does not match the number of labels (M)" and the
  axis rendered garbled. Current figrecipe already records ticks faithfully;
  these are guards so it can never silently regress:
  - **Reproduce-side heal**: loading a recipe whose tick positions/labels counts
    diverge now truncates/pins to the common length and WARNS loudly instead of
    hard-failing — legacy recipes render rather than crash.
  - **Record-time fail-loud guard** (`FR-FAITHFUL-TICKS`): a `set_xticks`/
    `set_yticks` op whose serialized positions count != labels count raises at
    save, so a mismatched (unreproducible) recipe is never shipped.
  - Regression tests lock faithful `set_xticks([8,16,24], labels=...)` round-trip.

## [0.29.4] - 2026-06-27

### Added
- **Caption validation FR-CAP-001: `\footnote` in a caption now errors loud.**
  figrecipe owns captions canonically, so it rejects caption text containing the
  `\footnote` command (and the `\footnotemark`/`\footnotetext` family) — which
  breaks LaTeX in spanning floats (`figure*`): `\caption@ydblarg` "extra }" + a
  runaway `\@xfootnote`. Checked at input (`add_figure_caption`, `compose`
  `caption=`/`panel_captions=`) and at the save/`.tex`-emit output (naming the
  file + which caption/panel). Raises `figrecipe._captions.FootnoteInCaptionError`
  (a `ValueError`). Inline the footnote text into the caption instead. This is
  figrecipe's own independent rule (scitex-writer enforces its own on the
  manuscript-LaTeX side).

## [0.29.3] - 2026-06-26

### Added
- **Composed figures now carry their source panels' captions forward.**
  `compose()` pulls each source panel's own `record.caption`, prefixes its
  `(A)/(B)/...` label, and assembles them into the composed figure's
  `figure.panel_captions` when the caller passes no explicit `panel_captions`
  (grid mode always; mm/tiled when each source contributes one axes). Closes
  the gap where composed figures silently dropped panel captions — the same
  defect class as the composed-colorbar drop. Caller-supplied `panel_captions`
  still take precedence.
- **Writer-compatible caption-only `.tex` sidecar.** Saving a recipe that
  carries caption text now emits `<stem>.tex` next to the `.png`/`.yaml`,
  derived from the canonical `record.caption` (+ folded per-panel captions).
  It is a bare `\caption{...}\label{fig:<stem>}` fragment with NO
  `\begin{figure}` wrapper, so it `\input`s directly inside a manuscript's own
  float without nesting figure environments. New `format_caption_only_tex()`.
- **Manuscript mode** (`fr.set_manuscript_mode()`, `fr.manuscript_mode()`
  context manager, or `FIGRECIPE_MANUSCRIPT_MODE=1`). When active, captions are
  recorded canonically (`metadata.caption`) and the `.tex` sidecar is still
  emitted, but the caption is NOT drawn onto the canvas — so a manuscript build
  doesn't double-render the caption (baked pixels + LaTeX `\caption`).

## [0.29.2] - 2026-06-25

### Performance
- **`import figrecipe` no longer pays the `.env` walk-up cost up front
  (audit-cli §10).** The eager `scitex_config` import + `load_dotenv(walk_up=True)`
  is deferred to first public-API use: importing `scitex_config` pulls in
  `importlib.metadata`, and the parent-dir `.env` walk does many filesystem stat
  calls that, on a network filesystem (Spartan gpfs), dominate import startup and
  tripped the §10 import-speed audit. A bare `import figrecipe` that never touches
  the public API now performs no `.env` walk; any real use loads it once before
  the first API call. **Behavior note:** `.env` is loaded on first figrecipe API
  use rather than at `import figrecipe` time.

### Note
- Also carries the 0.29.1 colorbar round-trip fix below, which never reached PyPI
  (its release run was blocked by this same §10 audit gate).

## [0.29.1] - 2026-06-25

### Fixed
- **Manual `plt.colorbar`/`fig.colorbar` calls now survive the recipe
  round-trip.** Colorbars added via the manual matplotlib API (rather than
  figrecipe's wrappers) were not recorded, so `reproduce` dropped them.
  The recorder now captures these calls and the reproducer replays them,
  keeping the colorbar (and its mappable spec, clim, and axes geometry)
  faithful through record → save → reproduce.

## [0.28.20] - 2026-06-04

### Fixed
- **`tests/integration/test_entry_points.py` PA-307 TQ006 + TQ007.**
  v0.28.19 shipped the entry-point regression-guard test with a
  parametrized body containing a top-level `if`/`else` for the
  `<module>:<attr>` splitting (TQ006) and multiple assertions disguised
  by the same `if` branches (TQ007). v0.28.19 release CI's audit-all
  gate caught it (no broken wheel reached PyPI). Refactor: extract the
  value-splitting into a `_resolve(value)` helper so the test body has
  no `if` and exactly one `assert`. Behaviour unchanged.

## [0.28.19] - 2026-06-04

### Added
- **Module-rename back-compat via `figrecipe._compat` (operator direct via
  Telegram).** The #141 topical refactor moved four private modules into
  `figrecipe._quality.*`. Per the YAGNI grep the ecosystem had zero
  runtime consumers of the old paths, but the operator asked for uniform
  scitex-compat-style deprecation messaging when *any* code touches a
  moved path. New `figrecipe._compat._module_aliases` registers
  transparent `sys.modules` aliases at the old paths so legacy imports
  still resolve AND emit a single-fire `DeprecationWarning` pointing at
  the new path. No flat shim files at the package root (PS-108b
  threshold unaffected).

  Aliases installed (eagerly, from `figrecipe.__init__`):
  - `figrecipe._validator`              → `figrecipe._quality._validator`
  - `figrecipe._linter_plugin`          → `figrecipe._quality._linter_plugin`
  - `figrecipe._axis_alignment_checker` → `figrecipe._quality._axis_alignment_checker`
  - `figrecipe._axis_range_alignment`   → `figrecipe._quality._axis_range_alignment`

- **Entry-point regression guard (lead msg b4e3dc7e).** New parametrized
  smoke test (`tests/figrecipe/test__entry_points.py`) parses every
  `[project.entry-points.*]` group in `pyproject.toml` and asserts each
  `<module>:<attr>` value resolves to a real importable attribute.
  Catches the "moved module + stale entry-point string + aggregator
  silent-skip" failure class generically — new entry points + future
  moves are covered with zero extra test maintenance.

## [0.28.18] - 2026-06-03

### Fixed
- **`Diagram.render(ax)` recipe-recording silently no-op'd because the
  relative import was one dot too shallow (#144 regression).** The hook
  added in #144 to record a `function="diagram"` `CallRecord` on the
  recording axes used `from .._wrappers._axes_diagram import
  _record_diagram_call`. From `src/figrecipe/_diagram/_diagram/_core.py`,
  `..` resolves to `figrecipe._diagram`, NOT `figrecipe`, so the import
  raised `ImportError` (`figrecipe._diagram._wrappers` doesn't exist).
  The defensive `except Exception` then swallowed it silently, so
  `Diagram.render(ax)` "succeeded" but produced **zero** recipe entries
  — exactly the original #139 symptom this PR was supposed to fix.
  v0.28.15/16/17 all shipped this regression; v0.28.15 was caught by the
  release CI on a *different* import bug, v0.28.16 on a fictional test
  kwarg, and **v0.28.17 was caught by the release CI on THIS bug**
  (`assert 0 == 1` in the recording-hook smoke test). No broken wheel
  ever reached PyPI in any of the three attempts.
  Fix: `from ..._wrappers._axes_diagram` (three dots, hitting
  `figrecipe._wrappers`). Promoted the `ImportError` branch to
  `logger.error` so any future "did this hook actually run" silent
  regression is LOUD — the catch-all `Exception` branch stays so the
  recording never breaks the render itself.

## [0.28.17] - 2026-06-03

### Fixed
- **`tests/figrecipe/_diagram/_diagram/test__core_render_records.py` used
  a fictional `figsize_mm` kwarg on `fr.subplots`.** The #144 / #145 test
  scaffolding copied the API shape from the issue #139 reproduction body
  literally, but `fr.subplots` takes per-axes sizing as
  `axes_width_mm` / `axes_height_mm` — there is no `figsize_mm`
  parameter. v0.28.16's release CI test-matrix surfaced this
  (`AttributeError: Figure.set() got an unexpected keyword argument
  'figsize_mm'`), correctly skipped build/publish/release, so **no
  broken wheel reached PyPI**. Fixed the test helper; behaviour
  unchanged everywhere else.

## [0.28.16] - 2026-06-03

### Fixed
- **`_quality/_validator.py` sibling-relative imports broken by the #141
  topical move.** When `_validator.py` moved from `figrecipe/` into
  `figrecipe/_quality/`, two of its internal lazy imports —
  `from ._reproducer import reproduce` and
  `from ._utils._image_diff import compare_images` — kept the single-dot
  form, so at runtime they resolved to non-existent
  `figrecipe._quality._reproducer` / `figrecipe._quality._utils`. v0.28.15
  shipped this regression and `fr.save(..., validate=True)` raised
  `ModuleNotFoundError` on the validate path (caught by the release CI's
  test-matrix — release publish was skipped, no broken wheel hit PyPI).
  Bump both imports to `from .._reproducer` / `from .._utils._image_diff`
  to point at the actual sibling packages of `figrecipe/`, not of
  `figrecipe/_quality/`. Adds an inline comment so the next move catches
  it. The rename-symbols pass at #141 only rewrote OUTSIDE-pointing
  references; this PR closes the inside-pointing gap.

## [0.28.15] - 2026-06-03

### Added
- **`fr.nice_lim(data, lower=0.0, round_to=None)` — tick-friendly axis limit
  helper (closes #140, PR #146).** Snaps an axis limit to a "round" boundary
  above (and optionally below) the data extent so the right (or top) spine
  doesn't get its own tick label. `round_to=None` auto-picks the data's
  order of magnitude. `lower=None` snaps the left edge down to a round
  boundary below `data.min()` (negative-friendly). Edge cases handled:
  empty input, all-NaN, `data.max() == 0`, exact round-boundary `data.max()`
  (lifted one step), `round_to <= 0` raises `ValueError`. Exposed via
  PEP-562 lazy-attr so `import figrecipe as fr; fr.nice_lim(...)` works at
  zero matplotlib-import cost on plain `import figrecipe`.

### Changed
- **`fr.compose()` default `gap_mm=2` (was 5) + panel-label fontsize from
  `SCITEX_STYLE.yaml` (PR #138).** Multi-panel mm-based layouts looked too
  sparse at 5 mm; 2 mm gives the close-pack default users expect. Explicit
  `gap_mm=...` callers unaffected. `_add_panel_labels_{grid,mm}` now read
  `fontsize` from a `_panel_label_fontsize()` helper that consults
  `SCITEX_STYLE.yaml`'s new `panel_label_pt` key (default 10 — Nature-style
  panel label convention).
- **Topical refactor: four quality-gate modules grouped into
  `src/figrecipe/_quality/` (PR #141).** `_axis_alignment_checker`,
  `_axis_range_alignment`, `_linter_plugin`, `_validator` moved under
  `_quality/` per the audit-all `PS-108b` recommendation (flat-file count
  16 → 14, well under threshold). All import paths updated via
  `scitex-dev rename-symbols --regex` (3 passes, 9 files, 11 substitutions,
  0 collisions). Public surface (`figrecipe.fr.*`) unaffected — moved
  modules were private (underscore-prefixed) throughout. Test mirror
  created at `tests/figrecipe/_quality/` (PR #142).

### Fixed
- **`Diagram.render(ax)` now emits a recipe `CallRecord` so
  `fr.save(fig, validate=True)` round-trips cleanly on figures containing
  a `figrecipe.diagram.Diagram` panel (closes #139, PR #144).** Previously,
  the direct-render path bypassed the recipe-recording mechanism that the
  `ax.diagram(...)` wrapper path uses, so the reproducer rendered an empty
  panel where the diagram should be → MSE > 100 → validation raised. Round
  trip is figrecipe's core concept. Single-call high-level recording via
  the existing `_record_diagram_call` helper; the replay side
  (`_reproducer/_replay_diagram.py`) was already in place.
- **Test-quality fix-forwards** for #144 and #146: split combined
  `# Act / Assert` markers and multi-assert tests into AAA-marked
  one-assertion siblings per STX-TQ002 / STX-TQ007 (#145, #147).

## [0.28.14] - 2026-06-02

### Added
- **STX-FIG001 `axis-range-alignment` static lint rule** (#136). AST checker that fires when two or more subplots on the same figure carry explicit literal `set_xlim` / `set_ylim` calls with disagreeing tuples — mismatched ranges destroy the visual comparison the subplots are presumably trying to make (scientific-figure standards rule #4). Severity WARNING; opt-out via `# stx-allow: STX-FIG001`. Covers the literal-mismatch case only.
- **`axis_range_alignment` runtime validator** (#137). Fires at savefig time, walks `fig.axes`, groups peers by inferred shared quantity (matching xlabel/ylabel or same gridspec row/col), warns when `get_xlim`/`get_ylim` disagree above tolerance. Honors matplotlib `sharex`/`sharey`, twin axes, and a `fig._figrecipe_allow_axis_mismatch` opt-out sentinel. Default `validate_error_level="warning"` per issue #134 preference. Covers the dominant autoscale-with-different-data case that the static checker provably cannot detect.

## [0.28.9] - 2026-05-16

### Fixed
- **Defensive import of `scitex_dev._branding`** in `_wrappers/_axes_scitex.py`. The branding-registry refactor (a78434c) hard-imported `scitex_dev._branding`, but that module lives only on scitex-dev's develop branch and is not in the PyPI v0.11.16 wheel — CI installed the PyPI version and crashed at import time with `ModuleNotFoundError`, blocking every job. Wrap the import + alias registration in a `try/except ModuleNotFoundError` so figrecipe installs cleanly against any scitex-dev>=0.11.7 while the registry rolls out across the ecosystem. Mirrors socialia's commit 5640a56.
- **Subprocess test PYTHONPATH** in `tests/figrecipe/test__env_runtime_respect.py::test_import_in_subprocess_with_no_dotenv_succeeds`. Explicitly inject `<repo>/src` so the test does not depend on the editable-install `.pth` file resolving correctly under an overridden `HOME`.

## [0.25.0] - 2026-02-16

### Added
- **Diagram element editor** - Edit box colors, styles, and titles directly in the GUI editor
- **Diagram hitmap** - Pixel-perfect click detection for diagram boxes, containers, and arrows
- **Bullet point support** - BoxSpec now supports bullet styles (circle, dash, arrow)

### Changed
- **Emphasis resolves to explicit colors** - `add_box()`/`add_container()` now store resolved hex colors instead of deferring to render time
- **Complete schematic→diagram rename** - All variable names, function names, and docstrings updated (210 occurrences); example output dirs and sphinx docs renamed
- **Serializer refactored** - `_serializer.py` split into `_serializer/` package
- **Diagram render/IO extraction** - `render_to_file()` moved to `_io.py`, `draw_all_elements()` to `_render.py`

### Fixed
- **Editor color picker** - Shows actual box colors instead of #cccccc fallback
- **Text click in diagram boxes** - Clicking text now activates the Element tab
- **Ruff lint errors** - Fixed F821, E731, F841 across diagram module

## [0.24.1] - 2026-02-14

### Changed
- **Schematic -> Diagram rename** - Complete rename across codebase: examples, docs, wrappers, reproducer
- **Module reorganization** - `_recorder.py` -> `_recorder/` package, `_graph.py` -> `_graph/` package, graphviz/mermaid backends moved into `_diagram/`
- **HPC test infrastructure** - Async sbatch support with `--watch`/`--poll`/`--result` modes

### Fixed
- **OOM in parallel tests** - Added `plt.close('all')` conftest fixture for pytest-xdist workers
- **Gallery CI** - Added missing joblib dependency
- **Pre-commit speed** - Use pytest-testmon for incremental testing on commit

## [0.24.0] - 2026-02-13

### Changed
- **CSS flexbox layout** - `auto_layout()` now supports CSS flexbox-like container nesting with `direction`, `gap_mm`, `padding_mm`
- **Auto-height containers** - Containers auto-calculate height from children when `height_mm` not specified
- **Overlap resolution** - Extracted overlap detection to `_overlap.py` module

## [0.23.0] - 2026-02-08

### Added
- **Diagram validation pipeline** - R1-R8 validation rules with _FAILED figure saving for inspection
- **Style anatomy documentation** - Comprehensive style anatomy figure with pie chart

### Changed
- **Diagram API standardized** - `add_box()` and `add_container()` now use flat `x_mm`, `y_mm`, `width_mm`, `height_mm` params (replaces `position_mm`/`size_mm` tuples)

## [0.22.0] - 2026-02-07

### Added
- **Box-and-arrow diagrams** - New `fr.Diagram` class for publication-quality diagrams with mm-based positioning
- **Diagram auto-layout** - `auto_layout(layout="lr"|"tb")` for automatic box positioning
- **Container support** - Group boxes with `add_container()` for hierarchical diagrams

### Changed
- **README rewritten** - Collapsible sections, three APIs (Python/CLI/MCP), style granularity figure
- **Examples reorganized** - Converted all to `@stx.session`, numbered prefixes

## [0.21.0] - 2026-02-05

### Added
- **Read the Docs** - Sphinx documentation with quickstart, gallery, style reference, CLI reference
- **Bundle format** - Layered ZIP bundles with spec.json, style.json, data.csv, exports/

### Changed
- **API renamed** - `smart_align` → `align_smart`, `edit` → `gui`
- **CLI renamed** - `mcp run` → `mcp start`, `edit` → `gui`, separated `diff` and `hitmap` commands

## [0.20.0] - 2026-02-03

### Added
- **`list-python-apis` CLI command** - Show full API tree with signatures
- **Enhanced MCP tools** - `plt_` prefix for figure tools, better categorization
- **CLI UX improvements** - Categorized help, explicit edit command

## [0.19.0] - 2026-02-02

### Changed
- **API minimized** - Reduced public API surface for cleaner user experience
- **Reproduction fidelity improved** - Better accuracy in figure reproduction

## [0.18.0] - 2026-01-30

### Added
- **Concept diagram example** - FigRecipe concept diagram with pure matplotlib
- **Editor improvements** - Figure element given lowest selection priority

## [0.17.0] - 2026-01-25

### Added
- **Diagram module** - Mermaid and Graphviz output support via `fr.Diagram`

## [0.16.2] - 2026-01-20

### Fixed
- **Compose mm-based positioning** - Free-form `canvas_size_mm` and `xy_mm`/`size_mm` placement (#74, #77)
- **Compose raw images** - Support raw image files as composition sources (#75, #76)

## [0.16.1] - 2026-01-18

### Fixed
- **Editor boxplot colors** - Show box colors in Element panel (#60)
- **Pixel-perfect hit detection** - Correct DPI scaling in coordinate transformation (#59, #61)

## [0.16.0] - 2026-01-16

### Added
- **Specialized plot types** - New plot styling utilities and axis helpers (#69, #70, #72)
- **Scientific captions** - Caption system for publications (#71)
- **Configurable branding** - White-label integration via `FIGRECIPE_BRAND` env var

## [0.15.0] - 2026-01-14

### Added
- **MCP server** - Declarative plot API for AI-assisted figure creation
- **CSV column support** - Read data directly from CSV files in plot specs
- **Shell tab completion** - `figrecipe completion` command
- **`--help-recursive`** - Show all subcommands help at once

### Fixed
- **YAML parsing** - Switch from pyyaml to ruamel.yaml

## [0.14.0] - 2026-01-13

### Added
- **Unified save API** - `fr.save()` and `fig.savefig()` now have identical parameters and defaults
- **facecolor parameter** - New `facecolor` parameter for saving figures with custom background colors (Issue #62)
- **Editor layer_index support** - Multi-layer plots now track layer indices for accurate element selection
- **Color picker for elements** - Editor now supports color picking from plot elements

### Changed
- **BREAKING: `fig.savefig()` defaults** - Now defaults to `validate=True` (was `False`) and `save_recipe=True`
- **Improved hitmap detection** - Better element detection in the interactive editor

## [0.13.0] - 2026-01-12

### Fixed
- **Editor drag overlay coordinate alignment** - Fixed overlay positioning at different zoom levels by using natural image dimensions instead of CSS-scaled dimensions

## [0.12.0] - 2026-01-12

### Added
- **Symlink support for composed figures** - Composed figures now create symlinks to original data files instead of copying, reducing disk usage and preserving data provenance
- **Demo workflow** - New `make demo-plot-all` and `make demo-composition` targets for generating and composing all 47 plot type demos

### Fixed
- **Auto-crop with constrained_layout** - Fixed Issue #41 where `constrained_layout=True` disabled mm_layout and auto-crop functionality
- **fig.savefig() consistency** - `fig.savefig()` now behaves the same as `fr.save()` with auto-crop and mm_layout support (Issue #42)
- **SCITEX error bar styling** - Bar plots with `yerr` now correctly use 0.2mm linewidth for error bars

## [0.11.0] - 2026-01-11

### Added
- **Auto-crop with bbox adjustment** - Save images with automatic cropping while preserving correct axes bounding box coordinates for GUI alignment/snap functionality
- **crop_info and bbox support** - Recipe records now store crop information and axes bounding boxes for post-crop coordinate mapping
- **Graph plotter** - New network visualization demo using networkx (`plot_graph.py`)
- **Demo scripts** - Added `demo_editor.py` and `demo_all_plots.py` for demonstrations
- **crop_margin_mm parameter** - Explicit cropping margin control in `fr.save()`

### Changed
- **mm-based layout** - Margins now represent final output margins (after auto-crop) rather than internal padding
- **run_all_demos()** - Updated to use `fr.save()` for proper mm layout and auto-cropping

### Fixed
- **Barplot edge styling** - Bar edges now properly styled with black borders at save time (was previously applied before bars existed)
- **Style dict loading** - Fixed `finalize_special_plots()` to use correctly flattened style dict
- **CSV format** - Removed dtype header from CSV files for cleaner import into external tools (Excel, SigmaPlot, etc.)

## [0.10.0] - 2026-01-11

### Added
- **Graph visualization** - NetworkX graph support with `ax.graph(G)` method
- **Graph presets** - Built-in styles: `social`, `hierarchy`, `flow`, `minimal`
- **Node styling** - Size/color mapping from node attributes (e.g., `node_size="degree"`)
- **Interactive graphs** - Export to interactive HTML via pyvis integration
- **Label options** - `labels=True`, `labels="attribute"`, or `labels={dict}` for node labels

### Changed
- **Simplified API** - Reduced public exports from ~50 to 21 items for cleaner interface
- **Code organization** - Split large modules into focused files for maintainability
  - `_axes.py` → extracted `_axes_graph.py` (graph visualization)
  - `_core.py` → extracted `_reconstruct.py`, `_replay_graph.py`
- **CSV storage** - Always use CSV format for data storage (INLINE_THRESHOLD=0)

### Fixed
- **Editor reliability** - Improved demo recorder stability

## [0.9.1] - 2026-01-01

### Changed
- **README redesign** - Improved messaging with "Why", "Who", and "Philosophy" sections
- **Demo image** - Higher resolution GUI editor screenshot

## [0.9.0] - 2026-01-01

### Added
- **Desktop mode** - Native window support via pywebview (`fr.edit(desktop=True)`)
- **Tri-directional pane sync** - Canvas, datatable, and properties panels now synchronize bidirectionally
- **Datatable direct editing** - Excel-like cell editing with keyboard navigation (Ctrl+C/V/X, arrow keys)
- **Panel drag dual overlay** - Shows both axis edge (orange) and panel bbox (blue) during drag
- **Data cell highlighting** - Datatable highlights entire columns (headers + data rows) for selected elements
- **Figure caption section** - Edit figure caption directly in the editor
- **`fr.load()` alias** - Shorthand for `fr.reproduce()` for loading recipes
- **Directory save support** - Save figures to directories with `fr.save(fig, "path/to/dir/")`
- **ZIP bundle save** - Save complete figure bundles as `.zip` files
- **TIF/TIFF format** - Added TIF format support for image exports
- **Debug mode** - `fr.edit(debug=True)` shows server timestamp and detailed logs

### Changed
- **Panel bbox computation** - Now uses `ax.get_tightbbox()` for accurate bounds
- **Pre-commit speed** - Parallel pytest execution for faster commits
- **Server timestamp** - Hidden by default, shown only in debug mode

### Fixed
- **Pane sync matching** - Improved element-to-tab matching in tri-directional sync
- **Light mode visibility** - Column labels now visible when highlighted in light mode
- **Panel selection** - Panel/axes selections no longer overwrite element highlighting

## [0.8.1] - 2025-12-28

### Added
- **GUI PORT configuration** - `make gui PORT=5051` to specify custom port (default: 5050)
- **Click sound effects** - Browser demo recordings now include click sounds
- **Narration utilities export** - `extract_captions_from_script`, `add_narration_to_video` in browser module

### Changed
- **Demo recording improvements** - Color change and panel drag demos with better cursor synchronization
- **Video trimming margins** - Adjusted trim margins for cleaner demo output (1.5s start, 1s end)
- **Narration settings** - Lower BGM volume (0.08), longer fade-out (2s)

## [0.8.0] - 2025-12-27

### Added
- **Statistical annotations** - `fr.stats.add_significance()` for adding p-value annotations
- **p-value formatting** - `p_to_stars()` converts p-values to significance stars (*, **, ***, n.s.)
- **Smart alignment** - `fr.composition.smart_align()` for automatic panel alignment with asymmetric margins

### Fixed
- **Stats test assertions** - Correct n.s. assertion in p_to_stars test
- **Composition margins** - Use asymmetric margin variables in smart_align

## [0.7.6] - 2025-12-27

### Added
- **Demo movie infrastructure** - Automated recording and processing of demo videos
- **Full HD recording** - 1920x1080 resolution for demo videos
- **Timing metadata** - Automatic `.timing.json` generation for precise TTS sync
- **Parallel processing** - `process_all_demos.py` with `--workers` option
- **TTS integration** - ElevenLabs with gTTS fallback for narration
- **BGM support** - Background music with fade in/out effects

### Changed
- **README improvements** - Collapsible sections, enhanced readability

## [0.7.5] - 2025-12-25

### Added
- **Panel snapping** - Snap to grid (5mm), panel edges, and centers during drag
- **Magnetic attraction** - Panels slow down and "stick" as they approach snap targets
- **Visual alignment guides** - Orange/purple lines with opacity indicating proximity
- **Alt+Drag fine control** - Hold Alt to disable snapping for precise positioning

## [0.7.4] - 2025-12-25

### Added
- **Click priority z-index** - Scatter/legend have highest click priority, axes lowest
- **Legend drag-to-move** - Drag legends to reposition with x,y coordinates
- **Expanded panel bounds** - Panel drag includes title/label areas (15mm left, 8mm top, 12mm bottom margins)

### Fixed
- **Coordinate precision** - Legend drag uses upper-left corner for precise bbox_to_anchor positioning
- **Demo plot legend** - Added legend to plot demo for testing

## [0.7.3] - 2025-12-25

### Added
- **Panel drag-to-move** - Drag panels directly without modifier keys
- **mm coordinates** - Panel positions use mm units with upper-left origin
- **Restore positions** - Restore button now restores original panel coordinates
- **Server timestamp** - Debug timestamp visible in editor header

### Fixed
- **Container ID fix** - Fixed drag initialization (preview-container → zoom-container)
- **Null overlay check** - Added safety checks for drag overlay element

## [0.7.2] - 2025-12-25

### Added
- **Panel position editing** - View and edit panel positions numerically

## [0.7.1] - 2025-12-24

### Added
- **Panel selection** - Click to select panels in figure editor

## [0.7.0] - 2025-12-24

### Added
- **Hitmap improvements** - Enhanced element hit detection

## [0.6.0] - 2025-12-23

### Added
- **`ax.joyplot()`** - Ridgeline/joyplot visualization with KDE-based density estimation
- **`ax.swarmplot()`** - Beeswarm plot with non-overlapping point positioning
- **Theme switching** - Switch between SCITEX/MATPLOTLIB presets with live preview in editor
- **Theme CRUD** - View theme content, download as YAML, copy to clipboard
- **Legend controls** - Show/hide toggle, location dropdown, xy coordinate positioning
- **scipy dependency** - Added scipy>=1.7.0 for joyplot KDE computation

### Changed
- **Editor layout** - Moved axes size (width_mm, height_mm) from Figure tab to Axis tab

### Fixed
- **Tick direction validation** - Empty tick direction values no longer cause errors
- **Theme CommentedMap handling** - Fixed TypeError when switching themes with ruamel.yaml

## [0.5.1] - 2025-12-22

### Fixed
- **Dark theme colors** - Fixed typo in SCITEX preset: text/spine/tick now all use "#d4d4d4"
- **GitHub Actions CI** - Added automated testing workflow for Python 3.9-3.12

### Added
- **Example outputs** - Added `outputs/notebook/` with pre-generated example figures
- **Style presets tracked** - SCITEX.yaml and MATPLOTLIB.yaml now tracked in repo

## [0.5.0] - 2025-12-22

### Added
- **`fr.crop()`** - Crop images to content with mm-based margins
- **`validate_error_level` parameter** - Configurable validation handling:
  - `"error"` (default): Raise ValueError on validation failure
  - `"warning"`: Print warning but continue
  - `"debug"`: Silent, check result programmatically
- **Optional extras documentation** - README now documents `pip install figrecipe[seaborn,imaging,all]`

### Changed
- **`save()` API refactored** - Now returns `(image_path, yaml_path, result)` tuple
- **Path extension controls format** - `.png`, `.pdf`, `.svg`, `.jpg` supported
- **Default DPI** - Changed from 100 to 300 for publication quality
- **Development Status** - Updated from Alpha to Beta
- **Validation message** - "Validation: PASSED" → "Reproducible Validation: PASSED"

### Fixed
- **Legend styling in dark mode** - Font size, background color, and text color now applied via rcParams
- **`unload_style()` reset** - Now properly resets matplotlib rcParams to defaults
- **SCITEX preset alias** - Fixed alias direction (FIGRECIPE → SCITEX)
- **FTS typo** - "Statics" → "Statistics"

## [0.3.4] - 2025-12-21

### Added
- **Style presets** - Built-in style presets for easy switching:
  - `SCIENTIFIC` (default): Publication-quality with colorblind-friendly Wong 2011 palette
  - `MINIMAL`: Clean, minimal design with grayscale emphasis
  - `PRESENTATION`: Large fonts and bold lines for slides
- **`ps.list_presets()`** - List all available style presets
- **Custom YAML styles** - Load your own style files: `ps.load_style("/path/to/style.yaml")`
- **Reproducibility validation** - Validate recipe reproduces original figure:
  - `ps.save(fig, path, validate=True)` - Validate on save
  - `ps.validate(path)` - Standalone validation
  - Returns `ValidationResult` with MSE, dimensions, PSNR
- **Layout recording** - `subplots_adjust` parameters now recorded for pixel-perfect reproduction
- **Style recording** - Style parameters recorded and re-applied during reproduction

### Changed
- Renamed brand-specific "SCITEX" references to generic "SCIENTIFIC" preset
- `ps.load_style()` now accepts preset names: `ps.load_style("MINIMAL")`
- Default style is now the SCIENTIFIC preset

### Fixed
- **Pixel-perfect reproduction** - MM-layout and styled figures now reproduce with MSE=0

## [0.3.2] - 2025-12-21

### Added
- **Colorblind-friendly color palette** - Scientific color palette automatically applied via rcParams
  - Blue (#0072B2), Orange (#D55E00), Green (#009E73), Purple (#CC79A7), etc.
  - Access via `style.colors.palette` or auto-cycling in plots
- **Transparent background** - Default light theme now uses transparent background

### Fixed
- **Title overlap in multi-panel figures** - Added proper `subplots_adjust()` based on mm layout parameters
- **n_ticks** - Changed default from 5 to 4 for cleaner tick labels

### Changed
- Style applier now sets matplotlib color cycle from style palette

## [0.3.1] - 2025-12-21

### Fixed
- **Seaborn duplicate recording** - Seaborn calls no longer record underlying matplotlib calls (e.g., `ax.scatter()` from `sns.scatterplot()`)
- **Seaborn sizes parameter** - `sizes=(min, max)` tuples now correctly serialize and deserialize, fixing the legend reproduction issue where all size values were listed instead of grouped ranges

## [0.3.0] - 2025-12-21

### Added
- **MM-based layout system** for publication-quality figures
  - `axes_width_mm`, `axes_height_mm` parameters for precise axes sizing
  - `margin_left_mm`, `margin_right_mm`, `margin_bottom_mm`, `margin_top_mm` for margins
  - `space_w_mm`, `space_h_mm` for spacing between axes in multi-panel figures
- **Style system** inspired by SciTeX
  - `ps.load_style()` to load style configuration from YAML
  - `ps.apply_style()` to apply publication-quality styling to axes
  - `ps.STYLE` proxy for quick access to default style
  - `FIGRECIPE_STYLE.yaml` default configuration with:
    - Font sizes (axis labels, tick labels, title, legend)
    - Line thicknesses in mm
    - Tick parameters in mm
    - Theme support (light/dark mode)
- **Unit conversion utilities**
  - `ps.mm_to_inch()`, `ps.inch_to_mm()`
  - `ps.mm_to_pt()`, `ps.pt_to_mm()`
- Example `06_mm_layout_and_style.py` demonstrating new features

### Changed
- `ps.subplots()` now accepts mm-based layout parameters
- `ps.subplots()` accepts `apply_style_mm=True` for automatic style application
- Version updated to 0.3.0

## [0.2.0] - 2025-12-21

### Added
- CHANGELOG.md for tracking version history
- Version bump for PyPI publication

### Changed
- Version updated to 0.2.0

## [0.1.0] - 2025-12-21

### Added
- Core recording functionality via `ps.subplots()` wrapper
- YAML-based recipe format for figure serialization
- `ps.save()` function to export figures as recipes
- `ps.reproduce()` function to recreate figures from recipes
- `ps.info()` function to inspect recipe metadata
- CSV as default data format for human readability
- NPZ format support for binary data storage
- External data file support for large arrays (>100 elements)
- Custom call IDs for identifying plot elements
- Selective call reproduction via `calls` parameter
- Seaborn integration (`ps.sns.scatterplot()`, `ps.sns.lineplot()`, etc.)
- DataFrame column serialization for seaborn plots
- Makefile for common development tasks
- Comprehensive test suite (40 tests)
- Example scripts demonstrating core functionality

### Supported matplotlib methods
- `plot()` - line plots
- `scatter()` - scatter plots
- `bar()`, `barh()` - bar charts
- `fill_between()` - filled areas
- `step()` - step plots
- `errorbar()` - error bar plots
- `hist()` - histograms
- `imshow()` - image display
- `contour()`, `contourf()` - contour plots
- `set_xlabel()`, `set_ylabel()`, `set_title()` - decorations
- `legend()`, `grid()` - additional decorations

### Supported seaborn functions
- `scatterplot()` - scatter plots with hue/size support
- `lineplot()` - line plots with confidence intervals
- Additional functions available but may need further testing

[0.24.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.24.0...v0.24.1
[0.24.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.22.0...v0.23.0
[0.22.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.20.0...v0.21.0
[0.20.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.19.0...v0.20.0
[0.19.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.18.0...v0.19.0
[0.18.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.17.0...v0.18.0
[0.17.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.16.2...v0.17.0
[0.16.2]: https://github.com/ywatanabe1989/figrecipe/compare/v0.16.1...v0.16.2
[0.16.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.7.6...v0.8.0
[0.7.6]: https://github.com/ywatanabe1989/figrecipe/compare/v0.7.5...v0.7.6
[0.6.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.3.4...v0.5.0
[0.3.4]: https://github.com/ywatanabe1989/figrecipe/compare/v0.3.2...v0.3.4
[0.3.2]: https://github.com/ywatanabe1989/figrecipe/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/ywatanabe1989/figrecipe/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ywatanabe1989/figrecipe/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ywatanabe1989/figrecipe/releases/tag/v0.1.0
