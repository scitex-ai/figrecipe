---
description: |
  [TOPIC] Mcp Tools
  [DETAILS] figrecipe MCP tools for AI agents — creating, composing, cropping, validating, and extracting data from figures.
tags: [figrecipe-mcp-tools, figrecipe]
---


# MCP Tools

All tools are prefixed `plt_` and available via the figrecipe MCP server.

Start server: `figrecipe mcp start`

## Core figure tools

### plt_plot

Create a matplotlib figure from a declarative specification dict.

```python
result = plt_plot(
    spec={
        "figure": {"width_mm": 80, "height_mm": 60, "style": "SCITEX"},
        "plots": [
            {"type": "line", "x": [1,2,3,4,5], "y": [1,4,9,16,25],
             "color": "blue", "label": "quadratic"}
        ],
        "xlabel": "X",
        "ylabel": "Y",
        "title": "My Plot",
    },
    output_path="figure.png",
    dpi=300,
    save_recipe=True,
)
# result: {"image_path": "figure.png", "recipe_path": "figure.yaml", "success": True}
```

Full spec format: see `figrecipe://spec-schema` MCP resource.

### plt_reproduce

Reproduce a figure from a saved YAML recipe.

```python
result = plt_reproduce(
    recipe_path="figure.yaml",
    output_path=None,        # defaults to figure.reproduced.png
    format="png",            # "png", "pdf", "svg"
    dpi=300,
)
# result: {"output_path": "figure.reproduced.png", "success": True}
```

### plt_compose

Compose multiple figures into one panel figure.

```python
# Grid-based (list sources)
result = plt_compose(
    sources=["panel_a.png", "panel_b.png", "panel_c.png"],
    output_path="figure.png",
    layout="horizontal",       # "horizontal", "vertical", "grid"
    gap_mm=5.0,
    panel_labels=True,
    label_style="uppercase",   # "uppercase", "lowercase", "numeric"
    dpi=300,
    save_recipe=True,
)

# Free-form mm-based (dict sources)
result = plt_compose(
    sources={
        "panel_a.yaml": {"xy_mm": [0, 0], "size_mm": [80, 50]},
        "panel_b.yaml": {"xy_mm": [90, 0], "size_mm": [80, 50]},
    },
    output_path="figure.png",
    canvas_size_mm=[180, 60],
)
# result: {"output_path": ..., "success": True, "layout_spec": ..., "recipe_path": ...}
```

## Image processing

### plt_crop

Crop whitespace from a figure image.

```python
result = plt_crop(
    input_path="figure.png",
    output_path=None,          # defaults to input + ".cropped" suffix
    margin_mm=1.0,
    overwrite=False,
)
# result: {"output_path": "figure.cropped.png", "success": True}
```

## Information and validation

### plt_info

Get metadata about a recipe file.

```python
result = plt_info(
    recipe_path="figure.yaml",
    verbose=False,
)
# result: dict with figure dimensions, axes count, call counts, etc.
```

### plt_validate

Validate that a recipe can reproduce its original figure.

```python
result = plt_validate(
    recipe_path="figure.yaml",
    mse_threshold=100.0,
)
# result: {"valid": True, "mse": 0.5, "message": "...", "recipe_path": "..."}
```

### plt_extract_data

Extract plotted data arrays from a recipe.

```python
result = plt_extract_data(recipe_path="figure.yaml")
# result: {"call_id": {"x": [...], "y": [...]}, ...}
# Arrays are serialized as lists for JSON compatibility
```

## Discovery

### plt_get_plot_types

```python
result = plt_get_plot_types()
# result: {
#   "plot_types": ["line", "scatter", "bar", ...],
#   "mapping": {"line": "plot", "scatter": "scatter", ...},
#   "categories": {
#     "line_curve": ["line", "plot", "step", ...],
#     "scatter_points": ["scatter"],
#     ...
#   }
# }
```

### plt_list_styles

```python
result = plt_list_styles()
# result: {"presets": ["SCITEX", "SCITEX_DARK", "MATPLOTLIB", ...], "count": N}
```

## More tools

- Per-type plot tools, SciTeX scientific plot tools, Diagram tools, and MCP Resources — see [14_mcp-tool-catalog.md](14_mcp-tool-catalog.md)
