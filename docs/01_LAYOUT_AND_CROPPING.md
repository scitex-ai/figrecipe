# Layout and Output: Understanding Matplotlib's Spacing and Cropping

This document explains how matplotlib handles figure layout (element positioning) and output cropping (whitespace trimming). FigRecipe uses sensible defaults for both.

---

## Part 1: Layout Engines

When creating multi-panel figures, matplotlib needs to calculate positions for all elements (titles, axis labels, tick labels, legends) to prevent overlapping.

### The Problem

Without layout management, elements can overlap:

```
┌─────────────────────────────────┐
│     Title A        Title B      │
│  ┌─────────┐    ┌─────────┐    │
│  │         │    │         │    │
│  │  Plot   │    │  Plot   │    │
│  │         │    │         │    │
│  └─────────┘    └─────────┘    │
│     xlabel         xlabel       │
│     Title C  ← OVERLAP! → Title D│
│  ┌─────────┐    ┌─────────┐    │
│  │  Plot   │    │  Plot   │    │
│  └─────────┘    └─────────┘    │
└─────────────────────────────────┘
```

### Solution 1: `tight_layout()` - Post-hoc Adjustment

**How it works:**
1. Render all elements (titles, labels, ticks, legends)
2. Calculate bounding boxes of each element
3. Find overlaps between elements
4. Adjust subplot margins (`left`, `right`, `top`, `bottom`, `wspace`, `hspace`)
5. One-time calculation - done

**Usage:**
```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2)
# ... add all plots, labels, titles ...
plt.tight_layout()  # Must call AFTER adding all elements
fig.savefig('output.png')
```

**Pros:**
- Simple to use
- Fast computation
- Works for most cases

**Cons:**
- Must call manually after adding all elements
- Doesn't adapt to figure resize or interactive changes
- Can fail with complex layouts (colorbars, inset axes)

### Solution 2: `constrained_layout` - Constraint Solver (Recommended)

**How it works:**
1. Treat layout as a constraint satisfaction problem
2. Each element has constraints:
   - "title must be above axes with padding X"
   - "xlabel must be below axes with padding Y"
   - "axes must not overlap"
3. Use Kiwi solver (similar to CSS Flexbox) to find optimal positions
4. Re-solves on every render (resize, zoom, export)

**Usage:**
```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, constrained_layout=True)  # Set at creation
# ... add plots ...
# No need to call anything - auto-adjusts
fig.savefig('output.png')
```

**Pros:**
- Handles complex layouts (colorbars, nested axes, legends outside)
- Adapts automatically to figure resize
- More robust for publication figures
- No manual intervention needed

**Cons:**
- Slightly slower (constraint solving on each render)
- Must be set at figure creation time
- Cannot be combined with manual `subplots_adjust()`

### Visual Comparison

```
tight_layout (post-hoc):          constrained_layout (continuous):
┌─────────────────────┐           ┌─────────────────────┐
│  Render elements    │           │  Define constraints │
│         ↓           │           │         ↓           │
│  Calculate boxes    │           │  Kiwi solver runs   │
│         ↓           │           │         ↓           │
│  Find total extent  │           │  Find optimal pos   │
│         ↓           │           │         ↓           │
│  Adjust margins     │           │  Apply positions    │
│         ↓           │           │         ↓           │
│  Done (static)      │           │  Re-solve on change │
└─────────────────────┘           └─────────────────────┘
```

---

## Part 2: Output Cropping with `bbox_inches`

When saving figures, `bbox_inches` controls how the output image is cropped.

### Default Behavior (No Cropping)

```python
fig.savefig("plot.png")  # Saves entire figsize canvas
```

The output has exact dimensions matching `figsize`, but may include empty whitespace margins.

```
┌─────────────────────────────────┐
│                                 │  ← Empty margin
│    ┌───────────────────────┐   │
│    │     Title             │   │
│    │  ┌─────────────────┐  │   │
│    │  │                 │  │   │
│    │  │     Plot        │  │   │
│    │  │                 │  │   │
│    │  └─────────────────┘  │   │
│    │       xlabel          │   │
│    └───────────────────────┘   │
│                                 │  ← Empty margin
└─────────────────────────────────┘
         ↑ Full figsize canvas
```

### With `bbox_inches='tight'` (Cropped)

```python
fig.savefig("plot.png", bbox_inches='tight')  # Crops to content
```

