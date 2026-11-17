---
description: |
  [TOPIC] Cropping
  [DETAILS] Crop whitespace from figure images using mm or pixel margins. Requires Pillow (figrecipe[imaging]).
tags: [figrecipe-cropping, figrecipe]
---


# Cropping

Removes whitespace borders from saved raster images, leaving the content area
with a specified margin. PNG and JPEG are supported through Pillow. PDF input
is not supported; export a raster image before calling crop.

Requires: `pip install figrecipe[imaging]` (Pillow).

## fr.crop()

```text
def crop(
    input_path,
    output_path=None,       # default: input with "_cropped" suffix
    margin_mm=1.0,          # margin in millimeters (default: 1.0)
    margin_px=None,         # margin in pixels (overrides margin_mm)
    overwrite=False,        # overwrite input file in place
    verbose=False,
    return_offset=False,    # if True, return (path, offset_dict)
) -> Path | Tuple[Path, dict]
```

## Examples

```python
import figrecipe as fr

# Crop with default 1mm margin
fr.crop("figure.png")
# → figure_cropped.png

# Specify output path
fr.crop("figure.png", output_path="figure_tight.png")

# Larger margin
fr.crop("figure.png", margin_mm=3.0)

# Pixel margin
fr.crop("figure.png", margin_px=10)

# Overwrite in place
fr.crop("figure.png", overwrite=True)

# Get crop offset metadata
path, offset = fr.crop("figure.png", return_offset=True)
# offset: {"left": N, "top": N, "right": N, "bottom": N}  (pixels)
```

The public `fr.crop()` supports one uniform millimeter or pixel margin. The
CLI exposes one uniform `--margin` in mm or px; the MCP tool exposes one uniform
`margin_mm`. Per-side margins and an explicit crop box are internal utility
options, not parameters of these public interfaces.

## CLI: figrecipe crop

```bash
# Default 1mm margin
figrecipe crop figure.png

# Specify output
figrecipe crop figure.png -o figure_tight.png

# Custom margin in mm
figrecipe crop figure.png --margin 2mm

# Custom margin in pixels
figrecipe crop figure.png --margin 10px

# Overwrite in place
figrecipe crop figure.png --overwrite
```

## MCP tool: plt_crop

```python
result = plt_crop(
    input_path="figure.png",
    output_path=None,       # optional; defaults to input with "_cropped" suffix
    margin_mm=1.0,
    overwrite=False,
)
# result: {"output_path": "figure_cropped.png", "success": True}
```

## Auto-crop on compose

Figures created by `fr.compose()` are automatically marked for 1mm-margin cropping when saved. This happens transparently during `fr.save()` — no explicit crop call needed for composed figures.

## Implementation and behavioral coverage

The public Python wrapper is `figrecipe._api._public.crop`, delegating to
`figrecipe._utils._crop.crop`; the CLI adapter is
`figrecipe._cli._crop.crop`, and the MCP adapter is
`figrecipe._mcp.server.plt_crop`. Legacy crop dispatch controls live in
`tests/figrecipe/_api/test__save_crop.py`; mode/metadata/padding controls live in
`tests/integration/test_crop_corner_sampling.py`. A raster export is required
for PDF figures; these adapters do not provide a PDF rasterizer.
