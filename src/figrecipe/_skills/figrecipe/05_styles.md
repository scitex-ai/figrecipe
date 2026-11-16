---
description: |
  [TOPIC] Styles
  [DETAILS] loading, applying, and customizing SCITEX/MATPLOTLIB styles and dark themes.
tags: [figrecipe-styles, figrecipe]
---


# Styles

## What the SCITEX style is

`SCITEX` is figrecipe's default **publication-quality** style — a Nature/journal-
oriented look defined in millimetres (so figures are print-exact regardless of
DPI) rather than inches/points. It is the house style of the SciTeX ecosystem;
`scitex.plt` activates it automatically (via `FIGRECIPE_BRAND="scitex.plt"`, which
triggers `figrecipe._brand_style`).

Source of truth: `figrecipe/styles/presets/SCITEX.yaml` (the `load_style("SCITEX")`
preset) and the flat-kwargs variant `figrecipe/presets/SCITEX_STYLE.yaml`
(`SCITEX_STYLE`, splatted into `subplots(**SCITEX_STYLE)`).

What it sets (from `SCITEX.yaml`):

```yaml
axes:
  width_mm: 40        # ~1 : 0.7 aspect
  height_mm: 28
  thickness_mm: 0.2   # spines; top/right hidden
margins:              # final output margin after auto-crop
  left_mm: 1
  right_mm: 1
  bottom_mm: 1
  top_mm: 1
spacing:
  horizontal_mm: 10   # between columns
  vertical_mm: 15     # between rows (title + xlabel space)
fonts:
  family: "Arial"     # DejaVu Sans fallback (Docker)
  axis_label_pt: 7
  tick_label_pt: 7
  title_pt: 8
  suptitle_pt: 9
  legend_pt: 6
ticks:
  length_mm: 0.8
  thickness_mm: 0.2
  direction: "out"
  n_ticks_min: 3      # 3–4 per axis
  n_ticks_max: 4
lines:
  trace_mm: 0.12
markers:
  scatter_mm: 0.8
# + legend frameon=False, mathtext upright (regular fontset),
#   300 DPI save, SCITEX colour palette ("blue" → SciTeX blue).
```

Variants: `SCITEX_DARK` (dark background), `MATPLOTLIB` (vanilla defaults).

## fr.load_style()

```python
def load_style(
    style="SCITEX",      # preset name, path to YAML, None/False to unload
    dark=False,          # apply dark theme transformation
    background=None,     # override background: "white", "transparent", etc.
) -> DotDict | None
```

After calling `load_style()`, subsequent `fr.subplots()` calls automatically use the loaded style.

## Japanese and other CJK labels

Install a font with the glyphs you need in the environment that creates and
reproduces the figure. Figrecipe does not install or embed font files. The
configured Latin face (Arial in SCITEX) alone does not cover Japanese.

List the actual installed family names, then check the exact family you intend
to use. A fallback face is not evidence that the requested family is installed:

```bash
figrecipe list-fonts --search "Noto" --json
figrecipe list-fonts --check "Noto Sans JP" --json
```

A missing family produces `"available": false` and exit status 1. Install it
before continuing. Use your installed family's exact name; `Noto Sans JP` is
an example, and `IPAexGothic` is another possible choice when installed.

For recorded plots, `FIGRECIPE_CJK_FONT` selects an installed fallback before
the built-in candidate list. Set it before the first font lookup in a fresh
Python process, for example when running the following script:

```bash
FIGRECIPE_CJK_FONT="Noto Sans JP" python my_figure.py
```

```python
import figrecipe as fr

fr.load_style("SCITEX")
fig, ax = fr.subplots()
ax.plot([0, 1, 2], [1, 3, 2])
ax.set_title("日本語")
ax.set_xlabel("月")
fr.save(fig, "japanese.png", validate=True)
```

Use the same font environment when reproducing the recipe. Restart Python after
installing a font or changing the override, because fallback resolution is
cached. An unavailable override warns and tries the built-in candidates; it
does not install the missing font. Avoid changing native Matplotlib `Text`
objects after plotting: those mutations are not recorded and can make recipe
validation fail. This workflow does not establish standalone Diagram box/arrow
font support or preserve manual `rcParams` font preference order.

## Built-in presets

| Preset | Description |
|--------|-------------|
| `"SCITEX"` / `"FIGRECIPE"` | Scientific publication style (default) |
| `"SCITEX_DARK"` / `"FIGRECIPE_DARK"` | Dark variant |
| `"MATPLOTLIB"` | Vanilla matplotlib defaults |

```python
import figrecipe as fr

# Scientific publication style (default)
fr.load_style()
fr.load_style("SCITEX")  # explicit

# Dark theme
fr.load_style("SCITEX_DARK")
fr.load_style("SCITEX", dark=True)  # equivalent

# Opaque white background (default is transparent)
fr.load_style("SCITEX", background="white")

# Vanilla matplotlib
fr.load_style("MATPLOTLIB")
fr.load_style(None)   # unload (same as MATPLOTLIB)
fr.load_style(False)  # unload
```

## fr.unload_style()

```python
fr.unload_style()
# Resets to matplotlib defaults; next subplots() is unstyled
```

## fr.list_presets()

```python
presets = fr.list_presets()
# Returns list of available preset names
```

## CLI: figrecipe style

```bash
figrecipe style list              # list all presets
figrecipe style show SCITEX       # show SCITEX style details
figrecipe style apply SCITEX      # apply style globally
figrecipe style reset             # reset to matplotlib defaults
```

## MCP: plt_list_styles

```python
result = plt_list_styles()
# result: {"presets": ["SCITEX", "SCITEX_DARK", "MATPLOTLIB", ...], "count": N}
```

## Custom style from YAML

```python
fr.load_style("/path/to/my_style.yaml")
```

## Accessing style values

```python
style = fr.load_style("SCITEX")
style.axes.width_mm   # 40 (default axes width)
style.axes.height_mm
style.fonts.title_pt   # 8 in SCITEX
```

## Style in declarative spec

```yaml
figure:
  width_mm: 80
  height_mm: 60
  style: SCITEX          # applied before plotting
  facecolor: white       # optional opaque background
```