Matplotlib calculates the bounding box containing all visible artists, then crops to that box.

```
┌───────────────────────┐
│     Title             │
│  ┌─────────────────┐  │
│  │                 │  │
│  │     Plot        │  │
│  │                 │  │
│  └─────────────────┘  │
│       xlabel          │
└───────────────────────┘
   ↑ Cropped to content
```

### How `bbox_inches='tight'` Works

1. **Collect all artists**: Finds every visible element (axes, titles, labels, legends, annotations)
2. **Calculate bounding boxes**: Gets the extent of each artist in figure coordinates
3. **Union all boxes**: Combines into one encompassing bounding box
4. **Add padding**: Applies `pad_inches` (default: 0.1 inches) around the content
5. **Crop output**: Saves only the cropped region

```
Step 1-2: Find each element's box    Step 3: Union all boxes
┌─────────┐                          ┌─────────────────────┐
│ Title   │ ──┐                      │                     │
└─────────┘   │                      │  Combined bounding  │
┌─────────────┴──┐                   │       box           │
│     Axes       │ ──→              │                     │
└────────────────┘                   └─────────────────────┘
┌──────────┐                                   ↓
│  xlabel  │ ──┘                    Step 4: Add pad_inches
└──────────┘                        Step 5: Crop & save
```

### With Padding Control

```python
# Default padding (0.1 inches)
fig.savefig("plot.png", bbox_inches='tight')

# Custom padding
fig.savefig("plot.png", bbox_inches='tight', pad_inches=0.2)

# No padding (exact content bounds)
fig.savefig("plot.png", bbox_inches='tight', pad_inches=0)
```

### Trade-offs

| Aspect | Default (`bbox_inches=None`) | `bbox_inches='tight'` |
|--------|------------------------------|------------------------|
| Output dimensions | Exact `figsize` | Variable (content-dependent) |
| Whitespace | May have excess | Trimmed to content |
| Reproducibility | Predictable size | Size varies with content |
| Use case | Exact dimension requirements | Clean output, no manual cropping |

---

## Part 3: FigRecipe Defaults

### For Non-MM Layouts (Auto-spacing)

```python
import figrecipe as fr

# constrained_layout=True is automatic
fig, axes = fr.subplots(2, 2, figsize=(10, 8))
# No overlap - spacing handled automatically by constraint solver
```

### For MM-Based Layouts (Precise Control)

```python
# MM-based layout uses manual positioning
fig, axes = fr.subplots(
    2, 2,
    axes_width_mm=40,
    axes_height_mm=30,
    space_h_mm=15,  # Explicit vertical spacing
)
# Uses subplots_adjust() for exact mm positioning
# constrained_layout is disabled (conflicts with manual adjustments)
```

### For Saving

```python
# FigRecipe's save() handles format/path automatically
fr.save(fig, "output")  # Saves as PDF by default

# For manual savefig with cropping
fig.savefig("output.png", bbox_inches='tight', dpi=300)
```

---

## Recommendations

| Scenario | Layout | Cropping |
|----------|--------|----------|
| Quick exploratory plots | `constrained_layout=True` (default) | `bbox_inches='tight'` |
| Publication with exact dimensions | MM-based layout | No cropping (use exact figsize) |
| Complex layouts (colorbars, etc.) | `constrained_layout=True` | `bbox_inches='tight'` |
| Figures for web/presentations | Either | `bbox_inches='tight'` |
| Batch processing (consistent sizes) | Either | No cropping |

---

## Common Issues

### Conflict Warning
```
UserWarning: The figure layout has changed to tight
```
**Cause:** Calling `tight_layout()` on a figure created with `constrained_layout=True`
**Fix:** Remove the `tight_layout()` call - constrained_layout handles it automatically

### Inconsistent Output Sizes
**Cause:** Using `bbox_inches='tight'` produces different sizes based on content
**Fix:** For consistent sizes, either:
- Don't use `bbox_inches='tight'`
- Use MM-based layout with explicit dimensions

---

## References

- [Requested raster crops with content outside the canvas](overflow-content-crop.md)
- [Matplotlib: Constrained Layout Guide](https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html)
- [Matplotlib: Tight Layout Guide](https://matplotlib.org/stable/tutorials/intermediate/tight_layout_guide.html)
- [Matplotlib: savefig() Documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)
