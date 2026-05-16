---
name: figrecipe
description: |
  [WHAT] Publication-ready matplotlib figures with mm-precision layouts, YAML recipes, declarative specs, multi-panel composition, whitespace cropping, style presets (SCITEX, MATPLOTLIB), and box-and-arrow diagrams.
  [WHEN] Use when the user asks to "make a figure", "plot this data", "save a figure", "lay out panels at exact mm sizes", "compose panels A/B/C", "crop whitespace", "reproduce a figure", "plot mean ± CI", "confusion matrix", "raster plot", "apply SCITEX style".
  [HOW] `import figrecipe` for the Python API; see leaf skills for entry points.
tags: [figrecipe]
allowed-tools: mcp__scitex__plt_*
primary_interface: mixed
interfaces:
  python: 3
  cli: 1
  mcp: 3
  skills: 2
  hook: 0
  http: 0
---


# figrecipe

> **Interfaces:** Python ⭐⭐⭐ · CLI ⭐ · MCP ⭐⭐⭐ · Skills ⭐⭐ · Hook — · HTTP —

## Installation & import

`pip install figrecipe` installs the standalone:

```python
import figrecipe
```

This package does not ship as a submodule of the `scitex` umbrella.

## Sub-skills

### Mandatory
* [01_installation](01_installation.md) — pip install + extras + verify
* [02_quick-start](02_quick-start.md) — subplots → save → reproduce
* [03_python-api](03_python-api.md) — Public callables grouped by area
* [04_cli-reference](04_cli-reference.md) — `figrecipe` console entry

### Deep-dive
* [05_styles](05_styles.md) — Style presets, SCITEX/MATPLOTLIB, custom styles
* [06_bundle](06_bundle.md) — ZIP bundle format (spec.json + data.csv + exports)
* [07_diagram](07_diagram.md) — Box-and-arrow diagrams, Mermaid, Graphviz
* [15_quick-start](15_quick-start.md) — Legacy quick-start (preserved)
* [16_plot-types](16_plot-types.md) — All supported plot types with examples
* [17_composition](17_composition.md) — Multi-panel figure composition (grid and mm-based)
* [18_cropping](18_cropping.md) — Figure cropping, whitespace removal

### Workflows
* [10_workflows](10_workflows.md) — Common figure workflows
* [11_cli-reference](11_cli-reference.md) + [13_cli-extras](13_cli-extras.md) — Extended CLI notes
* [12_mcp-tools](12_mcp-tools.md) + [14_mcp-tool-catalog](14_mcp-tool-catalog.md) — MCP tool reference

### Standards
* [20_return-fig](20_return-fig.md) — Convention: plotting functions must return fig

## At a glance

- MCP tools — see [12_mcp-tools.md](12_mcp-tools.md)
- CLI commands — see [11_cli-reference.md](11_cli-reference.md)
- Env vars — see [30_env-vars.md](30_env-vars.md)
