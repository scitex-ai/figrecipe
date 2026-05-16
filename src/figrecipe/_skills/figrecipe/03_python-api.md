---
description: |
  [TOPIC] Python API
  [DETAILS] Public callables grouped by area — figures, save/reproduce, layout, styles, diagrams, inspection.
tags: [figrecipe-python-api]
---

# Python API

```python
import figrecipe as fr
```

## Figures

| Symbol | Purpose |
|---|---|
| `subplots(...)` | Drop-in `matplotlib.pyplot.subplots` returning enriched wrappers |
| `Figz` | Enriched figure wrapper (data tracking, mm sizing) |
| `Pltz` | Enriched axes wrapper (`plot_line`, `set_xyt`, …) |
| `sns` | Seaborn passthrough (with style harmonization) |

## Save / load / reproduce

| Symbol | Purpose |
|---|---|
| `save(fig, path)` | Save image + companion CSV + recipe YAML |
| `load(path)` | Load a saved figure spec |
| `reproduce(spec)` | Re-render from a recipe |
| `save_bundle(...)` | ZIP bundle (spec.json + data.csv + exports) |
| `load_bundle(...)` | Inverse of `save_bundle` |
| `reproduce_bundle(...)` | Re-render from a bundle |

## Layout / composition

| Symbol | Purpose |
|---|---|
| `compose(panels, layout=...)` | Multi-panel composition |
| `align_panels(...)` | Align edges of panels |
| `distribute_panels(...)` | Even spacing |
| `align_smart(...)` | Heuristic alignment |
| `crop(img, ...)` | Whitespace-aware image cropping |

## Styles

| Symbol | Purpose |
|---|---|
| `load_style(name)` | Apply a preset (e.g. `"SCITEX"`, `"MATPLOTLIB"`) |
| `unload_style()` | Restore previous matplotlib rcParams |
| `list_presets()` | Enumerate available preset names |
| `colors` | Curated palette accessors |
| `signature`, `caption_with_signature` | Provenance string + caption helper |

## Diagrams

| Symbol | Purpose |
|---|---|
| `Diagram` | Box-and-arrow diagrams; backends: matplotlib / Mermaid / Graphviz |

## Inspection / validation / extraction

| Symbol | Purpose |
|---|---|
| `info(spec)` | Summarize a recipe |
| `validate(spec)` | Verify a recipe re-renders to the same image |
| `extract_data(spec)` | Recover plotted arrays from a recipe |

## Interactive

| Symbol | Purpose |
|---|---|
| `gui()` | Launch interactive editor (requires `[editor]` extra) |

## See also

- [04_cli-reference.md](04_cli-reference.md) — CLI mirroring most of this surface
- [16_plot-types.md](16_plot-types.md) — full catalog of plot types
- [05_styles.md](05_styles.md) — preset details
- [07_diagram.md](07_diagram.md) — Diagram backends
