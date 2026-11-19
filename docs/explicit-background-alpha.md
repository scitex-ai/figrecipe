# Explicit background alpha

`fr.save(fig, path, facecolor=...)` accepts Matplotlib color specifications,
including `"#ffffff00"` (zero alpha), `"#12345680"` (partial alpha), and RGBA
tuples. Fully opaque colors temporarily force figure and axes patch alpha to
1. Partial or zero color alpha remains intact. The special `"auto"` value
retains its existing opaque-patch behavior while Matplotlib selects the color;
`None` leaves the style in charge.

Existing explicit artist alpha and axes backgrounds still follow Matplotlib's
layering rules. This change does not remove those layers or record save-time
overrides into the recipe. Invalid colors raise Matplotlib's normal
`ValueError`. Patch state is restored after opaque exports and file-write
failures.

The owner is `_api/_save_config.py::_is_opaque_facecolor`.
`tests/integration/test_alpha_facecolor.py` checks actual PNG corner alpha for
fixed-canvas and millimetre content-crop exports, plus opaque/auto compatibility,
recipe validation, state restoration and invalid-color rejection. The selected
PNG controls do not establish every vector backend, opaque-only image format,
layered artist combination, composition or hosted editor workflow.
