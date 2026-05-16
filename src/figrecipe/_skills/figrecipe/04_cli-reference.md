---
description: |
  [TOPIC] CLI reference
  [DETAILS] `figrecipe` console entry — plot, reproduce, compose, gui, convert, crop, diff, hitmap, extract, validate, info, diagram, style, fonts.
tags: [figrecipe-cli-reference]
---

# CLI Reference

```
figrecipe [OPTIONS] COMMAND [ARGS]...
```

Reproducible, style-editable scientific figures via YAML recipes.
Use `figrecipe gui` to launch the GUI editor.

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
| `validate` | Validate that a recipe reproduces its original figure |
| `info` | Show information about a recipe |

### Diagram

| Command | Purpose |
|---|---|
| `diagram` | Create and manage diagrams (flowcharts, pipelines, …) |

### Style + appearance

| Command | Purpose |
|---|---|
| `style` | Manage figure styles and presets |
| `fonts` | List or check available fonts |

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
