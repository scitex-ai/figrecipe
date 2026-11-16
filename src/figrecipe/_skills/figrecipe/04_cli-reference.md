---
description: |
  [TOPIC] CLI reference
  [DETAILS] `figrecipe` console entry — plot, reproduce, compose, gui, convert, crop, diff, hitmap, extract, validate, info, diagram, style, list-fonts.
tags: [figrecipe-cli-reference]
---

# CLI Reference

```
figrecipe [OPTIONS] COMMAND [ARGS]...
```

Reproducible, style-editable scientific figures via YAML recipes.
Use `figrecipe gui open` to launch the GUI editor.

## Global options

| Flag | Purpose |
|---|---|
| `-V`, `--version` | Show version and exit |
| `--help-recursive` | Show help for all commands |
| `--json` | Emit structured JSON (propagates to subcommands) |
| `-h`, `--help` | Show this message and exit |

## Configuration precedence

```
config.yaml -> $FIGRECIPE_CONFIG -> ~/.scitex/figrecipe/config.yaml -> defaults
```

## Commands

### Figure creation

| Command | Purpose |
|---|---|
| `plot` | Create a figure from a declarative YAML/JSON spec |
| `reproduce` | Reproduce a figure from a YAML recipe |
| `compose` | Compose multiple figures into one |
| `gui` | Launch interactive GUI editor (requires `[editor]` extra) |

### Image processing

| Command | Purpose |
|---|---|
| `convert` | Convert between figure formats |
| `crop` | Crop an image to its content area |
| `diff` | Compare two images and report pixel differences |
| `hitmap` | Generate hitmap visualization from two images |

### Data + validation

| Command | Purpose |
|---|---|
| `extract` | Extract plotted data arrays from a recipe |
| `validate` | Render a recipe twice and compare those renders for self-consistency |
| `info` | Show information about a recipe |

### Diagram

| Command | Purpose |
|---|---|
| `diagram` | Create and manage diagrams (flowcharts, pipelines, …) |

### Style + appearance

| Command | Purpose |
|---|---|
| `style` | Manage figure styles and presets |
| `list-fonts` | List or check available fonts |

`list-fonts` is the registered command name (`_cli/_fonts.py`); the Python
callback is named `fonts`. For example,
`figrecipe list-fonts --check "DejaVu Sans" --json` reports exact installed-family
availability. Font fallback does not count as availability; a missing family
returns `available: false` and exit 1. Owning controls are in
`tests/figrecipe/_cli/test__fonts.py`.

Standalone `validate` calls `_api/_validate.py::validate_recipe`: it compares
two replays, rather than a replay with the original image. A passing result
establishes recipe self-consistency, not fidelity to the original plot.
The ordinary `fr.save` validation is a separate check.

## Examples

```bash
figrecipe plot recipe.yaml -o figure.png
figrecipe reproduce figure.png.recipe.yaml
figrecipe crop figure.png
figrecipe diff a.png b.png
figrecipe diagram create flow.yaml --backend mermaid
figrecipe style list
```

For per-command flags, run `figrecipe <command> --help` or
`figrecipe --help-recursive`.

## See also

- [11_cli-reference.md](11_cli-reference.md) — extended legacy reference
- [13_cli-extras.md](13_cli-extras.md) — auxiliary CLI notes
- [12_mcp-tools.md](12_mcp-tools.md) — MCP equivalents
