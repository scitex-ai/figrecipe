---
description: |
  [TOPIC] Quick start
  [DETAILS] Smallest example — subplots → plot_line → save (PNG + companion CSV).
tags: [figrecipe-quick-start]
---

# Quick Start

## Hello plot

```python
import figrecipe as fr

fig, ax = fr.subplots()
ax.plot_line([1, 2, 3], [1, 4, 9], label="quadratic")
ax.set_xyt("x", "y", "Demo")
fr.save(fig, "demo.png")        # writes demo.png + demo.csv
```

## Reproduce from a recipe

```python
fr.reproduce("demo.png.recipe.yaml")
```

## Compose multiple panels

```python
panel_a = fr.subplots()[0]
panel_b = fr.subplots()[0]
composed = fr.compose([panel_a, panel_b], layout="2x1")
fr.save(composed, "two-panel.png")
```

## Crop whitespace

```python
from figrecipe import crop
crop("plot.png", out="plot-tight.png")
```

## Apply a publication style

```python
fr.load_style("SCITEX")          # mm-precision, journal-friendly
fig, ax = fr.subplots()
# … plot …
fr.save(fig, "paper-fig.pdf")
```

## Next

- [03_python-api.md](03_python-api.md) — full surface
- [04_cli-reference.md](04_cli-reference.md) — `figrecipe` CLI
- [16_plot-types.md](16_plot-types.md) — all supported plot types
- [17_composition.md](17_composition.md) — multi-panel layouts
- [05_styles.md](05_styles.md) — SCITEX / MATPLOTLIB presets
