# Rendering ink beyond the canvas during a content crop

The raster content-crop path now renders overflowing content before cropping.
Previously it saved the original canvas first, then padded a larger recorded
crop box. A legend beyond that canvas became blank padding, even when recipe
replay had MSE 0 against the clipped image.

This change applies to the existing deterministic crop routes: millimetre
layouts with crop margins and non-collapsed constrained-layout raster exports.
When the recorded content extent exceeds the canvas, the exporter combines it
with the actual output-DPI tight extent and renders that explicit Matplotlib
bounding box, including the requested margins. Output-DPI measurement matters
because font hinting can change text width. Axes are not stretched or resized.
In-bounds output and fixed-canvas exports without a requested crop keep their
existing paths. Vector output and other legacy crop routes are not changed.

Crop metadata uses the original physical canvas as its coordinate reference.
The hitmap uses the same explicit extent, avoiding a second crop or a separate
"tight" remeasurement. Its existing pixel budget is also applied to explicit
bounding-box dimensions; the limits and fallback bounds are unchanged.

The source is `_api/_save_extent.py`, its save/hitmap integration in
`_api/_save.py`, and the explicit-bbox budget check in `_editor/_hitmap_main.py`.
`tests/integration/test_overflow_content_crop.py` checks actual outside legend
ink and clearance, physical axes sizing at the output pixel resolution,
fixed-canvas compatibility, hitmap alignment/budget, background handling and
pixel equality after extra replay draws. The selected inspected fixture uses
an entire outside legend and explicit 2 mm margins.

Image replay validation remains enabled with the same thresholds and failure
behavior. It establishes reproduction, not completeness of the source figure:
visual/content checks are still necessary. This bounded raster correction does
not establish every font, DPI, vector format, layout, clipping policy, editor
workflow or original business proposal script. Fixed-canvas exports may still
clip artists placed beyond their canvas; this change does not silently enlarge
a fixed physical canvas when no content crop was requested.
