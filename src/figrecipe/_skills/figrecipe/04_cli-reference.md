---
description: |
  [TOPIC] CLI reference
  [DETAILS] `figrecipe` console entry — plot, reproduce, compose, gui, convert, crop, diff, show-hitmap, extract, validate, info, diagram, style, list-fonts.
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
| `--json` | Set a context preference; only subcommands consuming it change output |
| `-h`, `--help` | Show this message and exit |

For `list-fonts`, both `figrecipe --json list-fonts` and
`figrecipe list-fonts --json` emit structured output, including checks and
filtered inventories. A missing exact font still exits 1 with
`available: false`; fallback faces do not count as availability. Root/local
flag combinations and text output are covered by
`tests/figrecipe/_cli/test__fonts.py`.

Diagram discovery also honors both positions: `figrecipe --json diagram
show-presets` and `figrecipe diagram show-presets --json` return the same
structured data. This applies to `diagram show-info PATH`, `show-presets`
and `show-backends`, with root/local/both flags, default text and missing-file
behavior covered by `tests/figrecipe/_cli/test__diagram.py`. Backend discovery
reports local availability; it does not establish successful rendering.
Image comparison accepts both `figrecipe --json diff a.png b.png` and
`figrecipe diff a.png b.png --json`. Both return the existing pixel statistics,
including `is_match`, without writing a difference image. Matching and
one-pixel-different inputs, root/local/both flags and ordinary text output are
covered by `tests/figrecipe/_cli/test__diff.py`. A completed comparison exits 0
even when `is_match` is false; command/input errors remain errors.

Read-only metadata commands also accept the root flag: `info RECIPE`,
`show-version` (including `--full`), `style list`, `style show NAME`, and
`list-python-apis`. For example, `figrecipe --json style show SCITEX` and
`figrecipe style show SCITEX --json` return the same preset data. Their existing
JSON schemas are preserved. Plain `style show` emits the preset as YAML;
an unknown preset exits 1 instead of returning null success. These behaviors
are covered by `tests/figrecipe/_cli/test__style.py`. Recipe metadata is about
the loaded recipe, not proof that its saved image reproduces. Owning controls:
`tests/integration/test_cli_metadata_json.py`; root/local/both forms are compared
using a normally saved, validated recipe and actual installed metadata.

Other commands' consumption of the root preference remains a separate check;
use their own `--json` when available. In particular, these read-only checks do
not qualify GUI lifecycle operations, hitmap generation or MCP discovery.

## Configuration scope

The target SciTeX precedence chain is:

```
config.yaml -> $FIGRECIPE_CONFIG -> ~/.scitex/figrecipe/config.yaml -> defaults
```

The CLI entry point (`_cli/_main.py::main`) does not implement this loader.
Use explicit command options and input files. In a controlled check,
`list-fonts --check "DejaVu Sans" --json` ignores malformed local `config.yaml`
and `$FIGRECIPE_CONFIG` files; that is a configuration-consumption gap, not
evidence of working precedence. Style and GUI readers have separate scope.
The shared configuration contract remains outstanding.

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
| `show-hitmap` | Generate hitmap visualization from two images |

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
figrecipe plot spec.yaml -o figure.png --save-recipe
figrecipe reproduce figure.yaml
figrecipe crop figure.png
figrecipe diff a.png b.png
figrecipe diagram create flow.mmd --format mermaid
figrecipe style list
```

`plot` consumes a declarative specification (`figure` and `plots`), while
`reproduce` consumes the recorded companion recipe. These are different inputs.
Graph compilation commands under `diagram` use `GraphDiagram`; the mm-based
box-and-arrow builder remains `fr.Diagram`.
Owning graph CLI controls are in `tests/figrecipe/_cli/test__diagram.py`.

For per-command flags, run `figrecipe <command> --help` or
`figrecipe --help-recursive`.

## See also

- [11_cli-reference.md](11_cli-reference.md) — extended legacy reference
- [13_cli-extras.md](13_cli-extras.md) — auxiliary CLI notes
- [12_mcp-tools.md](12_mcp-tools.md) — MCP equivalents
