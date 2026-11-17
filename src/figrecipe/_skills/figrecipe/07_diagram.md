---
description: |
  [TOPIC] Diagram
  [DETAILS] Box-and-arrow diagram builder and Mermaid/Graphviz diagram compilation via fr.Diagram.
tags: [figrecipe-diagram, figrecipe]
---


# Diagrams

figrecipe supports two diagram types: box-and-arrow builders (Python API) and text-format diagrams (Mermaid and Graphviz).

## fr.Diagram — Box-and-arrow builder

```python
import figrecipe as fr

diagram = fr.Diagram(width_mm=110, height_mm=45)
diagram.add_box(
    "input", "Input", shape="box",
    x_mm=25, y_mm=22, width_mm=35, height_mm=18,
)
diagram.add_box(
    "output", "Output", shape="box",
    x_mm=85, y_mm=22, width_mm=35, height_mm=18,
)
diagram.add_arrow("input", "output")
path = diagram.save("flow.png", save_debug=False)
```

Box positions (`x_mm`, `y_mm`) are **centres in millimetres**, not top-left
corners. With the explicit canvas size above, `(0, 0)` is the bottom-left
and y increases upward. Leave at least half a box's width/height between
its centre and the canvas edge so the box fits.

`diagram.render()` returns a Matplotlib `(fig, ax)` pair; its optional first
argument is an axes, **not a filename**. Use `diagram.save(path)` (also
available as `render_to_file(path)`) to write an image. A valid save also
writes the diagram recipe beside it. `save_debug=False` omits the separate
debug image. If layout validation fails, the returned path has a `_FAILED`
suffix and an error reports the failed rule and offending element IDs;
that diagnostic is not a valid output, and no recipe is written for it.
PNG, SVG and PDF saves report the same validation outcome: failed artifacts
log the rule and offending IDs at error level and never log a save success.
A valid vector save logs its filename without claiming raster dimensions.
Owning controls: `tests/figrecipe/_diagram/_diagram/test__io.py`.

## Mermaid diagrams

```python
from figrecipe._diagram._mermaid.mermaid import Mermaid

m = Mermaid("graph LR; A-->B; B-->C")
m.render("flow.png")
```

## Graphviz diagrams

```python
from figrecipe._diagram._graphviz.graphviz import Graphviz

g = Graphviz("digraph { A -> B -> C }")
g.render("graph.png")
```

## CJK text and recipe geometry

Native diagram box text, container/diagram titles and arrow labels append the
installed CJK fallback without requiring an earlier `fr.subplots()` call.
Set `FIGRECIPE_CJK_FONT` to an installed family name before the first font
lookup when the built-in candidate list does not select the font you need.
The original serif, sans-serif and plain-code monospace choices are retained;
font files must also be available in the environment that replays the recipe.
Syntax-highlighted code text has its own rendering path.

Arrow endpoint adjustments, label offsets and margins are saved with the
recipe, so a positioned label does not move back over its arrow on replay.
Older recipes retain their previous defaults; reconstruct any adjustments
omitted by an older writer before resaving them.

## Diagram presets

```python
from figrecipe._diagram import list_presets, get_preset

presets = list_presets()
# ["WORKFLOW", "DECISION", "PIPELINE", "SCIENTIFIC"]

preset = get_preset("WORKFLOW")
```

## MCP tools

| Tool | Purpose |
|------|---------|
| `plt_diagram_create` | Create diagram from spec dict |
| `plt_diagram_render` | Render diagram to image |
| `plt_diagram_compile_mermaid` | Compile Mermaid text to image |
| `plt_diagram_compile_graphviz` | Compile Graphviz DOT to image |
| `plt_diagram_list_presets` | List available diagram presets |
| `plt_diagram_get_preset` | Get preset configuration |
| `plt_diagram_get_backends` | List available render backends |
| `plt_diagram_get_paper_modes` | List paper size modes |
| `plt_diagram_split` | Split diagram across pages |

## CLI: figrecipe diagram

```bash
# Render a Mermaid file
figrecipe diagram render flow.mmd -o flow.png

# Create from preset
figrecipe diagram create --preset WORKFLOW

# List available backends
figrecipe diagram --help
```

## Diagram schema types

```python
from figrecipe._diagram import (
    DiagramSpec,    # full diagram specification
    NodeSpec,       # node definition
    EdgeSpec,       # edge/arrow definition
    DiagramType,    # "flowchart", "sequence", etc.
    PaperMode,      # "A4", "letter", custom
    SpacingLevel,   # "compact", "normal", "spacious"
    ColumnLayout,   # column arrangement hints
    LayoutHints,    # layout algorithm hints
    PaperConstraints,
)
```
