# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.29.0] — 2026-06-07

### Added

- **`figrecipe.media` submodule** — media handling (detect / classify / show)
  absorbed from the scitex-python umbrella per Phase B routing. The operator
  reneged scitex-python ADR-0001 (which had this module landing in
  scitex-etc): media belongs with figure rendering, not with the etc
  catch-all. Public surface:
  - `figrecipe.media.render.classify(path)`
  - `figrecipe.media.render.detect(text, root_path=...)`
  - `figrecipe.media.render.show(path, target=...)`
  - `python -m figrecipe.media.render {show,classify,detect} ...` CLI
  - `figrecipe.media.render.mcp_server` MCP tools (optional fastmcp dep)

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
