# Figure view and export

On the Figures page, **Fit** aligns figure content to the top-left and enlarges
it to fit the available canvas viewport. Rulers can stay visible or be toggled off; their
tracks do not shift the fitted figure outside the viewport. The standalone
editor fills the SDK shell's content frame, leaving shell controls outside it.

Fit changes the view only. It does not change figure dimensions or the exported
artifact. Use **Export** to choose PNG, SVG, or PDF, enter a filename, and
confirm the download.

The fitting arithmetic is checked by the real geometry cases in
`src/figrecipe/_django/frontend/tests/canvasPan.test.ts`, including viewport
containment with visible and hidden ruler origins:

```sh
node --experimental-strip-types src/figrecipe/_django/frontend/tests/canvasPan.test.ts
```

For a browser check, open a recipe, click Fit with rulers on and off, and ensure
the image remains inside the canvas. Export PNG and confirm that a nonempty
image downloads. These checks exercise view positioning and the export path;
inspect the exported figure separately for scientific and publication quality.
